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
                
                # Draw on the display image
                cv2.rectangle(display_image, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                
                text_to_show = f"{plate_result['plate_text']}"
                if 'state' in plate_result and plate_result['state']:
                    text_to_show = f"{plate_result['state']}: {text_to_show}"
                    
                cv2.putText(display_image, text_to_show, (int(x1), int(y1)-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                results.append(plate_result)
            
            return results, display_image
            
        except Exception as e:
            print(f"Error in license plate detection: {e}")
            return [], display_image


    async def _recognize_plate_text(self, plate_image: np.ndarray) -> Dict[str, Any]:
        """
        Recognize text on a license plate image using OCR and apply corrections.

        Args:
            plate_image: Cropped license plate image

        Returns:
            Dict with plate text and metadata
        """
        # Preprocess the image for better OCR
        preprocessed = self._preprocess_plate_image(plate_image)

        # Run OCR on the preprocessed image in a separate thread
        loop = asyncio.get_event_loop()

        # Wrap OCR call in a function to run in executor
        def run_ocr(img):
            return self.ocr_reader.readtext(img)
        ocr_result = await loop.run_in_executor(None, run_ocr, preprocessed)

        # Extract and process OCR results
        extracted_text, confidence, state_code = self._process_ocr_results(ocr_result)

        # Clean and validate the plate text
        cleaned_text = self._clean_plate_text(extracted_text)

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
            "raw_text": extracted_text
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
