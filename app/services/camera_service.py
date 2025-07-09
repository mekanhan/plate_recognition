import cv2
import logging
import os
import json
logger = logging.getLogger(__name__)

def get_available_cameras(max_cameras=10):
    """Get list of available camera indices"""
    available_cameras = []
    for i in range(max_cameras):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                available_cameras.append(i)
                cap.release()
        return available_cameras
    
class CameraService:
    def __init__(self, config=None):
        # Load camera config from file if available
        config_path = os.path.join('config', 'camera_config.json')
        self.config = {}

        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    self.config = json.load(f)
                logger.info(f"Loaded camera configuration from {config_path}")
            except Exception as e:
                logger.error(f"Error loading camera config: {e}")

        # Override with runtime config if provided
        if config:
            self.config.update(config)

        # Get camera source - handle string or int values
        camera_source = self.config.get('camera_source', 'auto')

        # Set camera index
        if camera_source == 'auto':
            self.camera_index = None  # Will auto-detect in initialize()
        elif isinstance(camera_source, str) and camera_source.isdigit():
            self.camera_index = int(camera_source)
        else:
            self.camera_index = camera_source

        # Camera object
        self.camera = None

        # Resolution settings
        resolution = self.config.get('resolution', {})
        self.width = resolution.get('width', 1280)
        self.height = resolution.get('height', 720)

        logger.info(f"Camera service initialized with source: {camera_source}")

    def initialize(self):
        """Initialize camera"""
        try:
            # Auto-detect if no specific camera is configured
            if self.camera_index is None:
                available_cameras = get_available_cameras()
                if available_cameras:
                    self.camera_index = available_cameras[0]
                    logger.info(f"Auto-detected camera at index {self.camera_index}")
                else:
                    logger.warning("No cameras detected! Using mock camera.")
                    self.camera_index = 0

            # Open camera
            self.camera = cv2.VideoCapture(self.camera_index)
                    
            # Set resolution if specified
            if self.width and self.height:
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

            # Check if camera opened successfully
            if not self.camera.isOpened():
                logger.error(f"Failed to open camera index: {self.camera_index}")
                return False

            logger.info(f"Camera initialized: {self.camera_index}")
            return True
        except Exception as e:
            logger.error(f"Error initializing camera: {e}")
            return False

    def get_frame(self):
        """Get frame from camera"""
        if self.camera is None or not self.camera.isOpened():
            if not self.initialize():
                # Return empty frame if camera isn't available
                return False, None

        # Read frame
        ret, frame = self.camera.read()
        return ret, frame

    def release(self):
        """Release camera resources"""
        if self.camera is not None:
            self.camera.release()
            self.camera = None
            logger.info("Camera released")
