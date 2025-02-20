import cv2
import os
import sys
import torch
from ultralytics import YOLO
import easyocr
import subprocess
import time

# Get the root folder of the project and add to sys.path
root_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(root_folder)

# Import scrcpy from utils
from utils.scrcpy import start_scrcpy

def load_model():
    """Load YOLO model from models/ folder and auto-detect GPU availability."""
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}")
    return YOLO(os.path.join(root_folder, 'models', 'yolo11m_best.pt')).to(device)

# Initialize EasyOCR Reader
reader = easyocr.Reader(['en'])

# Load YOLO model with automatic device selection
model = load_model()

def list_connected_devices():
    """List connected devices using ADB."""
    try:
        devices = subprocess.check_output(["adb", "devices"]).decode().splitlines()
        connected_devices = [line.split()[0] for line in devices if "\tdevice" in line]
        return connected_devices
    except subprocess.CalledProcessError as e:
        print("Error listing devices:", e)
        return []

def connect_to_device():
    """Check and connect to an available Android device via ADB (USB preferred)."""
    print("Checking for connected devices...")

    # List connected devices
    connected_devices = list_connected_devices()

    # Prefer USB connection (Lower latency)
    for device in connected_devices:
        # Check if the device is connected via USB
        if not device.startswith("10.0.168.") and not device.startswith("192.168."):
            print(f"USB device found: {device}")
            return device
    
    # No USB device found, trying to connect via Wi-Fi
    print("No USB device found. Trying to connect via Wi-Fi...")

    # Wi-Fi settings (Change this to your device's IP)
    device_ip = "10.0.0.81"  # Use your device's IP from adb shell ip route
    print(f"Attempting to connect to {device_ip} via Wi-Fi...")
    subprocess.run(["adb", "connect", f"{device_ip}:5555"])
    time.sleep(2)  # Give it a moment to connect

    # Check again after connecting via Wi-Fi
    connected_devices = list_connected_devices()
    if connected_devices:
        print(f"Connected device(s): {connected_devices}")
        return connected_devices[0]  # Return the first connected device
    else:
        print("Error: No devices connected. Make sure USB Debugging is enabled.")
        return None

def start_adb_stream():
    """Start ADB streaming using scrcpy and tail MP4 file in real-time"""
    # Start ADB server
    subprocess.run(["adb", "start-server"])

    # Connect to the device automatically (USB preferred, Wi-Fi fallback)
    device = connect_to_device()
    if device is None:
        return

    print("Starting ADB Screen Stream and recording to temp MP4 file...")

    # Start scrcpy streaming and get the recorded file path
    temp_file = start_scrcpy()
    if temp_file is None:
        return

    # Use OpenCV to read the recorded video file in real-time
    cap = cv2.VideoCapture(temp_file)

    # Retry mechanism for stream connection
    retries = 0
    while not cap.isOpened() and retries < 3:
        print("Error: Could not open recorded stream. Retrying in 3 seconds...")
        time.sleep(3)
        cap = cv2.VideoCapture(temp_file)
        retries += 1

    if not cap.isOpened():
        print("Error: Could not open recorded stream after multiple attempts.")
        return None
    
    return cap



def detect_and_read_license_plate_live():
    """Detect and read license plates live from ADB stream using MP4 recording"""
    # Start ADB streaming and read MP4 file
    cap = start_adb_stream()
    if cap is None:
        return

    # Process each frame
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame from recorded stream.")
            break
        
        # Run YOLOv8 inference on the frame
        results = model(frame)

        # Loop through the results and draw bounding boxes
        for result in results[0].boxes:
            x1, y1, x2, y2 = map(int, result.xyxy[0])
            conf = result.conf[0]
            class_id = int(result.cls[0])
            class_name = model.names[class_id]

            # Draw the bounding box and label on the frame
            label = f"{class_name}: {conf:.2f}"
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Crop the license plate area for OCR
            cropped_plate = frame[y1:y2, x1:x2]

            # Run EasyOCR on the cropped plate
            ocr_results = reader.readtext(cropped_plate)

            # Loop through OCR results and draw the text
            for bbox, text, conf in ocr_results:
                cv2.putText(frame, text, (x1, y2 + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                print(f"Detected Plate Text: {text}")

        # Show the frame live
        cv2.imshow('Live License Plate Detection - Press Q to exit', frame)

        # Press 'q' to exit the video window
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release resources
    cap.release()
    cv2.destroyAllWindows()
    print("ADB Stream Ended.")




# Run real-time license plate recognition from ADB stream
if __name__ == "__main__":
    detect_and_read_license_plate_live()
