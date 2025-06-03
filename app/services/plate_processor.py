"""
License plate processor service.
This module provides specialized functionality for processing different types of license plates.
"""

import cv2
import numpy as np
import re
from typing import List, Dict, Any, Optional, Tuple
import asyncio
from app.utils.us_states import (
    STATE_NAMES, COMMON_WORDS, STATE_PATTERNS, 
    SPECIAL_PLATES, get_state_from_text, get_state_pattern
)

class PlateProcessor:
    """
    Processes license plate images with specialized logic for different plate types.
    Handles multi-region analysis, state detection, and format validation.
    """
    
    def __init__(self, ocr_reader=None):
        """
        Initialize the plate processor.
        
        Args:
            ocr_reader: OCR reader instance (e.g., EasyOCR)
        """
        self.ocr_reader = ocr_reader
        
    async def process_plate(self, plate_image, ocr_reader=None):
        """
        Process a license plate image.
        
        Args:
            plate_image: Image of the license plate
            ocr_reader: Optional OCR reader (uses instance reader if None)
            
        Returns:
            Dict with processed plate info
        """
        reader = ocr_reader or self.ocr_reader
        if not reader:
            raise ValueError("OCR reader is required")
            
        # Determine plate type (standard, temporary, etc.)
        plate_type = await self.classify_plate_type(plate_image)
        
        if plate_type == "temporary_tag":
            return await self.process_temporary_tag(plate_image, reader)
        else:
            return await self.process_standard_plate(plate_image, reader)
    
    async def classify_plate_type(self, plate_image) -> str:
        """
        Determine the type of license plate.
        
        Args:
            plate_image: License plate image
            
        Returns:
            Plate type string
        """
        height, width = plate_image.shape[:2]
        aspect_ratio = width / height
        
        # Temporary tags are often paper-based with different aspect ratios
        if aspect_ratio > 2.5 or aspect_ratio < 1.5:
            return "temporary_tag"
        
        # Color analysis can help identify temporary vs permanent plates
        # Temporary tags often have white background
        hsv = cv2.cvtColor(plate_image, cv2.COLOR_BGR2HSV)
        white_pixels = cv2.inRange(hsv, (0, 0, 200), (180, 30, 255))
        white_percentage = cv2.countNonZero(white_pixels) / (height * width)
        
        if white_percentage > 0.7:
            return "temporary_tag"
        
        return "standard_plate"
    
    async def process_standard_plate(self, plate_image, reader) -> Dict[str, Any]:
        """
        Process a standard license plate using multi-region analysis.
        
        Args:
            plate_image: License plate image
            reader: OCR reader
            
        Returns:
            Dict with plate information
        """
        height, width = plate_image.shape[:2]
        
        # Split the plate into regions
        # The top 1/3 typically contains the state name
        state_roi = plate_image[0:int(height*0.3), :]
        
        # The bottom 2/3 typically contains the plate number
        plate_roi = plate_image[int(height*0.3):, :]
        
        # Run OCR on each region using a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        state_ocr_result = await loop.run_in_executor(None, lambda: reader.readtext(state_roi))
        plate_ocr_result = await loop.run_in_executor(None, lambda: reader.readtext(plate_roi))
        
        # Process state region
        state_text = ""
        for bbox, text, conf in state_ocr_result:
            state_text += " " + text
            
        state_text = state_text.strip()
        state_code = get_state_from_text(state_text)
        
        # Process plate region
        plate_text = ""
        plate_confidence = 0.0
        plate_texts = []
        plate_confs = []
        
        for bbox, text, conf in plate_ocr_result:
            plate_texts.append(text)
            plate_confs.append(conf)
        
        if plate_texts:
            # Start with the highest confidence text
            best_idx = plate_confs.index(max(plate_confs))
            plate_text = plate_texts[best_idx]
            plate_confidence = plate_confs[best_idx]
        
        # Clean the plate text
        cleaned_text = self.clean_plate_text(plate_text, state_code)
        
        # Apply state-specific pattern matching if state is known
        final_text, validation_score = self.validate_with_pattern(cleaned_text, state_code)
        
        # Calculate final confidence
        final_confidence = plate_confidence * (0.5 + 0.5 * validation_score)
        
        return {
            "plate_text": final_text,
            "confidence": float(final_confidence),
            "state": state_code,
            "plate_type": "standard",
            "raw_text": plate_text,
            "validation_score": float(validation_score)
        }
    
    async def process_temporary_tag(self, plate_image, reader) -> Dict[str, Any]:
        """
        Process a temporary tag license plate.
        
        Args:
            plate_image: License plate image
            reader: OCR reader
            
        Returns:
            Dict with plate information
        """
        # Enhance the image for better OCR on temporary tags
        enhanced = self.enhance_temporary_tag(plate_image)
        
        # Run OCR on the full enhanced image
        loop = asyncio.get_event_loop()
        ocr_result = await loop.run_in_executor(None, lambda: reader.readtext(enhanced))
        
        # Temporary tags often have multiple text fields
        all_texts = []
        all_confs = []
        
        for bbox, text, conf in ocr_result:
            all_texts.append(text)
            all_confs.append(conf)
        
        # Look for patterns that match temporary tag formats
        temp_tag_text = self.extract_temp_tag_number(all_texts)
        
        # If no specific temp tag pattern found, use the highest confidence text
        if not temp_tag_text and all_texts:
            best_idx = all_confs.index(max(all_confs))
            temp_tag_text = all_texts[best_idx]
            
        # Clean the text
        cleaned_text = self.clean_plate_text(temp_tag_text)
        
        # Determine confidence - temporary tags generally have lower confidence
        avg_confidence = sum(all_confs) / len(all_confs) if all_confs else 0.5
        
        return {
            "plate_text": cleaned_text,
            "confidence": float(avg_confidence * 0.8),  # Reduce confidence for temporary tags
            "state": None,  # Often hard to determine state for temp tags
            "plate_type": "temporary",
            "raw_text": ' '.join(all_texts),
            "validation_score": 0.7  # Default validation score for temp tags
        }
    
    def enhance_temporary_tag(self, plate_image) -> np.ndarray:
        """
        Enhance temporary tag images for better OCR.
        
        Args:
            plate_image: License plate image
            
        Returns:
            Enhanced image
        """
        # Convert to grayscale
        gray = cv2.cvtColor(plate_image, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive threshold to handle varying lighting
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # Remove noise
        kernel = np.ones((1, 1), np.uint8)
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        
        # Invert back
        result = cv2.bitwise_not(opening)
        
        return result
    
    def extract_temp_tag_number(self, texts: List[str]) -> str:
        """
        Extract temporary tag number from OCR results.
        
        Args:
            texts: List of text strings from OCR
            
        Returns:
            Extracted temporary tag number or empty string
        """
        # Common temporary tag patterns
        temp_patterns = [
            r"([A-Z0-9]{6,8})",  # 6-8 alphanumeric characters
            r"TEMP\s*#?\s*([A-Z0-9]{4,})",  # TEMP followed by number
            r"TEMPORARY\s*#?\s*([A-Z0-9]{4,})",  # TEMPORARY followed by number
            r"([A-Z0-9]{2,3}-[A-Z0-9]{2,3}-[A-Z0-9]{2,3})"  # Format with dashes
        ]
        
        # Check each text for temporary tag patterns
        for text in texts:
            text = text.upper().strip()
            
            # Look for temporary tag indicators
            is_temp = False
            for indicator in SPECIAL_PLATES["TEMPORARY"]:
                if indicator in text:
                    is_temp = True
                    break
            
            if is_temp:
                # Try to extract the number part
                for pattern in temp_patterns:
                    match = re.search(pattern, text)
                    if match:
                        return match.group(1)
            
            # Even if not explicitly marked as temporary, check for patterns
            for pattern in temp_patterns:
                match = re.search(pattern, text)
                if match:
                    return match.group(1)
        
        return ""
    
    def clean_plate_text(self, text: str, state_code: str = None) -> str:
        """
        Clean and normalize license plate text.
        
        Args:
            text: Raw text from OCR
            state_code: Two-letter state code if known
            
        Returns:
            Cleaned plate text
        """
        if not text:
            return ""
        
        # Convert to uppercase and remove spaces
        text = text.upper().strip().replace(" ", "")
        
        # Remove common special characters
        text = re.sub(r'[^\w]', '', text)
        
        # Remove state names
        for state_name, code in STATE_NAMES.items():
            text = text.replace(state_name, "")
            
        # Remove state code if different from provided state
        if state_code:
            for code in STATE_NAMES.values():
                if code != state_code:
                    text = text.replace(code, "")
        
        # Remove common words
        for word in COMMON_WORDS:
            text = text.replace(word, "")
        
        # If text is too long (>10 chars), it probably contains extra information
        if len(text) > 10:
            # Try to extract the most likely plate part (usually last 5-8 chars)
            text = text[-8:] if len(text) >= 8 else text
        
        return text
    
    def validate_with_pattern(self, text: str, state_code: str = None) -> Tuple[str, float]:
        """
        Validate plate text against state-specific patterns.
        
        Args:
            text: Cleaned plate text
            state_code: Two-letter state code
            
        Returns:
            Tuple of (validated_text, validation_score)
        """
        if not text:
            return "", 0.0
            
        # If we know the state, check against its pattern
        if state_code and state_code in STATE_PATTERNS:
            pattern = STATE_PATTERNS[state_code][0]
            match = re.search(pattern, text)
            
            if match:
                # Full match against the state pattern
                return match.group(0), 1.0
        
        # If no state pattern match, check against common patterns
        common_patterns = [
            r"[A-Z]{3}[0-9]{3,4}",  # 3 letters followed by 3-4 numbers (common)
            r"[0-9]{3}[A-Z]{3}",     # 3 numbers followed by 3 letters
            r"[A-Z][0-9]{6,7}",      # 1 letter followed by 6-7 numbers
            r"[0-9]{1,3}[A-Z]{3,5}"  # 1-3 numbers followed by 3-5 letters
        ]
        
        for pattern in common_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0), 0.8
        
        # If text is all alphanumeric and reasonable length (4-8 chars)
        if re.match(r'^[A-Z0-9]{4,8}$', text):
            return text, 0.6
            
        # No pattern match, return as is with low confidence
        return text, 0.4