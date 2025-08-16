"""
Feature Flag Management System
Centralized configuration for enabling/disabling detection features
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import os

logger = logging.getLogger(__name__)

class FeatureFlags:
    """Feature flag manager for detection system configuration"""
    
    def __init__(self, config_path: str = "config/features.json"):
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self):
        """Load feature flags from JSON configuration file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    self._config = json.load(f)
                logger.info(f"Feature flags loaded from {self.config_path}")
            else:
                # Create default config if it doesn't exist
                self._create_default_config()
                logger.warning(f"Created default feature config at {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to load feature config: {e}")
            self._config = self._get_default_config()
    
    def _create_default_config(self):
        """Create default feature configuration"""
        default_config = self._get_default_config()
        os.makedirs(self.config_path.parent, exist_ok=True)
        
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        self._config = default_config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default feature configuration"""
        return {
            "detection_features": {
                "license_plate_detection": True,
                "universal_detection": False,
                "vehicle_detection": False,
                "object_detection": False
            },
            "api_features": {
                "universal_detection_endpoints": False,
                "legacy_detection_endpoints": True
            },
            "processing_features": {
                "smart_deduplication": True,
                "storage_management": True,
                "continuous_processing": True
            }
        }
    
    def is_enabled(self, feature_path: str) -> bool:
        """
        Check if a feature is enabled
        
        Args:
            feature_path: Dot notation path like 'detection_features.license_plate_detection'
        
        Returns:
            bool: True if feature is enabled, False otherwise
        """
        try:
            keys = feature_path.split('.')
            value = self._config
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    logger.warning(f"Feature flag '{feature_path}' not found, defaulting to False")
                    return False
            
            return bool(value)
            
        except Exception as e:
            logger.error(f"Error checking feature flag '{feature_path}': {e}")
            return False
    
    def get_enabled_detection_types(self) -> list[str]:
        """Get list of enabled detection types"""
        enabled = []
        detection_features = self._config.get('detection_features', {})
        
        for feature, enabled_flag in detection_features.items():
            if enabled_flag:
                enabled.append(feature)
        
        return enabled
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get summary of current feature configuration"""
        return {
            "enabled_detection_features": [
                feature for feature, enabled in self._config.get('detection_features', {}).items() 
                if enabled
            ],
            "enabled_api_features": [
                feature for feature, enabled in self._config.get('api_features', {}).items() 
                if enabled
            ],
            "enabled_processing_features": [
                feature for feature, enabled in self._config.get('processing_features', {}).items() 
                if enabled
            ],
            "config_path": str(self.config_path)
        }
    
    def reload_config(self):
        """Reload configuration from file"""
        self._load_config()
        logger.info("Feature flags reloaded")

# Global feature flags instance
feature_flags = FeatureFlags()

# Convenience functions
def is_license_plate_detection_enabled() -> bool:
    """Check if license plate detection is enabled"""
    return feature_flags.is_enabled('detection_features.license_plate_detection')

def is_universal_detection_enabled() -> bool:
    """Check if universal detection is enabled"""
    return feature_flags.is_enabled('detection_features.universal_detection')

def is_universal_endpoints_enabled() -> bool:
    """Check if universal detection API endpoints are enabled"""
    return feature_flags.is_enabled('api_features.universal_detection_endpoints')

def is_continuous_processing_enabled() -> bool:
    """Check if continuous processing is enabled"""
    return feature_flags.is_enabled('processing_features.continuous_processing')

def get_detection_config_summary() -> Dict[str, Any]:
    """Get detection configuration summary"""
    return feature_flags.get_config_summary()