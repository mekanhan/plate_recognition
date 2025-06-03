import re
from typing import Dict, List, Optional, Tuple

class LicensePlateProcessor:
    def __init__(self):
        # State-specific regex patterns for license plate formats
        # This dictionary can be expanded with more state formats
        self.state_patterns: Dict[str, List[str]] = {
            # Format: 3 letters + 4 numbers (may have state silhouette between)
            'TX': [r'([A-Z]{3})[^A-Z0-9]*([0-9]{4})'],
            
            # California: 1 number + 3 letters + 3 numbers
            'CA': [r'([0-9]{1})[^A-Z0-9]*([A-Z]{3})[^A-Z0-9]*([0-9]{3})'],
            
            # New York: 3 letters + 4 numbers, or custom formats
            'NY': [r'([A-Z]{3})[^A-Z0-9]*([0-9]{4})', r'([A-Z]{3})[^A-Z0-9]*([0-9]{3}[A-Z]{1})'],
            
            # Florida: 3 letters + 3 numbers, or 3 letters + 2 numbers + 1 letter
            'FL': [r'([A-Z]{3})[^A-Z0-9]*([0-9]{3})', r'([A-Z]{3})[^A-Z0-9]*([0-9]{2})([A-Z]{1})'],
            
            # Pennsylvania: 3 letters + 4 numbers
            'PA': [r'([A-Z]{3})[^A-Z0-9]*([0-9]{4})'],
            
            # Illinois: 2 letters + 5 numbers or personalized
            'IL': [r'([A-Z]{2})[^A-Z0-9]*([0-9]{5})', r'([A-Z]{1,7})'],
            
            # Ohio: 3 letters + 4 numbers or 2 letters + 4 numbers
            'OH': [r'([A-Z]{3})[^A-Z0-9]*([0-9]{4})', r'([A-Z]{2})[^A-Z0-9]*([0-9]{4})'],
            
            # Michigan: 3 letters + 4 numbers or personalized
            'MI': [r'([A-Z]{3})[^A-Z0-9]*([0-9]{4})', r'([A-Z]{1,7})'],
            
            # Georgia: 3 letters + 4 numbers or various personalized formats
            'GA': [r'([A-Z]{3})[^A-Z0-9]*([0-9]{4})'],
            
            # North Carolina: 3 letters + 4 numbers or personalized
            'NC': [r'([A-Z]{3})[^A-Z0-9]*([0-9]{4})'],
            
            # New Jersey: 1 letter + 2 numbers + 3 letters or D series
            'NJ': [r'([A-Z]{1})[^A-Z0-9]*([0-9]{2})[^A-Z0-9]*([A-Z]{3})', r'D[^A-Z0-9]*([0-9]{4}[A-Z]{1})'],
            
            # Virginia: 3 letters + 4 numbers or various personalized formats
            'VA': [r'([A-Z]{3})[^A-Z0-9]*([0-9]{4})'],
            
            # Washington: 3 letters + 4 numbers or personalized
            'WA': [r'([A-Z]{3})[^A-Z0-9]*([0-9]{4})'],
            
            # Massachusetts: 3 numbers + 3 letters or personalized
            'MA': [r'([0-9]{3})[^A-Z0-9]*([A-Z]{3})'],
            
            # Arizona: 3 letters + 4 numbers or personalized
            'AZ': [r'([A-Z]{3})[^A-Z0-9]*([0-9]{4})'],
            
            # Indiana: 3 letters + 3 numbers or personalized
            'IN': [r'([A-Z]{3})[^A-Z0-9]*([0-9]{3})'],
            
            # Tennessee: 3 letters + 4 numbers
            'TN': [r'([A-Z]{3})[^A-Z0-9]*([0-9]{4})'],
            
            # Missouri: 3 letters + 3 numbers or personalized
            'MO': [r'([A-Z]{3})[^A-Z0-9]*([0-9]{3}[A-Z]?)'],
            
            # Maryland: 3 letters + 3 numbers or personalized
            'MD': [r'([A-Z]{3})[^A-Z0-9]*([0-9]{3})'],
            
            # Wisconsin: 3 letters + 4 numbers or personalized
            'WI': [r'([A-Z]{3})[^A-Z0-9]*([0-9]{4})'],
            
            # Minnesota: 3 letters + 3 numbers or personalized
            'MN': [r'([A-Z]{3})[^A-Z0-9]*([0-9]{3})'],
            
            # Colorado: 3 letters + 3 numbers or personalized
            'CO': [r'([A-Z]{3})[^A-Z0-9]*([0-9]{3})'],
            
            # Alabama: 1-2 numbers + 1-3 letters + optional number
            'AL': [r'([0-9]{1,2})[^A-Z0-9]*([A-Z]{1,3})([0-9]?)'],
            
            # South Carolina: 3 letters + 3 numbers or personalized
            'SC': [r'([A-Z]{3})[^A-Z0-9]*([0-9]{3})'],
            
            # Louisiana: 3 letters + 4 numbers or personalized
            'LA': [r'([A-Z]{3})[^A-Z0-9]*([0-9]{4})'],
            
            # Kentucky: 3 letters + 3 numbers or personalized
            'KY': [r'([A-Z]{3})[^A-Z0-9]*([0-9]{3})'],
            
            # Oregon: 3 letters + 3 numbers or personalized
            'OR': [r'([A-Z]{3})[^A-Z0-9]*([0-9]{3})'],
            
            # Oklahoma: 3 letters + 3 numbers or personalized
            'OK': [r'([A-Z]{3})[^A-Z0-9]*([0-9]{3})'],
            
            # Connecticut: 3 letters + 4 numbers or personalized
            'CT': [r'([A-Z]{3})[^A-Z0-9]*([0-9]{4})'],
            
            # Iowa: 3 letters + 3 numbers or personalized
            'IA': [r'([A-Z]{3})[^A-Z0-9]*([0-9]{3})'],
            
            # Generic patterns that match common formats across multiple states
            'GENERIC': [
                # 3 letters + 3-4 numbers (most common)
                r'([A-Z]{3})[^A-Z0-9]*([0-9]{3,4})',
                
                # 1-3 letters + 3-5 numbers
                r'([A-Z]{1,3})[^A-Z0-9]*([0-9]{3,5})',
                
                # 3-4 numbers + 1-3 letters
                r'([0-9]{3,4})[^A-Z0-9]*([A-Z]{1,3})',
                
                # 1 number + 3 letters + 3 numbers (CA style)
                r'([0-9]{1})[^A-Z0-9]*([A-Z]{3})[^A-Z0-9]*([0-9]{3})',
                
                # Any text that looks like it could be a plate (fallback)
                r'([A-Z0-9]{5,8})'
            ]
        }
        
        # Common dealership/frame text to filter out
        self.common_frame_text = [
            "dealer", "dealership", "auto", "group", "motors", "toyota", 
            "honda", "ford", "chevrolet", "chevy", "nissan", "hyundai", 
            "kia", "subaru", "dodge", "jeep", "lexus", "audi", "bmw", 
            "mercedes", "volkswagen", "volvo", "mazda", "acura", "infiniti",
            "cadillac", "lincoln", "buick", "gmc", "chrysler", "fiat",
            "service", "sales", "parts", "collision", "center", "financing",
            "lease", "leasing", "rental", "used", "new", "certified",
            "university", "college", "alumni", "proud", "support", "owner",
            "visit", "call", "www", "http", ".com", ".net", ".org",
            "phone", "drive", "driving", "road", "street", "ave", "hwy",
            "tag", "frame", "holder", "license", "plate"
        ]
    
    def extract_plate_from_raw_text(self, raw_text: str, detected_state: Optional[str] = None) -> Tuple[str, float]:
        """
        Extract the most likely license plate number from raw OCR text.
        
        Args:
            raw_text: The raw text from OCR
            detected_state: The detected state code (TX, CA, etc.) if available
            
        Returns:
            Tuple of (extracted_plate, confidence_score)
        """
        # Clean the raw text
        clean_text = self._clean_raw_text(raw_text)
        
        # Split into words for analysis
        words = clean_text.split()
        
        # Filter out common dealership/frame text
        filtered_words = [word for word in words if not self._is_common_frame_text(word)]
        
        # Attempt to find plate using state-specific patterns
        if detected_state and detected_state in self.state_patterns:
            plate, confidence = self._find_plate_with_patterns(filtered_words, self.state_patterns[detected_state])
            if plate:
                return plate, confidence
        
        # If no match with state patterns or no state provided, try generic patterns
        plate, confidence = self._find_plate_with_patterns(filtered_words, self.state_patterns['GENERIC'])
        if plate:
            return plate, confidence
            
        # If still no match, look for alphanumeric strings of appropriate length
        for word in filtered_words:
            if self._is_likely_plate(word):
                return word, 0.4  # Lower confidence for this fallback method
                
        # Last resort: return the longest alphanumeric string
        alphanumeric_words = [word for word in filtered_words if any(c.isalnum() for c in word)]
        if alphanumeric_words:
            longest_word = max(alphanumeric_words, key=len)
            if len(longest_word) >= 4:  # Minimum reasonable length for a plate
                return longest_word, 0.3
        
        # If nothing looks like a plate, return empty with zero confidence
        return "", 0.0
    
    def _clean_raw_text(self, raw_text: str) -> str:
        """Clean up raw text by removing unwanted characters and normalizing spacing."""
        # Convert to uppercase for consistency
        text = raw_text.upper()
        
        # Replace common OCR mistakes
        text = text.replace('0', 'O').replace('1', 'I').replace('5', 'S')
        
        # Replace certain punctuation with spaces to help with word separation
        for char in '.,;:\'"|\\/<>[](){}':
            text = text.replace(char, ' ')
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        return text
    
    def _is_common_frame_text(self, word: str) -> bool:
        """Check if word is likely to be common dealership or frame text."""
        word_lower = word.lower()
        
        # Check against our list of common frame text
        for frame_text in self.common_frame_text:
            if frame_text in word_lower:
                return True
                
        # Very short words are unlikely to be plates
        if len(word) < 4:
            return True
            
        return False
    
    def _find_plate_with_patterns(self, words: List[str], patterns: List[str]) -> Tuple[str, float]:
        """Try to find a license plate match using the provided regex patterns."""
        for word in words:
            for pattern in patterns:
                match = re.match(pattern, word)
                if match:
                    # Reconstruct the plate without the separators
                    plate = ''.join(match.groups())
                    
                    # Calculate confidence based on match quality
                    confidence = self._calculate_confidence(plate, pattern)
                    
                    return plate, confidence
                    
        # Also try to match patterns across adjacent words (for when OCR splits a plate)
        text = ' '.join(words)
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                # Take the first match
                if isinstance(matches[0], tuple):
                    plate = ''.join(matches[0])
                else:
                    plate = matches[0]
                    
                confidence = self._calculate_confidence(plate, pattern)
                return plate, confidence
                
        return "", 0.0
    
    def _calculate_confidence(self, plate: str, pattern: str) -> float:
        """Calculate a confidence score for the plate match."""
        # Base confidence
        confidence = 0.7
        
        # Adjust based on plate length (most plates are 5-8 characters)
        if 6 <= len(plate) <= 7:
            confidence += 0.1
        elif len(plate) < 5 or len(plate) > 8:
            confidence -= 0.1
            
        # Penalize unusual character distributions
        letter_count = sum(1 for c in plate if c.isalpha())
        number_count = sum(1 for c in plate if c.isdigit())
        
        # Most plates have a mix of letters and numbers
        if letter_count == 0 or number_count == 0:
            confidence -= 0.2
            
        # Specialized pattern matching gives higher confidence
        if pattern in self.state_patterns.get('GENERIC', []):
            confidence -= 0.1  # Generic patterns are less reliable
            
        # Ensure confidence is between 0 and 1
        return max(0.0, min(1.0, confidence))
    
    def _is_likely_plate(self, word: str) -> bool:
        """Check if a word is likely to be a license plate based on characteristics."""
        # Minimum length for a reasonable plate
        if len(word) < 5 or len(word) > 8:
            return False
            
        # Should contain at least some alphanumeric characters
        if not any(c.isalnum() for c in word):
            return False
            
        # Most plates have both letters and numbers
        has_letters = any(c.isalpha() for c in word)
        has_numbers = any(c.isdigit() for c in word)
        
        if not (has_letters and has_numbers):
            # Some vanity plates might be all letters
            if has_letters and len(word) >= 5:
                return True
            return False
            
        return True

