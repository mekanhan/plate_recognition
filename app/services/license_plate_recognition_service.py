"""
License plate recognition service that uses specialized models for US license plates.
"""
# might need to remove this file.

import cv2
import numpy as np
import torch
from ultralytics import YOLO
import easyocr
from typing import List, Dict, Any, Optional, Tuple
import asyncio
import re
import time
import os
from app.utils.us_states import get_state_from_text, get_state_pattern

class LicensePlateRecognitionService:
    """
    Service for detecting and recognizing license plates using specialized models.
    """
    
    def __init__(self):
        """Initialize the license plate recognition service."""
        self.detector_model = None
        self.ocr_reader = None
        self.initialized = False
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        # Character confusion matrix for correction
        self.char_confusion = {
            'I': ['T', '1'],  # I is often confused with T or 1
            'T': ['I'],       # T is often confused with I
            '0': ['O', 'D'],  # 0 is often confused with O or D
            'O': ['0', 'D'],  # O is often confused with 0 or D
            '8': ['B'],       # 8 is often confused with B
            'B': ['8'],       # B is often confused with 8
            '5': ['S'],       # 5 is often confused with S
            'S': ['5'],       # S is often confused with 5
            '1': ['I', 'L'],  # 1 is often confused with I or L
            'Z': ['2'],       # Z is often confused with 2
            '2': ['Z']        # 2 is often confused with Z
        }
        
    """
    Service for detecting and recognizing license plates using specialized models.
    """

    def __init__(self):
        """Initialize the license plate recognition service."""
        self.detector_model = None
        self.ocr_reader = None
        self.initialized = False
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'

        # Character confusion matrix for correction
        self.char_confusion = {
            'I': ['T', '1'],  # I is often confused with T or 1
            'T': ['I'],       # T is often confused with I
            '0': ['O', 'D'],  # 0 is often confused with O or D
            'O': ['0', 'D'],  # O is often confused with 0 or D
            '8': ['B'],       # 8 is often confused with B
            'B': ['8'],       # B is often confused with 8
            '5': ['S'],       # 5 is often confused with S
            'S': ['5'],       # S is often confused with 5
            '1': ['I', 'L'],  # 1 is often confused with I or L
            'Z': ['2'],       # Z is often confused with 2
            '2': ['Z']        # 2 is often confused with Z
        }

        # Invalid words that shouldn't appear in license plates
        self.invalid_words = ["ZANE", "FAKE", "SAMPLE", "TEST", "DEMO"]

    async def initialize(self):
        """Initialize models and resources."""
        self.invalid_words = ["ZANE", "FAKE", "SAMPLE", "TEST", "DEMO"]
        
    async def initialize(self):
        """Initialize models and resources."""
        if self.initialized:
            return
            
        # Initialize detector model
        await self._initialize_detector()
        
        # Initialize OCR reader
        await self._initialize_ocr()
        
        self.initialized = True
        print(f"License plate recognition service initialized (Device: {self.device})")
        
    async def _initialize_detector(self):
        """Initialize the license plate detector model."""
        def load_model():
            # Use your existing model - just pick one of your YOLOv8 models
            # Try these paths in order of preference for license plate detection
            model_paths = [
                "app/models/yolo11m_best.pt",  # Your custom trained model
                "app/models/yolov11m.pt",      # Another potential custom model
                "app/models/yolov8m.pt"        # Fallback to standard YOLOv8
            ]
        
            # Find the first model that exists
            model_path = None
            for path in model_paths:
                if os.path.exists(path):
                    model_path = path
                    break
                
            if not model_path:
                raise FileNotFoundError("No YOLO model found in app/models directory")

            print(f"Loading detector model on {self.device}: {model_path}")

            # Load the model with GPU acceleration
            model = YOLO(model_path)
            model.to(self.device)

            # Set the model to half precision for faster inference if using GPU
            if self.device == 'cuda':
                model.model.half()  # Convert to FP16
                print("Using half precision (FP16) for faster inference")

            return model

        # Run model loading in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        self.detector_model = await loop.run_in_executor(None, load_model)

    async def _initialize_ocr(self):
        """Initialize the OCR reader for license plate text recognition."""
        def load_ocr():
            gpu = self.device == 'cuda'
            print(f"Initializing EasyOCR reader for license plates (GPU: {gpu})")

            # Set CUDA device correctly for EasyOCR
            if gpu:
                os.environ['CUDA_VISIBLE_DEVICES'] = '0'  # Use the first GPU
            return easyocr.Reader(['en'], gpu=gpu, quantize=gpu)

        # Run OCR loading in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        self.ocr_reader = await loop.run_in_executor(None, load_ocr)

    async def detect_and_recognize(self, image: np.ndarray) -> Tuple[List[Dict[str, Any]], np.ndarray]:
        """
        Detect and recognize license plates in an image.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Tuple of (list of detection results, annotated image)
        """
        if not self.initialized:
            await self.initialize()
            
        if self.detector_model is None or self.ocr_reader is None:
            raise RuntimeError("Models not properly initialized")
            
        # Create a copy of the image for visualization
        display_image = image.copy()
        
        # Run the detector
        try:
            # Offload YOLO inference to a separate thread to avoid blocking
            loop = asyncio.get_event_loop()

            # Function to run YOLO detection
            def run_detection(img):
                # Move image tensor to correct device if needed
                results = self.detector_model(img, verbose=False)
                return results[0]

            # Run detection in a thread pool
            detections = await loop.run_in_executor(None, run_detection, image)
            
            results = []
            
            # Process each detection
            boxes_data = detections.boxes.data.cpu().numpy()

            for det in boxes_data:
                x1, y1, x2, y2, conf, cls = det
                
                # Skip low confidence detections
                if conf < 0.3:
                    continue
                    
                # Extract license plate region
                plate_roi = image[int(y1):int(y2), int(x1):int(x2)]
                
                if plate_roi.size == 0:
                    continue
                
                # Process the plate region with OCR
                plate_result = await self._recognize_plate_text(plate_roi)
                
                # Skip if no valid text found
                if not plate_result["plate_text"]:
                    continue
                
                # Add bounding box to results
                plate_result["box"] = [int(x1), int(y1), int(x2), int(y2)]
                plate_result["detection_confidence"] = float(conf)
                plate_result["timestamp"] = time.time()
                plate_result["class_name"] = "license_plate"  # Add class name for tracking
                
                # Get confidence values for display
                ocr_confidence = plate_result.get('confidence', 0) * 100
                detection_confidence = plate_result.get('detection_confidence', 0) * 100
                
                # Determine color based on confidence levels
                avg_confidence = (ocr_confidence + detection_confidence) / 2
                if avg_confidence >= 80:
                    color = (0, 255, 0)  # Green for high confidence
                elif avg_confidence >= 60:
                    color = (0, 255, 255)  # Yellow for medium confidence
                else:
                    color = (0, 0, 255)  # Red for low confidence
                
                # Draw bounding box with confidence-based color
                cv2.rectangle(display_image, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                
                # Create enhanced text with confidence
                plate_text = plate_result['plate_text']
                state_prefix = f"{plate_result['state']}: " if plate_result.get('state') else ""
                confidence_text = f"({ocr_confidence:.0f}%/{detection_confidence:.0f}%)"
                
                # Main text: State + Plate + Confidence
                main_text = f"{state_prefix}{plate_text} {confidence_text}"
                
                # Calculate text positioning
                text_y = int(y1) - 15
                if text_y < 25:  # If too close to top, move below the box
                    text_y = int(y2) + 25
                
                # Draw main text with background for better visibility
                text_size = cv2.getTextSize(main_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                cv2.rectangle(display_image, 
                             (int(x1), text_y - text_size[1] - 5), 
                             (int(x1) + text_size[0] + 10, text_y + 5), 
                             (0, 0, 0), -1)  # Black background
                cv2.putText(display_image, main_text, (int(x1) + 2, text_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                
                # Add additional metadata if space allows (smaller text)
                if plate_result.get('frame_id'):
                    meta_text = f"Frame: {plate_result['frame_id']}"
                    cv2.putText(display_image, meta_text, (int(x1) + 2, text_y + 20),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                
                results.append(plate_result)
            
            return results, display_image
            
        except Exception as e:
            print(f"Error in license plate detection: {e}")
            return [], display_image


    async def _recognize_plate_text(self, plate_image: np.ndarray) -> Dict[str, Any]:
        """
        Recognize text on a license plate image using OCR with enhanced text filtering.

        Args:
            plate_image: Cropped license plate image

        Returns:
            Dict with plate text and metadata
        """
        # Preprocess the image for better OCR
        preprocessed = self._preprocess_plate_image(plate_image)

        # Run OCR on the preprocessed image in a separate thread with bounding boxes
        loop = asyncio.get_event_loop()

        # Wrap OCR call in a function to run in executor
        def run_ocr(img):
            return self.ocr_reader.readtext(img, detail=1)  # detail=1 gives us bounding boxes
        ocr_result = await loop.run_in_executor(None, run_ocr, preprocessed)

        # Process OCR results with enhanced text filtering
        best_plate_text, confidence, state_code, raw_text = self._process_ocr_results_enhanced(ocr_result, plate_image.shape)

        # Clean and validate the plate text
        cleaned_text = self._clean_plate_text(best_plate_text)

        # Apply character corrections based on confusion matrix
        corrected_text = self._apply_character_corrections(cleaned_text, state_code)

        # Validate the final text
        is_valid, validation_confidence = self._validate_plate_text(corrected_text, state_code)

        # Calculate final confidence
        final_confidence = confidence * validation_confidence if is_valid else 0.0

        return {
            "plate_text": corrected_text if is_valid else "",
            "confidence": float(final_confidence),
            "ocr_confidence": float(confidence),
            "state": state_code,
            "raw_text": raw_text
        }

    def _preprocess_plate_image(self, plate_image: np.ndarray) -> np.ndarray:
        """
        Preprocess license plate image to improve OCR accuracy.

        Args:
            plate_image: License plate image

        Returns:
            Preprocessed image
        """
        # Convert to grayscale
        gray = cv2.cvtColor(plate_image, cv2.COLOR_BGR2GRAY)

        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )

        # Create a kernel for morphological operations
        kernel = np.ones((1, 1), np.uint8)

        # Apply morphological operations to remove noise
        processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

        # Return both the grayscale and processed versions
        return plate_image  # Return original for now, can switch to processed if needed

    def _process_ocr_results(self, ocr_result) -> Tuple[str, float, Optional[str]]:
        """
        Process OCR results to extract plate text, confidence, and state.

        Args:
            ocr_result: Results from OCR

        Returns:
            Tuple of (extracted_text, confidence, state_code)
        """
        if not ocr_result:
            return "", 0.0, None

        # Extract all text and confidence values
        all_texts = []
        all_confs = []

        for bbox, text, conf in ocr_result:
            all_texts.append(text.strip())
            all_confs.append(conf)

        # Try to identify state from the texts
        state_code = None
        for text in all_texts:
            potential_state = get_state_from_text(text)
            if potential_state:
                state_code = potential_state
                break

        # Combine all text with spaces
        combined_text = " ".join(all_texts)

        # Calculate average confidence
        avg_confidence = sum(all_confs) / len(all_confs) if all_confs else 0.0

        return combined_text, avg_confidence, state_code

    def _process_ocr_results_enhanced(self, ocr_result, image_shape) -> Tuple[str, float, Optional[str], str]:
        """
        Enhanced OCR processing with size-based text filtering and state name removal.

        Args:
            ocr_result: Results from OCR with bounding boxes
            image_shape: Shape of the license plate image (height, width, channels)

        Returns:
            Tuple of (best_plate_text, confidence, state_code, raw_text)
        """
        if not ocr_result:
            return "", 0.0, None, ""

        height, width = image_shape[:2]
        text_elements = []
        all_raw_texts = []

        # Process each OCR result with bounding box analysis
        for bbox, text, confidence in ocr_result:
            # Extract bounding box coordinates
            x_coords = [point[0] for point in bbox]
            y_coords = [point[1] for point in bbox]
            
            # Calculate text element properties
            text_width = max(x_coords) - min(x_coords)
            text_height = max(y_coords) - min(y_coords)
            text_area = text_width * text_height
            
            # Calculate center position (normalized to 0-1)
            center_x = (min(x_coords) + max(x_coords)) / (2 * width)
            center_y = (min(y_coords) + max(y_coords)) / (2 * height)
            
            # Calculate relative size (normalized to image size)
            relative_area = text_area / (width * height)
            
            text_elements.append({
                "text": text.strip(),
                "confidence": confidence,
                "area": text_area,
                "relative_area": relative_area,
                "width": text_width,
                "height": text_height,
                "center_x": center_x,
                "center_y": center_y,
                "bbox": bbox
            })
            all_raw_texts.append(text.strip())

        # Try to identify state from all text elements
        state_code = None
        for element in text_elements:
            potential_state = get_state_from_text(element["text"])
            if potential_state:
                state_code = potential_state
                break

        # Filter and select the best plate text
        best_plate_text, best_confidence = self._select_best_plate_text_enhanced(text_elements, state_code)
        
        # Combine all raw text for debugging
        raw_text = " ".join(all_raw_texts)
        
        return best_plate_text, best_confidence, state_code, raw_text

    def _select_best_plate_text_enhanced(self, text_elements: List[Dict], state_code: Optional[str]) -> Tuple[str, float]:
        """
        Select the best license plate text from multiple text elements using size and position analysis.
        
        Args:
            text_elements: List of text elements with bounding box info
            state_code: Detected state code for pattern validation
            
        Returns:
            Tuple of (best_text, confidence)
        """
        if not text_elements:
            return "", 0.0
        
        # Import filtering lists
        from app.utils.us_states import STATE_NAMES, COMMON_WORDS, DEALER_FRAME_WORDS, STATE_SLOGANS
        
        # Filter out state names, common words, dealer text, and slogans
        filtered_elements = []
        for element in text_elements:
            text = element["text"].upper()
            
            # Skip if it's a state name
            if text in STATE_NAMES or text in STATE_NAMES.values():
                continue
                
            # Skip if it's a common word
            if any(word in text for word in COMMON_WORDS):
                continue
                
            # Skip if it contains dealer/frame text
            if any(word in text for word in DEALER_FRAME_WORDS):
                continue
                
            # Skip if it's a state slogan
            if any(slogan in text for slogan in STATE_SLOGANS):
                continue
                
            # Skip if it's likely a partial dealer name (contains "GROUP", "PURDY", etc.)
            dealer_keywords = ["GROUP", "PURDY", "STATION", "BAYAN", "COLLECE", "COLLEGE"]
            if any(keyword in text for keyword in dealer_keywords):
                continue
                
            # Skip very small text (likely decorative)
            if element["relative_area"] < 0.05:  # Less than 5% of image area
                continue
                
            # Skip very low confidence
            if element["confidence"] < 0.3:
                continue
                
            filtered_elements.append(element)
        
        if not filtered_elements:
            # Fallback to largest text element if filtering removes everything
            largest_element = max(text_elements, key=lambda x: x["area"])
            return largest_element["text"], largest_element["confidence"]
        
        # Score each remaining text element
        scored_elements = []
        for element in filtered_elements:
            score = self._calculate_text_element_score(element, state_code)
            scored_elements.append((element, score))
        
        # Sort by score (highest first)
        scored_elements.sort(key=lambda x: x[1], reverse=True)
        
        # Return the best scoring element
        best_element, best_score = scored_elements[0]
        return best_element["text"], best_element["confidence"]

    def _calculate_text_element_score(self, element: Dict, state_code: Optional[str]) -> float:
        """
        Calculate a score for a text element to determine if it's likely the license plate number.
        
        Args:
            element: Text element with properties
            state_code: Detected state code
            
        Returns:
            Score (higher is better)
        """
        text = element["text"].upper()
        score = 0.0
        
        # Base score from OCR confidence
        score += element["confidence"] * 40
        
        # Size bonus - larger text is more likely to be the plate number
        size_bonus = min(element["relative_area"] * 100, 30)  # Cap at 30 points
        score += size_bonus
        
        # Center position bonus - plates are usually centered
        center_x_bonus = 10 * (1 - abs(element["center_x"] - 0.5) * 2)  # Max 10 points for center
        center_y_bonus = 5 * (1 - abs(element["center_y"] - 0.5) * 2)   # Max 5 points for center
        score += center_x_bonus + center_y_bonus
        
        # Length bonus - typical plate lengths
        text_length = len(re.sub(r'[^A-Z0-9]', '', text))  # Count only alphanumeric
        if 5 <= text_length <= 8:
            score += 15
        elif 4 <= text_length <= 9:
            score += 10
        else:
            score -= 5
        
        # Pattern matching bonus
        if state_code:
            from app.utils.us_states import get_state_pattern
            pattern = get_state_pattern(state_code)
            if pattern and re.match(pattern, text):
                score += 20
        
        # Character composition bonus
        letter_count = sum(1 for c in text if c.isalpha())
        digit_count = sum(1 for c in text if c.isdigit())
        
        # Most plates have both letters and numbers
        if letter_count > 0 and digit_count > 0:
            score += 10
        elif letter_count > 0 or digit_count > 0:
            score += 5
        
        # Penalty for too many special characters
        special_count = len(text) - letter_count - digit_count
        if special_count > 2:
            score -= special_count * 3
        
        return score

    def _clean_plate_text(self, text: str) -> str:
        """
        Clean and normalize license plate text.

        Args:
            text: Raw text from OCR

        Returns:
            Cleaned text
        """
        if not text:
            return ""
                
        # Convert to uppercase and remove spaces
        text = text.upper().strip()

        # Remove common words and text that shouldn't be on a license plate
        for word in self.invalid_words:
            text = text.replace(word, "")

        # Remove non-alphanumeric characters except common separators
        text = re.sub(r'[^A-Z0-9\-•*]', '', text)
        # Remove spaces
        text = text.replace(" ", "")

        # If text is too long, it might contain extra information
        if len(text) > 8:
            # Try to extract most likely plate part (usually last 7-8 chars)
            text = text[-8:] if len(text) >= 8 else text

        return text

    def _apply_character_corrections(self, text: str, state_code: Optional[str] = None) -> str:
        """
        Apply corrections for commonly confused characters.

        Args:
            text: Cleaned plate text
            state_code: Two-letter state code if known

        Returns:
            Corrected text
        """
        if not text:
            return ""

        # Apply state-specific corrections if state is known
        if state_code:
            # Texas-specific corrections
            if state_code == "TX" and len(text) == 7:
                # Texas plates often have 3 letters followed by 4 digits
                if text[0:3].isalpha() and text[3:].isdigit():
                    # Common Texas format, check for specific character confusions
                    if text[2] == 'I':
                        # Third character is often T, not I in Texas plates
                        text = text[0:2] + 'T' + text[3:]

        # Apply general character corrections based on confusion matrix
        corrected = text
        for i, char in enumerate(text):
            if char in self.char_confusion:
                # Try each possible correction
                for potential in self.char_confusion[char]:
                    candidate = text[:i] + potential + text[i+1:]
                    # Check if the correction produces a more valid plate
                    if self._is_valid_pattern(candidate, state_code):
                        corrected = candidate
                        break

        return corrected

    def _is_valid_pattern(self, text: str, state_code: Optional[str] = None) -> bool:
        """
        Check if text matches valid license plate patterns.

        Args:
            text: Plate text to validate
            state_code: Two-letter state code if known

        Returns:
            True if valid pattern, False otherwise
        """
        # If state is known, check against state-specific pattern
        if state_code:
            pattern = get_state_pattern(state_code)
            if pattern and re.match(pattern, text):
                return True

        # Common license plate patterns
        common_patterns = [
            r"[A-Z]{3}[0-9]{3,4}",  # 3 letters + 3-4 digits
            r"[A-Z]{2}[0-9]{4,5}",  # 2 letters + 4-5 digits
            r"[0-9]{3}[A-Z]{3}",    # 3 digits + 3 letters
            r"[A-Z][0-9]{5,6}",     # 1 letter + 5-6 digits
            r"[0-9]{1,3}[A-Z]{3,5}" # 1-3 digits + 3-5 letters
        ]

        for pattern in common_patterns:
            if re.match(pattern, text):
                return True

        # General alphanumeric check for 5-8 characters
        if re.match(r'^[A-Z0-9]{5,8}$', text):
            return True

        return False

    def _validate_plate_text(self, text: str, state_code: Optional[str] = None) -> Tuple[bool, float]:
        """
        Validate if plate text is likely to be a real license plate.

        Args:
            text: Plate text to validate
            state_code: Two-letter state code if known

        Returns:
            Tuple of (is_valid, confidence)
        """
        if not text or len(text) < 4:
            return False, 0.0

        # Check for invalid words
        for word in self.invalid_words:
            if word in text:
                return False, 0.0

        # Validate pattern
        if self._is_valid_pattern(text, state_code):
            # Calculate confidence based on pattern match and length
            confidence = 0.8  # Base confidence for valid pattern
            
            # Adjust for optimal length (most plates are 6-7 characters)
            if 6 <= len(text) <= 7:
                confidence += 0.1
                
            # Boost confidence for state-specific matches
            if state_code and get_state_pattern(state_code) and re.match(get_state_pattern(state_code), text):
                confidence += 0.1
                
            return True, min(confidence, 1.0)  # Cap at 1.0
            
        return False, 0.3  # Low confidence for non-matching patterns




    async def shutdown(self):
        """
        Shutdown the license plate recognition service and release resources.
        """
        if not self.initialized:
            return
            
        # Release YOLO model resources
        if self.detector_model is not None:
            # Clear CUDA memory if using GPU
            if self.device == 'cuda':
                try:
                    import torch
                    torch.cuda.empty_cache()
                except Exception as e:
                    print(f"Error clearing CUDA cache: {e}")
            
            # Set model to None to help garbage collection
            self.detector_model = None
        
        # Clear OCR reader
        self.ocr_reader = None
        
        # Mark as uninitialized
        self.initialized = False
        
        print("License plate recognition service shutdown")
