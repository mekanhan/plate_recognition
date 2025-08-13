"""
Quality Metrics for License Plate Detection
Includes POP (Pixels-On-Plate) and other quality control measures
"""
import cv2
import numpy as np
from typing import List, Dict, Tuple
import logging


class QualityMetrics:
    """Calculate quality metrics for license plate detections"""
    
    def __init__(self):
        self.logger = logging.getLogger("QualityMetrics")
        
        # POP thresholds for quality classification
        self.pop_thresholds = {
            'excellent': 2000,   # >= 2000 pixels (e.g., 50x40)
            'good': 1200,        # >= 1200 pixels (e.g., 40x30)
            'fair': 600,         # >= 600 pixels (e.g., 30x20)
            'poor': 300          # >= 300 pixels (e.g., 20x15)
            # < 300 pixels = unusable
        }
    
    def calculate_pop_metrics(self, frame: np.ndarray, plate_bbox: List[int]) -> Dict:
        """
        Calculate Pixels-On-Plate (POP) metrics for quality assessment
        
        Args:
            frame: Input image
            plate_bbox: License plate bounding box [x1, y1, x2, y2]
            
        Returns:
            Dict with POP metrics and quality assessment
        """
        if not plate_bbox or len(plate_bbox) != 4:
            return self._empty_pop_metrics()
        
        x1, y1, x2, y2 = plate_bbox
        
        # Validate coordinates
        if x2 <= x1 or y2 <= y1:
            return self._empty_pop_metrics()
        
        # Calculate basic dimensions
        width = x2 - x1
        height = y2 - y1
        total_pixels = width * height
        
        # Extract plate region for detailed analysis
        try:
            plate_region = frame[y1:y2, x1:x2]
            if plate_region.size == 0:
                return self._empty_pop_metrics()
        except (IndexError, ValueError):
            return self._empty_pop_metrics()
        
        # Calculate additional quality metrics
        sharpness = self._calculate_sharpness(plate_region)
        contrast = self._calculate_contrast(plate_region)
        brightness = self._calculate_brightness(plate_region)
        aspect_ratio = width / height if height > 0 else 0
        
        # Determine quality level based on POP
        quality_level = self._classify_quality(total_pixels)
        
        # Calculate quality score (0-100)
        quality_score = self._calculate_quality_score(
            total_pixels, sharpness, contrast, brightness, aspect_ratio
        )
        
        return {
            'total_pixels': total_pixels,
            'width': width,
            'height': height,
            'aspect_ratio': round(aspect_ratio, 2),
            'quality_level': quality_level,
            'quality_score': round(quality_score, 1),
            'sharpness': round(sharpness, 2),
            'contrast': round(contrast, 2),
            'brightness': round(brightness, 2),
            'meets_minimum_quality': quality_score >= 60,
            'recommended_for_ocr': total_pixels >= self.pop_thresholds['fair'] and quality_score >= 70
        }
    
    def _empty_pop_metrics(self) -> Dict:
        """Return empty metrics for invalid inputs"""
        return {
            'total_pixels': 0,
            'width': 0,
            'height': 0,
            'aspect_ratio': 0,
            'quality_level': 'unusable',
            'quality_score': 0,
            'sharpness': 0,
            'contrast': 0,
            'brightness': 0,
            'meets_minimum_quality': False,
            'recommended_for_ocr': False
        }
    
    def _classify_quality(self, total_pixels: int) -> str:
        """Classify quality level based on total pixels"""
        if total_pixels >= self.pop_thresholds['excellent']:
            return 'excellent'
        elif total_pixels >= self.pop_thresholds['good']:
            return 'good'
        elif total_pixels >= self.pop_thresholds['fair']:
            return 'fair'
        elif total_pixels >= self.pop_thresholds['poor']:
            return 'poor'
        else:
            return 'unusable'
    
    def _calculate_sharpness(self, image: np.ndarray) -> float:
        """Calculate image sharpness using Laplacian variance"""
        try:
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Calculate Laplacian variance
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            return float(laplacian.var())
        except Exception:
            return 0.0
    
    def _calculate_contrast(self, image: np.ndarray) -> float:
        """Calculate image contrast using standard deviation"""
        try:
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            return float(gray.std())
        except Exception:
            return 0.0
    
    def _calculate_brightness(self, image: np.ndarray) -> float:
        """Calculate average brightness"""
        try:
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            return float(gray.mean())
        except Exception:
            return 0.0
    
    def _calculate_quality_score(self, total_pixels: int, sharpness: float, 
                               contrast: float, brightness: float, aspect_ratio: float) -> float:
        """
        Calculate overall quality score (0-100) based on multiple factors
        """
        # POP score (40% weight)
        pop_score = min(100, (total_pixels / self.pop_thresholds['excellent']) * 100)
        
        # Sharpness score (25% weight) - normalize based on typical values
        sharpness_score = min(100, (sharpness / 100) * 100)
        
        # Contrast score (20% weight) - normalize based on typical values
        contrast_score = min(100, (contrast / 50) * 100)
        
        # Brightness score (10% weight) - optimal range 80-180
        if 80 <= brightness <= 180:
            brightness_score = 100
        else:
            brightness_score = max(0, 100 - abs(brightness - 130) * 2)
        
        # Aspect ratio score (5% weight) - license plates typically 2:1 to 4:1
        if 1.5 <= aspect_ratio <= 5.0:
            aspect_score = 100
        else:
            aspect_score = max(0, 100 - abs(aspect_ratio - 3.0) * 20)
        
        # Weighted average
        quality_score = (
            pop_score * 0.40 +
            sharpness_score * 0.25 +
            contrast_score * 0.20 +
            brightness_score * 0.10 +
            aspect_score * 0.05
        )
        
        return min(100, max(0, quality_score))
    
    def filter_by_quality(self, detections: List[Dict], min_quality_score: float = 60) -> List[Dict]:
        """
        Filter detections based on quality score
        
        Args:
            detections: List of detection dictionaries with 'pop_metrics' field
            min_quality_score: Minimum quality score to keep (0-100)
            
        Returns:
            Filtered list of detections
        """
        filtered = []
        
        for detection in detections:
            pop_metrics = detection.get('pop_metrics', {})
            quality_score = pop_metrics.get('quality_score', 0)
            
            if quality_score >= min_quality_score:
                filtered.append(detection)
            else:
                self.logger.debug(f"Filtered out detection with quality score {quality_score}")
        
        return filtered
    
    def get_quality_statistics(self, detections: List[Dict]) -> Dict:
        """
        Calculate quality statistics for a batch of detections
        
        Args:
            detections: List of detection dictionaries with 'pop_metrics' field
            
        Returns:
            Dictionary with quality statistics
        """
        if not detections:
            return {
                'total_detections': 0,
                'quality_levels': {},
                'average_pop': 0,
                'average_quality_score': 0,
                'high_quality_percentage': 0
            }
        
        quality_levels = {'excellent': 0, 'good': 0, 'fair': 0, 'poor': 0, 'unusable': 0}
        total_pop = 0
        total_quality_score = 0
        high_quality_count = 0
        
        for detection in detections:
            pop_metrics = detection.get('pop_metrics', {})
            
            quality_level = pop_metrics.get('quality_level', 'unusable')
            quality_levels[quality_level] += 1
            
            total_pop += pop_metrics.get('total_pixels', 0)
            
            quality_score = pop_metrics.get('quality_score', 0)
            total_quality_score += quality_score
            
            if quality_score >= 80:
                high_quality_count += 1
        
        total_count = len(detections)
        
        return {
            'total_detections': total_count,
            'quality_levels': quality_levels,
            'average_pop': round(total_pop / total_count, 1) if total_count > 0 else 0,
            'average_quality_score': round(total_quality_score / total_count, 1) if total_count > 0 else 0,
            'high_quality_percentage': round((high_quality_count / total_count) * 100, 1) if total_count > 0 else 0
        }