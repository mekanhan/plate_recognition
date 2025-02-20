import cv2
import easyocr
import numpy as np
import re
import os
import time
import torch
from ultralytics import YOLO

def load_model():
    """Load YOLO model from models/ folder and auto-detect GPU availability."""
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}")
    return YOLO("models/yolov11m_best.pt").to(device)  # Use full path


# Load YOLO model with automatic device selection
model = load_model()

# Create output directory if it doesn't exist
os.makedirs("output_images", exist_ok=True)

# Initialize EasyOCR
reader = easyocr.Reader(['en'])

def clean_plate_text(text):
    """Cleans up the detected text to match license plate format."""
    text = re.sub(r'[^A-Z0-9]', '', text.upper())  # Keep only uppercase letters & numbers
    return text if len(text) >= 6 else None  # Minimum 6 characters

def detect_and_recognize_plate(image_path):
    """Detect license plates, extract text, and save processed images using OCR and YOLO correlation."""
    image = cv2.imread(image_path)
    results = model(image)[0]  # Run YOLOv8 detection
    timestamp = int(time.time())
    image_name = os.path.basename(image_path).split('.')[0]  # Get original image name without extension

    for result in results.boxes:
        x1, y1, x2, y2 = map(int, result.xyxy[0])
        cropped_plate = image[y1:y2, x1:x2]  # Crop detected plate
        
        # Run OCR only on the detected plate area
        ocr_results = reader.readtext(cropped_plate)
        
        for bbox, text, conf in ocr_results:
            text_cleaned = clean_plate_text(text)
            if text_cleaned:
                # Draw bounding box & text on the original image
                cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(image, text_cleaned, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                print(f"Detected Plate Text: {text_cleaned}")

    # Save the final processed image once with the original name and timestamp
    final_filename = f"output_images/{image_name}_{timestamp}.jpg"
    cv2.imwrite(final_filename, image)
    print(f"Processed image saved: {final_filename}")


def process_folder(folder_path):
    """Process all images in a given folder."""
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('png', 'jpg', 'jpeg')):
            image_path = os.path.join(folder_path, filename)
            detect_and_recognize_plate(image_path)

# Run detection on all images in the specified folder
process_folder("datasets/license_plate_data/test/images/")