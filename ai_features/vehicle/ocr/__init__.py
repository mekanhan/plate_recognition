"""
OCR module for license plate text recognition
"""
from .plate_validator import PlateValidator, PlateRegion, ValidationResult
from .enhanced_ocr import EnhancedOCRProcessor

__all__ = ['PlateValidator', 'PlateRegion', 'ValidationResult', 'EnhancedOCRProcessor']