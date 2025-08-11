"""
AI Features Core Module
Contains base classes and types used across all AI features
"""

from .types import Detection, VehicleInfo, PlateInfo, ProcessingResult
from .base_model import BaseAIModel

__all__ = [
    'Detection',
    'VehicleInfo', 
    'PlateInfo',
    'ProcessingResult',
    'BaseAIModel'
]