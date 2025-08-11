"""
AI Features Package
Organized AI functionality for license plate recognition and vehicle intelligence
"""

from .core import Detection, BaseAIModel
from .vehicle import LicensePlateModel

__all__ = [
    'Detection',
    'BaseAIModel', 
    'LicensePlateModel'
]