# Example usage
def process_detection_result(detection_data):
    """Process a detection result to extract the most likely license plate."""
    processor = LicensePlateProcessor()
    
    # Extract relevant information from the detection
    raw_text = detection_data.get('detection', {}).get('raw_text', '')
    detected_state = detection_data.get('detection', {}).get('state')
    
    # Get current plate text and confidence
    current_plate = detection_data.get('detection', {}).get('plate_text', '')
    current_confidence = detection_data.get('detection', {}).get('confidence', 0)
    
    # Process with our enhanced algorithm
    extracted_plate, new_confidence = processor.extract_plate_from_raw_text(raw_text, detected_state)
    
    print(f"Raw Text: {raw_text}")
    print(f"Current Plate: {current_plate} (Confidence: {current_confidence:.2f})")
    print(f"Extracted Plate: {extracted_plate} (Confidence: {new_confidence:.2f})")
    
    # Choose the better result
    if new_confidence > current_confidence:
        return extracted_plate, new_confidence
    else:
        return current_plate, current_confidence

# Example with your Texas plate
example_detection = {
    "detection_id": "5ae691ea-5d5a-45a2-bf85-da54c145eeba",
    "timestamp": 1748932157.418994,
    "detection": {
        "plate_text": "CETOYOIA",
        "confidence": 0.39449080752660914,
        "ocr_confidence": 0.4931135094082614,
        "state": "TX",
        "raw_text": "Purdy Group TEXAS VBR-7660 STATION BAYAN COLLECE Toyota",
        "box": [189, 106, 480, 273],
        "detection_confidence": 0.8737747669219971,
        "timestamp": 1748932157.418994
    }
}

# Process the example
best_plate, confidence = process_detection_result(example_detection)
print(f"\nBest license plate: {best_plate} (Confidence: {confidence:.2f})")
