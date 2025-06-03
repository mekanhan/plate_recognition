"""
Utility script to download a specialized license plate detection and recognition model.
"""
import os
import urllib.request
import sys

def download_license_plate_model():
    """Download specialized license plate YOLO model."""
    # Create models directory if it doesn't exist
    os.makedirs("app/models", exist_ok=True)
    
    # Path for the license plate model
    model_path = "app/models/license_plate_yolov8.pt"
    
    # Check if model already exists
    if os.path.exists(model_path):
        print(f"Model already exists at {model_path}")
        return model_path
    
    # Download the model
    # This is a YOLOv8 model fine-tuned on license plates from Roboflow Universe
    model_url = "https://github.com/RizwanMunawar/yolov8-license-plate-recognition/releases/download/license-plate/license_plate_detector_yolov8n.pt"
    
    print(f"Downloading license plate model from {model_url}...")
    try:
        urllib.request.urlretrieve(model_url, model_path)
        print(f"Model downloaded successfully to {model_path}")
        return model_path
    except Exception as e:
        print(f"Error downloading model: {e}")
        return None

if __name__ == "__main__":
    download_license_plate_model()