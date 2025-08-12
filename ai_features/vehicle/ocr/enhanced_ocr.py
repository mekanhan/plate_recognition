"""
Enhanced OCR Processor for License Plates
Advanced text recognition with preprocessing and validation
"""
import cv2
import numpy as np
import easyocr
import logging
from typing import Tuple, List, Optional, Dict
import time
from datetime import datetime

from .plate_validator import PlateValidator, PlateRegion, ValidationResult


class ImagePreprocessor:
    """Preprocess license plate images for better OCR results"""
    
    def __init__(self):
        self.logger = logging.getLogger("ImagePreprocessor")
    
    def process(self, plate_image: np.ndarray, debug: bool = False) -> List[np.ndarray]:
        """
        Apply multiple preprocessing techniques and return candidates
        
        Args:
            plate_image: Input license plate image
            debug: If True, return intermediate processing steps
            
        Returns:
            List of preprocessed image candidates
        """
        if plate_image is None or plate_image.size == 0:
            return []
        
        candidates = []
        
        try:
            # Original image
            candidates.append(plate_image.copy())
            
            # Resize if too small
            resized = self._resize_if_needed(plate_image)
            if not np.array_equal(resized, plate_image):
                candidates.append(resized)
            
            # Grayscale conversion
            if len(plate_image.shape) == 3:
                gray = cv2.cvtColor(plate_image, cv2.COLOR_BGR2GRAY)
            else:
                gray = plate_image.copy()
            
            # CLAHE enhancement
            clahe_enhanced = self._apply_clahe(gray)
            candidates.append(clahe_enhanced)
            
            # Gaussian blur + sharpen
            denoised = self._denoise_and_sharpen(gray)
            candidates.append(denoised)
            
            # Threshold variations
            thresh_candidates = self._apply_thresholding_variations(gray)
            candidates.extend(thresh_candidates)
            
            # Morphological operations
            morph_enhanced = self._apply_morphological_ops(gray)
            if morph_enhanced is not None:
                candidates.append(morph_enhanced)
            
            # Perspective correction (basic)
            perspective_corrected = self._correct_perspective(gray)
            if perspective_corrected is not None:
                candidates.append(perspective_corrected)
                
            # Remove duplicates and invalid candidates
            valid_candidates = []
            for candidate in candidates:
                if candidate is not None and candidate.size > 0:
                    # Convert to 3-channel if needed for consistency
                    if len(candidate.shape) == 2:
                        candidate = cv2.cvtColor(candidate, cv2.COLOR_GRAY2BGR)
                    valid_candidates.append(candidate)
            
            return valid_candidates[:6]  # Limit to top 6 candidates
            
        except Exception as e:
            self.logger.error(f"Preprocessing error: {e}")
            return [plate_image] if plate_image is not None else []
    
    def _resize_if_needed(self, image: np.ndarray, min_height: int = 40) -> np.ndarray:
        """Resize image if too small for good OCR"""
        height, width = image.shape[:2]
        
        if height < min_height:
            scale = min_height / height
            new_width = int(width * scale)
            new_height = int(height * scale)
            return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        return image
    
    def _apply_clahe(self, gray_image: np.ndarray) -> np.ndarray:
        """Apply Contrast Limited Adaptive Histogram Equalization"""
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        return clahe.apply(gray_image)
    
    def _denoise_and_sharpen(self, gray_image: np.ndarray) -> np.ndarray:
        """Apply denoising and sharpening"""
        # Gaussian blur for denoising
        blurred = cv2.GaussianBlur(gray_image, (3, 3), 0)
        
        # Unsharp mask for sharpening
        sharpening_kernel = np.array([[-1, -1, -1],
                                     [-1,  9, -1],
                                     [-1, -1, -1]])
        sharpened = cv2.filter2D(blurred, -1, sharpening_kernel)
        
        return sharpened
    
    def _apply_thresholding_variations(self, gray_image: np.ndarray) -> List[np.ndarray]:
        """Apply different thresholding techniques"""
        variations = []
        
        # Otsu's thresholding
        _, otsu_thresh = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        variations.append(otsu_thresh)
        
        # Adaptive thresholding
        adaptive_thresh = cv2.adaptiveThreshold(
            gray_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        variations.append(adaptive_thresh)
        
        # Fixed threshold variations
        for thresh_val in [120, 140, 160]:
            _, fixed_thresh = cv2.threshold(gray_image, thresh_val, 255, cv2.THRESH_BINARY)
            variations.append(fixed_thresh)
        
        return variations
    
    def _apply_morphological_ops(self, gray_image: np.ndarray) -> Optional[np.ndarray]:
        """Apply morphological operations to clean up the image"""
        try:
            # Small kernel for text cleanup
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            
            # Opening to remove small noise
            opened = cv2.morphologyEx(gray_image, cv2.MORPH_OPEN, kernel)
            
            # Closing to fill small gaps in characters
            closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)
            
            return closed
        except:
            return None
    
    def _correct_perspective(self, gray_image: np.ndarray) -> Optional[np.ndarray]:
        """Basic perspective correction for skewed plates"""
        try:
            # Find edges
            edges = cv2.Canny(gray_image, 50, 150, apertureSize=3)
            
            # Find lines using Hough transform
            lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=50)
            
            if lines is not None and len(lines) > 2:
                # Simple rotation correction based on dominant line angle
                angles = []
                for line in lines[:5]:  # Use top 5 lines
                    rho, theta = line[0]
                    angle = theta * 180 / np.pi
                    if angle > 90:
                        angle -= 180
                    angles.append(angle)
                
                # Get median angle
                median_angle = np.median(angles)
                
                # Only correct if angle is significant but not too extreme
                if abs(median_angle) > 2 and abs(median_angle) < 45:
                    height, width = gray_image.shape
                    center = (width // 2, height // 2)
                    
                    # Rotation matrix
                    rotation_matrix = cv2.getRotationMatrix2D(center, -median_angle, 1.0)
                    
                    # Apply rotation
                    corrected = cv2.warpAffine(gray_image, rotation_matrix, (width, height))
                    return corrected
            
            return None
        except:
            return None


class EnhancedOCRProcessor:
    """Enhanced OCR processor with validation and multiple technique support"""
    
    def __init__(self, languages: List[str] = None, gpu_enabled: bool = True):
        self.logger = logging.getLogger("EnhancedOCR")
        
        # Initialize OCR reader
        languages = languages or ['en']
        self.reader = easyocr.Reader(languages, gpu=gpu_enabled)
        
        # Initialize components
        self.preprocessor = ImagePreprocessor()
        self.validator = PlateValidator()
        
        # Performance tracking
        self.total_ocr_calls = 0
        self.total_ocr_time = 0.0
        self.success_rate = 0.0
    
    def process_plate(self, plate_image: np.ndarray, camera_id: Optional[str] = None,
                     region: PlateRegion = PlateRegion.US) -> Dict:
        """
        Process license plate image with enhanced OCR and validation
        
        Args:
            plate_image: License plate image array
            camera_id: Camera identifier for logging
            region: Target region for validation
            
        Returns:
            Dict containing OCR results, validation, and metadata
        """
        start_time = time.time()
        self.total_ocr_calls += 1
        
        if plate_image is None or plate_image.size == 0:
            return self._create_empty_result("Empty image")
        
        try:
            # Preprocess image into multiple candidates
            processed_candidates = self.preprocessor.process(plate_image)
            
            if not processed_candidates:
                return self._create_empty_result("Preprocessing failed")
            
            # Try OCR on each candidate
            best_result = None
            best_score = 0.0
            all_results = []
            
            for i, candidate in enumerate(processed_candidates):
                try:
                    # Perform OCR
                    ocr_results = self.reader.readtext(candidate)
                    
                    if not ocr_results:
                        continue
                    
                    # Extract and combine text
                    raw_text = self._extract_text_from_results(ocr_results)
                    ocr_confidence = self._calculate_ocr_confidence(ocr_results)
                    
                    # Validate the text
                    validation = self.validator.validate_plate(raw_text, region)
                    
                    # Calculate overall score
                    overall_score = self._calculate_overall_score(
                        ocr_confidence, validation, len(raw_text)
                    )
                    
                    result = {
                        'raw_text': raw_text,
                        'ocr_confidence': ocr_confidence,
                        'validation': validation,
                        'overall_score': overall_score,
                        'candidate_index': i,
                        'processing_method': f"candidate_{i}"
                    }
                    
                    all_results.append(result)
                    
                    # Track best result
                    if overall_score > best_score:
                        best_score = overall_score
                        best_result = result
                        
                except Exception as e:
                    self.logger.debug(f"OCR failed for candidate {i}: {e}")
                    continue
            
            # Finalize result
            if best_result and best_score > 0.1:  # Minimum acceptable score
                final_result = self._create_success_result(
                    best_result, all_results, camera_id, region
                )
            else:
                final_result = self._create_empty_result("No valid OCR results found")
                final_result['all_attempts'] = len(all_results)
            
            # Update performance tracking
            processing_time = time.time() - start_time
            self.total_ocr_time += processing_time
            final_result['processing_time_ms'] = processing_time * 1000
            
            if final_result['is_valid']:
                self.success_rate = (self.success_rate * (self.total_ocr_calls - 1) + 1) / self.total_ocr_calls
            else:
                self.success_rate = (self.success_rate * (self.total_ocr_calls - 1)) / self.total_ocr_calls
            
            return final_result
            
        except Exception as e:
            self.logger.error(f"OCR processing error: {e}")
            return self._create_empty_result(f"Processing error: {str(e)}")
    
    def _extract_text_from_results(self, ocr_results: List) -> str:
        """Extract and combine text from OCR results, prioritizing larger text (license plate numbers)"""
        if not ocr_results:
            return ""
        
        # Calculate text area/size for each result to prioritize larger text
        text_candidates = []
        
        for result in ocr_results:
            bbox, text, confidence = result
            
            if confidence > 0.1 and text.strip():
                # Calculate bounding box area (larger text typically has larger bounding boxes)
                text_area = self._calculate_text_area(bbox)
                text_height = self._calculate_text_height(bbox)
                
                # Clean text
                clean_text = ''.join(c for c in text.upper() if c.isalnum())
                
                if clean_text and len(clean_text) >= 3:  # Minimum length for valid plates
                    # Check if this looks like a state name or noise
                    is_likely_plate_number = self._is_likely_plate_number(clean_text)
                    
                    text_candidates.append({
                        'text': clean_text,
                        'confidence': confidence,
                        'area': text_area,
                        'height': text_height,
                        'bbox': bbox,
                        'is_likely_plate': is_likely_plate_number,
                        'priority_score': self._calculate_text_priority_score(
                            clean_text, confidence, text_area, text_height, is_likely_plate_number
                        )
                    })
        
        if not text_candidates:
            return ""
        
        # Sort by priority score (highest first) - this prioritizes larger, more likely plate text
        text_candidates.sort(key=lambda x: x['priority_score'], reverse=True)
        
        # Take the highest priority text that is NOT a state name
        best_candidate = None
        for candidate in text_candidates:
            # Skip if it's a known state name
            if self._is_definite_state_name(candidate['text']):
                self.logger.debug(f"Skipping state name candidate: {candidate['text']}")
                continue
            best_candidate = candidate
            break
        
        # If all candidates were state names, reluctantly take the first one
        if not best_candidate and text_candidates:
            best_candidate = text_candidates[0]
            self.logger.warning(f"All candidates were state names, using: {best_candidate['text']}")
        
        # Log analysis for debugging
        self.logger.debug(f"OCR text analysis: Found {len(text_candidates)} candidates")
        for i, candidate in enumerate(text_candidates[:3]):
            self.logger.debug(
                f"  {i+1}. '{candidate['text']}' - Priority: {candidate['priority_score']:.2f} "
                f"(area: {candidate['area']:.0f}, height: {candidate['height']:.1f}, "
                f"confidence: {candidate['confidence']:.2f}, is_plate: {candidate['is_likely_plate']})"
            )
        
        return best_candidate['text']
    
    def _calculate_text_area(self, bbox) -> float:
        """Calculate the area of the text bounding box"""
        try:
            if isinstance(bbox, list) and len(bbox) == 4:
                # Format: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                points = bbox
            else:
                # Convert other formats to points
                points = bbox
            
            # Calculate width and height from bounding box
            x_coords = [point[0] for point in points]
            y_coords = [point[1] for point in points]
            
            width = max(x_coords) - min(x_coords)
            height = max(y_coords) - min(y_coords)
            
            return width * height
        except:
            return 0.0
    
    def _calculate_text_height(self, bbox) -> float:
        """Calculate the height of the text (license plate numbers are typically taller)"""
        try:
            if isinstance(bbox, list) and len(bbox) == 4:
                points = bbox
            else:
                points = bbox
            
            y_coords = [point[1] for point in points]
            return max(y_coords) - min(y_coords)
        except:
            return 0.0
    
    def _is_likely_plate_number(self, text: str) -> bool:
        """Determine if text looks like a license plate number vs state name/noise"""
        # Common state names and noise words (should NOT be plate numbers)
        state_names = {
            'TEXAS', 'CALIFORNIA', 'FLORIDA', 'NEWYORK', 'ILLINOIS', 'OHIO', 
            'GEORGIA', 'MICHIGAN', 'PENNSYLVANIA', 'VIRGINIA', 'WASHINGTON',
            'ARIZONA', 'MASSACHUSETTS', 'TENNESSEE', 'INDIANA', 'MISSOURI',
            'MARYLAND', 'WISCONSIN', 'MINNESOTA', 'COLORADO', 'ALABAMA',
            'SOUTHCAROLINA', 'LOUISIANA', 'KENTUCKY', 'OREGON', 'OKLAHOMA',
            'CONNECTICUT', 'IOWA', 'ARKANSAS', 'UTAH', 'NEVADA', 'NEWMEXICO',
            'WESTVIRGINIA', 'NEBRASKA', 'IDAHO', 'HAWAII', 'NEWHAMPSHIRE',
            'MAINE', 'MONTANA', 'RHODEISLAND', 'DELAWARE', 'SOUTHDAKOTA',
            'NORTHDAKOTA', 'ALASKA', 'VERMONT', 'WYOMING', 'STATE', 'USA',
            'AMERICA', 'COUNTY', 'CITY', 'DEPT', 'POLICE', 'FIRE', 'EXEMPT',
            'DEALER', 'TEMPORARY', 'VETERAN', 'DISABLED',
            # Common misreads of state names
            'TEAXS', 'TEXSA', 'TXEAS', 'TESAS', 'TEBAS', 'TEKXAS', 'TEYAS',
            'CAIFORNIA', 'CALIFRONIA', 'CALFORNIA', 'FLORDIA', 'FLORDA'
        }
        
        # Remove spaces and check if it's a known state/noise word
        clean_text = text.replace(' ', '')
        if clean_text in state_names:
            return False
        
        # License plate characteristics (more likely to be actual plate numbers)
        
        # 1. Good length (most plates are 4-8 characters)
        if len(clean_text) < 4 or len(clean_text) > 8:
            return False
        
        # 2. Contains both letters and numbers (most common plate format)
        has_letters = any(c.isalpha() for c in clean_text)
        has_numbers = any(c.isdigit() for c in clean_text)
        
        if has_letters and has_numbers:
            return True
        
        # 3. All numbers (some specialty plates)
        if clean_text.isdigit() and len(clean_text) >= 4:
            return True
        
        # 4. All letters might be specialty plates, but less common
        if clean_text.isalpha() and len(clean_text) >= 5:
            return True
        
        return False
    
    def _calculate_text_priority_score(self, text: str, confidence: float, 
                                     area: float, height: float, is_likely_plate: bool) -> float:
        """Calculate priority score for text - higher score = more likely to be the actual plate number"""
        score = 0.0
        
        # Base confidence score
        score += confidence * 30
        
        # Size bonus - larger text is more likely to be the plate number
        # Normalize area and height (typical license plate text areas)
        normalized_area = min(area / 5000, 2.0)  # Cap bonus at 2x
        normalized_height = min(height / 40, 2.0)  # Cap bonus at 2x
        
        score += normalized_area * 25  # Area contributes up to 50 points
        score += normalized_height * 20  # Height contributes up to 40 points
        
        # Plate number pattern bonus
        if is_likely_plate:
            score += 40  # Big bonus for looking like actual plate number
        else:
            score -= 30  # Penalty for state names/noise
        
        # Length bonus (ideal license plate length)
        length = len(text)
        if 5 <= length <= 7:
            score += 15  # Ideal length
        elif 4 <= length <= 8:
            score += 10  # Good length
        else:
            score -= 10  # Poor length
        
        # Mixed alphanumeric bonus (most common plate format)
        has_letters = any(c.isalpha() for c in text)
        has_numbers = any(c.isdigit() for c in text)
        if has_letters and has_numbers:
            score += 15
        
        return score
    
    def _is_definite_state_name(self, text: str) -> bool:
        """Check if text is definitely a state name (stricter check)"""
        definite_state_names = {
            'TEXAS', 'CALIFORNIA', 'FLORIDA', 'NEWYORK', 'ILLINOIS', 'OHIO',
            'GEORGIA', 'MICHIGAN', 'PENNSYLVANIA', 'VIRGINIA', 'WASHINGTON',
            'ARIZONA', 'MASSACHUSETTS', 'TENNESSEE', 'INDIANA', 'MISSOURI',
            # Common misreads that are still state names
            'TEAXS', 'TEXSA', 'TXEAS', 'TESAS', 'TEYAS',
            # Other definite non-plate words
            'STATE', 'COUNTY', 'DEALER', 'EXEMPT', 'PLATE', 'LICENSE'
        }
        clean_text = text.replace(' ', '').upper().strip()
        return clean_text in definite_state_names
    
    def _calculate_ocr_confidence(self, ocr_results: List) -> float:
        """Calculate weighted average confidence from OCR results"""
        if not ocr_results:
            return 0.0
        
        total_confidence = 0.0
        total_weight = 0.0
        
        for result in ocr_results:
            bbox, text, confidence = result
            
            # Weight by text length (longer text is more reliable)
            weight = len(text.strip())
            
            total_confidence += confidence * weight
            total_weight += weight
        
        return total_confidence / total_weight if total_weight > 0 else 0.0
    
    def _calculate_overall_score(self, ocr_confidence: float, validation: ValidationResult, 
                               text_length: int) -> float:
        """Calculate overall quality score for OCR result with enhanced plate number prioritization"""
        if not validation.is_valid:
            return 0.0
        
        # Base score from OCR confidence
        score = ocr_confidence * 0.6
        
        # Validation confidence adjustment
        score *= validation.confidence_adjustment
        
        # Enhanced length scoring for license plates
        if 5 <= text_length <= 7:
            score *= 1.2  # Ideal license plate length
        elif text_length == 6:
            score *= 1.3  # Most common length
        elif 4 <= text_length <= 8:
            score *= 1.0  # Acceptable length
        elif text_length == 4:
            score *= 0.9  # Short but possible
        else:
            score *= 0.7  # Too long/short for typical plates
        
        # Check if this looks like a state name and penalize heavily
        plate_text = validation.formatted_text
        if self._is_state_name_or_noise(plate_text):
            score *= 0.1  # Heavy penalty for state names
            self.logger.debug(f"Applied state name penalty to '{plate_text}', score: {score:.3f}")
        
        # Bonus for mixed alphanumeric (most common plate format)
        has_letters = any(c.isalpha() for c in plate_text)
        has_numbers = any(c.isdigit() for c in plate_text)
        if has_letters and has_numbers:
            score *= 1.2  # Bonus for mixed format
        
        # Penalty for corrections
        if validation.suggested_corrections:
            score *= 0.8  # Reduced penalty since corrections might be valid
        
        # Minor penalty for validation issues
        if validation.validation_issues:
            score *= 0.95
        
        return min(1.0, score)  # Cap at 1.0
    
    def _is_state_name_or_noise(self, text: str) -> bool:
        """Check if text is likely a state name or noise rather than a plate number"""
        # Common state names and noise words
        noise_words = {
            'TEXAS', 'CALIFORNIA', 'FLORIDA', 'NEWYORK', 'ILLINOIS', 'OHIO',
            'GEORGIA', 'MICHIGAN', 'PENNSYLVANIA', 'VIRGINIA', 'WASHINGTON',
            'ARIZONA', 'MASSACHUSETTS', 'TENNESSEE', 'INDIANA', 'MISSOURI',
            'MARYLAND', 'WISCONSIN', 'MINNESOTA', 'COLORADO', 'ALABAMA',
            'SOUTHCAROLINA', 'LOUISIANA', 'KENTUCKY', 'OREGON', 'OKLAHOMA',
            'CONNECTICUT', 'IOWA', 'ARKANSAS', 'UTAH', 'NEVADA', 'NEWMEXICO',
            'WESTVIRGINIA', 'NEBRASKA', 'IDAHO', 'HAWAII', 'NEWHAMPSHIRE',
            'MAINE', 'MONTANA', 'RHODEISLAND', 'DELAWARE', 'SOUTHDAKOTA',
            'NORTHDAKOTA', 'ALASKA', 'VERMONT', 'WYOMING',
            'STATE', 'USA', 'AMERICA', 'COUNTY', 'CITY', 'DEPT', 'POLICE',
            'FIRE', 'EXEMPT', 'DEALER', 'TEMPORARY', 'VETERAN', 'DISABLED',
            'GOVT', 'GOV', 'OFFICIAL', 'MUNICIPAL', 'PUBLIC'
        }
        
        clean_text = text.replace(' ', '').upper()
        return clean_text in noise_words
    
    def _create_success_result(self, best_result: Dict, all_results: List, 
                              camera_id: Optional[str], region: PlateRegion) -> Dict:
        """Create successful OCR result dictionary"""
        validation = best_result['validation']
        
        return {
            'plate_text': validation.formatted_text,
            'raw_text': best_result['raw_text'],
            'ocr_confidence': best_result['ocr_confidence'],
            'validation_confidence': validation.confidence_adjustment,
            'overall_score': best_result['overall_score'],
            'is_valid': validation.is_valid,
            'detected_region': validation.detected_region.value if validation.detected_region else region.value,
            'validation_issues': validation.validation_issues,
            'corrections_applied': validation.suggested_corrections,
            'processing_method': best_result['processing_method'],
            'timestamp': datetime.now(),
            'camera_id': camera_id,
            'total_candidates_tried': len(all_results),
            'metadata': {
                'alternative_readings': [r['raw_text'] for r in all_results if r != best_result][:3]
            }
        }
    
    def _create_empty_result(self, reason: str) -> Dict:
        """Create empty/failed OCR result"""
        return {
            'plate_text': '',
            'raw_text': '',
            'ocr_confidence': 0.0,
            'validation_confidence': 0.0,
            'overall_score': 0.0,
            'is_valid': False,
            'detected_region': PlateRegion.US.value,
            'validation_issues': [reason],
            'corrections_applied': [],
            'processing_method': 'failed',
            'timestamp': datetime.now(),
            'camera_id': None,
            'total_candidates_tried': 0,
            'metadata': {}
        }
    
    def get_performance_stats(self) -> Dict:
        """Get OCR performance statistics"""
        avg_time = self.total_ocr_time / self.total_ocr_calls if self.total_ocr_calls > 0 else 0
        
        return {
            'total_ocr_calls': self.total_ocr_calls,
            'success_rate': round(self.success_rate * 100, 2),
            'average_processing_time_ms': round(avg_time * 1000, 2),
            'total_processing_time_seconds': round(self.total_ocr_time, 2)
        }
    
    def reset_stats(self):
        """Reset performance statistics"""
        self.total_ocr_calls = 0
        self.total_ocr_time = 0.0
        self.success_rate = 0.0