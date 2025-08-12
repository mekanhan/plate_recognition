"""
License Plate Validator
Validates and formats license plate text based on regional patterns
"""
import re
import logging
from typing import Tuple, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class PlateRegion(Enum):
    US = "US"
    CA = "CA"  # Canada
    EU = "EU"  # European Union
    UK = "UK"
    GENERIC = "GENERIC"


@dataclass
class ValidationResult:
    """Result of plate validation"""
    is_valid: bool
    formatted_text: str
    confidence_adjustment: float  # Multiplier for OCR confidence
    detected_region: Optional[PlateRegion]
    validation_issues: list
    suggested_corrections: list


class PlateValidator:
    """Validates license plate text and formats according to regional standards"""
    
    def __init__(self, default_region: PlateRegion = PlateRegion.US):
        self.logger = logging.getLogger("PlateValidator")
        self.default_region = default_region
        
        # US state patterns (most common)
        self.us_patterns = {
            # Standard format: 3 letters + 3-4 numbers or vice versa
            'standard': [
                r'^[A-Z]{3}[0-9]{3,4}$',  # ABC123, ABC1234
                r'^[0-9]{3}[A-Z]{3}$',    # 123ABC
                r'^[A-Z]{2}[0-9]{4}$',    # AB1234
                r'^[0-9]{2}[A-Z]{4}$',    # 12ABCD
            ],
            # Specialty patterns
            'specialty': [
                r'^[A-Z]{4}[0-9]{3}$',    # ABCD123 (specialty)
                r'^[A-Z]{1}[0-9]{6}$',    # A123456 (commercial)
                r'^[A-Z]{6}$',            # ABCDEF (vanity)
                r'^[0-9]{6}$',            # 123456 (numeric)
            ]
        }
        
        # Common OCR misreads
        self.character_corrections = {
            '0': ['O', 'Q', 'D'],
            'O': ['0', 'Q', 'D'],
            '1': ['I', 'L', '|'],
            'I': ['1', 'L', '|'],
            'L': ['1', 'I', '|'],
            '5': ['S'],
            'S': ['5'],
            '6': ['G', 'B'],
            'G': ['6', 'C'],
            '8': ['B'],
            'B': ['8', '6'],
            '2': ['Z'],
            'Z': ['2'],
        }
        
        # Invalid/noise patterns
        self.noise_patterns = [
            r'^(TEXAS|CALIFORNIA|FLORIDA|STATE|DEALER|EXEMPT|VETERAN|DISABLED)$',
            r'^[A-Z\s]+STATE[A-Z\s]*$',  # State names
            r'^[A-Z\s]*COUNTY[A-Z\s]*$',  # County names
            r'^(TEMP|TEMPORARY|PAPER)$',   # Temporary plates
            r'^[A-Z]*\d{0,2}$',           # Too few characters
            r'^(.)\1{3,}$',               # Repeated characters (AAAA, 1111)
        ]
        
        # Regional specific patterns
        self.regional_patterns = {
            PlateRegion.US: self.us_patterns,
            PlateRegion.CA: {
                'standard': [r'^[A-Z]{3}[0-9]{4}$', r'^[0-9]{3}[A-Z]{3}$']
            },
            PlateRegion.EU: {
                'standard': [r'^[A-Z]{2}[0-9]{2}[A-Z]{3}$']  # Simplified EU pattern
            }
        }
    
    def validate_plate(self, raw_text: str, region: Optional[PlateRegion] = None) -> ValidationResult:
        """
        Validate and format license plate text
        
        Args:
            raw_text: Raw OCR text
            region: Target region for validation
            
        Returns:
            ValidationResult with validation outcome and suggestions
        """
        if not raw_text:
            return ValidationResult(
                is_valid=False,
                formatted_text="",
                confidence_adjustment=0.0,
                detected_region=None,
                validation_issues=["Empty text"],
                suggested_corrections=[]
            )
        
        # Clean and normalize text
        cleaned_text = self._clean_text(raw_text)
        region = region or self.default_region
        
        # Check for noise patterns first
        if self._is_noise_plate(cleaned_text):
            return ValidationResult(
                is_valid=False,
                formatted_text=cleaned_text,
                confidence_adjustment=0.1,  # Very low confidence
                detected_region=region,
                validation_issues=["Detected as noise/invalid plate"],
                suggested_corrections=[]
            )
        
        # Validate against regional patterns
        validation_result = self._validate_regional_pattern(cleaned_text, region)
        
        # Apply character corrections if needed
        if not validation_result.is_valid:
            corrected_result = self._try_character_corrections(cleaned_text, region)
            if corrected_result.is_valid:
                validation_result = corrected_result
                validation_result.validation_issues.append("Applied character corrections")
        
        # Final formatting
        validation_result.formatted_text = self._format_plate_text(
            validation_result.formatted_text, region
        )
        
        return validation_result
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize raw OCR text"""
        # Remove common OCR artifacts
        text = re.sub(r'[^A-Z0-9]', '', text.upper())
        
        # Remove common prefixes/suffixes that aren't part of plate
        text = re.sub(r'^(THE|LICENSE|PLATE|NUMBER)', '', text)
        text = re.sub(r'(STATE|USA|AMERICA)$', '', text)
        
        return text.strip()
    
    def _is_noise_plate(self, text: str) -> bool:
        """Check if text matches noise patterns"""
        for pattern in self.noise_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _validate_regional_pattern(self, text: str, region: PlateRegion) -> ValidationResult:
        """Validate text against regional patterns"""
        patterns = self.regional_patterns.get(region, self.us_patterns)
        issues = []
        confidence_adj = 1.0
        
        # Check standard patterns first
        for pattern in patterns.get('standard', []):
            if re.match(pattern, text):
                return ValidationResult(
                    is_valid=True,
                    formatted_text=text,
                    confidence_adjustment=1.0,
                    detected_region=region,
                    validation_issues=[],
                    suggested_corrections=[]
                )
        
        # Check specialty patterns with lower confidence
        for pattern in patterns.get('specialty', []):
            if re.match(pattern, text):
                return ValidationResult(
                    is_valid=True,
                    formatted_text=text,
                    confidence_adjustment=0.8,  # Lower confidence for specialty
                    detected_region=region,
                    validation_issues=["Specialty plate format"],
                    suggested_corrections=[]
                )
        
        # Length validation
        if len(text) < 4:
            issues.append("Too short for valid license plate")
            confidence_adj *= 0.3
        elif len(text) > 8:
            issues.append("Too long for standard license plate")
            confidence_adj *= 0.5
        
        # Character composition validation
        if not re.search(r'[A-Z]', text):
            issues.append("No letters detected")
            confidence_adj *= 0.4
        elif not re.search(r'[0-9]', text):
            issues.append("No numbers detected - possible vanity plate")
            confidence_adj *= 0.7
        
        return ValidationResult(
            is_valid=len(issues) == 0 or confidence_adj > 0.5,
            formatted_text=text,
            confidence_adjustment=confidence_adj,
            detected_region=region,
            validation_issues=issues,
            suggested_corrections=[]
        )
    
    def _try_character_corrections(self, text: str, region: PlateRegion) -> ValidationResult:
        """Try common OCR character corrections"""
        best_result = ValidationResult(
            is_valid=False, formatted_text=text, confidence_adjustment=0.0,
            detected_region=region, validation_issues=["No valid corrections found"],
            suggested_corrections=[]
        )
        
        # Generate correction candidates
        candidates = self._generate_correction_candidates(text)
        
        for candidate in candidates[:10]:  # Limit to top 10 candidates
            result = self._validate_regional_pattern(candidate, region)
            if result.is_valid and result.confidence_adjustment > best_result.confidence_adjustment:
                best_result = result
                best_result.confidence_adjustment *= 0.8  # Reduce confidence for corrections
                best_result.suggested_corrections.append(f"Corrected '{text}' to '{candidate}'")
        
        return best_result
    
    def _generate_correction_candidates(self, text: str) -> list:
        """Generate potential corrections for common OCR errors"""
        candidates = []
        
        # Single character corrections
        for i, char in enumerate(text):
            if char in self.character_corrections:
                for replacement in self.character_corrections[char]:
                    candidate = text[:i] + replacement + text[i+1:]
                    candidates.append(candidate)
        
        # Remove/add single characters for length issues
        if len(text) > 4:
            # Try removing each character
            for i in range(len(text)):
                candidate = text[:i] + text[i+1:]
                candidates.append(candidate)
        
        return list(set(candidates))  # Remove duplicates
    
    def _format_plate_text(self, text: str, region: PlateRegion) -> str:
        """Format plate text according to regional conventions"""
        if region == PlateRegion.US:
            # US plates typically have no spaces in database storage
            return text.replace(' ', '').upper()
        elif region == PlateRegion.CA:
            # Canadian plates often have spaces (ABC 123)
            if len(text) == 6 and text.isalnum():
                return f"{text[:3]} {text[3:]}".upper()
        
        return text.upper()
    
    def get_confidence_multiplier(self, validation_result: ValidationResult) -> float:
        """Get confidence multiplier to apply to OCR confidence"""
        if not validation_result.is_valid:
            return 0.1  # Heavily penalize invalid plates
        
        multiplier = validation_result.confidence_adjustment
        
        # Apply additional penalties
        if validation_result.validation_issues:
            multiplier *= 0.9  # Small penalty for issues
        
        if validation_result.suggested_corrections:
            multiplier *= 0.7  # Larger penalty for corrections
        
        return max(0.1, min(1.0, multiplier))  # Clamp between 0.1 and 1.0