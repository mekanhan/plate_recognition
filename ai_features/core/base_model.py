"""
Base AI Model Class
Abstract base for all AI models with common functionality
"""
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

# Conditional imports - only import when actually needed
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

class BaseAIModel(ABC):
    """Abstract base class for all AI models"""
    
    def __init__(self, model_path: str = None, device: str = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.model_path = model_path
        self.device = self._detect_device(device)
        self.model = None
        self.is_loaded = False
        self.load_time = None
        
        self.logger.info(f"Initializing {self.__class__.__name__} on device: {self.device}")
    
    def _detect_device(self, device: str = None) -> str:
        """Auto-detect best available device"""
        if device:
            return device
        
        if TORCH_AVAILABLE and torch.cuda.is_available():
            return "cuda"
        else:
            return "cpu"
    
    @abstractmethod
    def _load_model(self) -> Any:
        """Load the AI model - implemented by subclasses"""
        pass
    
    @abstractmethod
    def predict(self, input_data: Any) -> Any:
        """Run prediction - implemented by subclasses"""
        pass
    
    def load(self) -> bool:
        """Load the model if not already loaded"""
        if self.is_loaded:
            return True
        
        try:
            start_time = time.time()
            self.model = self._load_model()
            self.load_time = time.time() - start_time
            self.is_loaded = True
            
            self.logger.info(f"Model loaded successfully in {self.load_time:.2f}s")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            return False
    
    def preprocess_image(self, image):
        """Common image preprocessing"""
        if not CV2_AVAILABLE:
            self.logger.warning("OpenCV not available for image preprocessing")
            return image
            
        if image is None:
            return None
            
        # Ensure image is in correct format
        if len(image.shape) == 3 and image.shape[2] == 3:
            # BGR to RGB if needed
            if hasattr(self, 'requires_rgb') and self.requires_rgb:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        return image
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            'model_class': self.__class__.__name__,
            'model_path': self.model_path,
            'device': self.device,
            'is_loaded': self.is_loaded,
            'load_time': self.load_time
        }
    
    def measure_inference_time(self, func, *args, **kwargs):
        """Measure inference time for a function"""
        start_time = time.time()
        result = func(*args, **kwargs)
        inference_time = (time.time() - start_time) * 1000  # Convert to ms
        return result, inference_time