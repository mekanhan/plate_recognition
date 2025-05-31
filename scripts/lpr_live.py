#!/usr/bin/env python3
import cv2
import easyocr
import numpy as np
import re
import os
import time
import torch
import json
import datetime
from ultralytics import YOLO
import argparse
from typing import Optional, Tuple, List, Dict, Any

def load_model() -> YOLO:
    """
    Load YOLO model from models/ folder and auto-detect GPU availability.
    
    Returns:
        YOLO: Loaded model on the appropriate device
    """
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}")
    return YOLO("models/yolo11m_best.pt").to(device)

def clean_plate_text(text: str) -> Optional[str]:
    """
    Cleans up the detected text to match license plate format.
    
    Args:
        text: Raw text from OCR
        
    Returns:
        Cleaned text or None if text is too short
    """
    text = re.sub(r'[^A-Z0-9]', '', text.upper())  # Keep only uppercase letters & numbers
    return text if len(text) >= 6 else None  # Minimum 6 characters

def detect_and_recognize_plate(frame: np.ndarray, model: YOLO, reader: easyocr.Reader) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    """
    Detect license plates and extract text using OCR and YOLO.
    
    Args:
        frame: Current video frame
        model: YOLO model for detection
        reader: EasyOCR reader for text recognition
        
    Returns:
        Tuple of processed frame and list of detected plate details
    """
    results = model(frame)[0]  # Run YOLOv8 detection
    detected_plates = []
    
    for result in results.boxes:
        x1, y1, x2, y2 = map(int, result.xyxy[0])
        conf = float(result.conf[0])
        class_id = int(result.cls[0])
        class_name = model.names[class_id]
        
        # Draw bounding box for license plate
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        cropped_plate = frame[y1:y2, x1:x2]  # Crop detected plate
        
        # Skip if cropped area is too small
        if cropped_plate.size == 0 or cropped_plate.shape[0] < 15 or cropped_plate.shape[1] < 15:
            continue
        
        # Run OCR only on the detected plate area
        ocr_results = reader.readtext(cropped_plate)
        
        for bbox, text, ocr_conf in ocr_results:
            text_cleaned = clean_plate_text(text)
            if text_cleaned:
                # Draw text on the original frame
                cv2.putText(frame, text_cleaned, (x1, y1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                
                # Create detection record with all relevant details
                detection = {
                    "plate_text": text_cleaned,
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "unix_timestamp": time.time(),
                    "ocr_confidence": float(ocr_conf),
                    "detection_confidence": conf,
                    "class_name": class_name,
                    "bbox": [int(x1), int(y1), int(x2), int(y2)]
                }
                
                detected_plates.append(detection)
                
    return frame, detected_plates

def process_android_camera(ip_address: str, port: int, save_output: bool = False) -> None:
    """
    Process video stream from Android camera app.
    
    Args:
        ip_address: IP address of Android device
        port: Port number used by the app
        save_output: Whether to save the output video
    """
    # Load model and initialize OCR
    model = load_model()
    reader = easyocr.Reader(['en'])
    
    # Create URL for the video stream
    stream_url = f"http://{ip_address}:{port}/video"
    print(f"Connecting to: {stream_url}")
    
    # Connect to video stream
    cap = cv2.VideoCapture(stream_url)
    
    if not cap.isOpened():
        print("Error: Could not connect to camera stream. Check IP address and port.")
        return
        
    print("Connected to camera stream. Press 'q' to quit.")
    
    process_video_stream(cap, model, reader, save_output)

def process_usb_camera(camera_id: int = 0, save_output: bool = False) -> None:
    """
    Process video from a USB camera connected to the device.
    
    Args:
        camera_id: Camera device ID (usually 0 for the first camera)
        save_output: Whether to save the output video
    """
    # Load model and initialize OCR
    model = load_model()
    reader = easyocr.Reader(['en'])
    
    print(f"Connecting to USB camera (device ID: {camera_id})...")
    
    # Connect to camera
    cap = cv2.VideoCapture(camera_id)
    
    # Try to set higher resolution if supported
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    if not cap.isOpened():
        print(f"Error: Could not open USB camera with ID {camera_id}")
        return
        
    print(f"Connected to USB camera. Camera resolution: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
    print("Press 'q' to quit.")
    
    process_video_stream(cap, model, reader, save_output)

def process_csi_camera(camera_id: int = 0, width: int = 1280, height: int = 720, save_output: bool = False) -> None:
    """
    Process video from a CSI camera connected to Jetson or Raspberry Pi.
    
    Args:
        camera_id: Camera device ID 
        width: Camera resolution width
        height: Camera resolution height
        save_output: Whether to save the output video
    """
    # Load model and initialize OCR
    model = load_model()
    reader = easyocr.Reader(['en'])
    
    print(f"Connecting to CSI camera...")
    
    # For Jetson Nano CSI camera
    if os.path.exists("/dev/video0"):
        # Jetson Nano gstreamer pipeline
        gstreamer_pipeline = (
            f"nvarguscamerasrc sensor-id={camera_id} ! "
            f"video/x-raw(memory:NVMM), width={width}, height={height}, format=NV12, framerate=30/1 ! "
            f"nvvidconv flip-method=0 ! video/x-raw, format=BGRx ! "
            f"videoconvert ! video/x-raw, format=BGR ! appsink"
        )
        cap = cv2.VideoCapture(gstreamer_pipeline, cv2.CAP_GSTREAMER)
    else:
        # Fallback for Raspberry Pi
        print("Using legacy CSI camera interface (for Raspberry Pi)")
        cap = cv2.VideoCapture(camera_id)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    
    if not cap.isOpened():
        print("Error: Could not open CSI camera")
        return
        
    print(f"Connected to CSI camera. Press 'q' to quit.")
    
    process_video_stream(cap, model, reader, save_output)

def process_video_stream(cap: cv2.VideoCapture, model: YOLO, reader: easyocr.Reader, save_output: bool = False) -> None:
    """
    Process video stream from any camera source.
    
    Args:
        cap: OpenCV VideoCapture object
        model: YOLO model for detection
        reader: EasyOCR reader for text recognition
        save_output: Whether to save the output video
    """
    # Create data directory if it doesn't exist
    data_dir = os.path.join(os.getcwd(), "data", "license_plates")
    os.makedirs(data_dir, exist_ok=True)
    
    # Create session file for storing all detections
    session_timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    session_file = os.path.join(data_dir, f"lpr_session_{session_timestamp}.json")
    
    # Initialize empty list to store all detections
    all_detections = []
    
    # Initialize dictionary to track unique plates
    plate_database = {
        "session_start": session_timestamp,
        "detections": []
    }
    
    # Initialize video writer if save_output is True
    output_writer = None
    if save_output:
        os.makedirs("output_videos", exist_ok=True)
        timestamp = int(time.time())
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        output_path = f"output_videos/live_detection_{timestamp}.avi"
        output_writer = cv2.VideoWriter(output_path, fourcc, 20.0, (frame_width, frame_height))
        print(f"Saving output to: {output_path}")
    
    # Set for tracking unique plates (to avoid duplicates)
    detected_plates_set = set()
    recent_detections = {}  # plate_text -> last detection time
    cooldown_period = 3.0  # seconds before re-recording the same plate
    
    last_detection_time = time.time()
    detection_interval = 1.0  # Time in seconds between detection runs
    fps_counter = 0
    fps_timer = time.time()
    fps = 0
    save_interval = 10.0  # Save to file every 10 seconds
    last_save_time = time.time()
    
    print(f"License plate data will be saved to: {session_file}")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to receive frame. Stream may have ended.")
            break
            
        current_time = time.time()
        
        # Calculate FPS
        fps_counter += 1
        if current_time - fps_timer >= 1.0:
            fps = fps_counter
            fps_counter = 0
            fps_timer = current_time
            
        time_diff = current_time - last_detection_time
        
        # Display the frame with stats
        display_frame = frame.copy()
        
        # Add FPS and detection count info
        cv2.putText(display_frame, f"FPS: {fps}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.putText(display_frame, f"Unique Plates: {len(detected_plates_set)}", 
                    (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Run detection at specified intervals to improve performance
        if time_diff >= detection_interval:
            processed_frame, plate_detections = detect_and_recognize_plate(frame, model, reader)
            display_frame = processed_frame
            
            # Process and store new detections
            for detection in plate_detections:
                plate_text = detection["plate_text"]
                
                # Check if we've recently seen this plate (cooldown period)
                if plate_text in recent_detections:
                    time_since_last = current_time - recent_detections[plate_text]
                    if time_since_last < cooldown_period:
                        continue  # Skip this detection during cooldown
                
                # Update last seen time
                recent_detections[plate_text] = current_time
                
                # Add to unique set if new
                if plate_text not in detected_plates_set:
                    detected_plates_set.add(plate_text)
                    print(f"New plate detected: {plate_text} | Confidence: {detection['ocr_confidence']:.2f} | Time: {detection['timestamp']}")
                
                # Add to our detection database
                plate_database["detections"].append(detection)
                
            last_detection_time = current_time
            
        # Periodically save detections to file
        if current_time - last_save_time >= save_interval and plate_database["detections"]:
            with open(session_file, 'w') as f:
                json.dump(plate_database, f, indent=2)
            last_save_time = current_time
            
        # Show the frame
        cv2.imshow("License Plate Detection", display_frame)
        
        # Save frame if output writer is initialized
        if output_writer is not None:
            output_writer.write(display_frame)
        
        # Break the loop on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Save final results before exiting
    if plate_database["detections"]:
        with open(session_file, 'w') as f:
            json.dump(plate_database, f, indent=2)
        print(f"Saved {len(plate_database['detections'])} license plate detections to {session_file}")
    
    # Release resources
    cap.release()
    if output_writer is not None:
        output_writer.release()
    cv2.destroyAllWindows()
    
    # Print summary
    print(f"\nDetection Summary:")
    print(f"Total unique plates detected: {len(detected_plates_set)}")
    if detected_plates_set:
        print("Detected plates:")
        for i, plate in enumerate(detected_plates_set, 1):
            print(f"{i}. {plate}")

def main() -> None:
    """Main function to parse arguments and run the program."""
    parser = argparse.ArgumentParser(description="License Plate Detection from Camera Stream")
    
    # Create a subparser for different camera types
    subparsers = parser.add_subparsers(dest="camera_type", help="Type of camera to use")
    
    # IP Camera (Android) parser
    ip_parser = subparsers.add_parser("ip", help="Use IP camera (Android)")
    ip_parser.add_argument("--ip", required=True, help="IP address of the Android device")
    ip_parser.add_argument("--port", type=int, default=8080, help="Port number (default: 8080)")
    
    # USB Camera parser
    usb_parser = subparsers.add_parser("usb", help="Use USB camera")
    usb_parser.add_argument("--id", type=int, default=0, 
        help="Camera device ID (default: 0)")
    
    # CSI Camera parser (for Jetson Nano / Raspberry Pi)
    csi_parser = subparsers.add_parser("csi", help="Use CSI camera (for Jetson Nano / Raspberry Pi)")
    csi_parser.add_argument("--id", type=int, default=0, 
        help="Camera sensor ID (default: 0)")
    csi_parser.add_argument("--width", type=int, default=1280, 
        help="Camera resolution width (default: 1280)")
    csi_parser.add_argument("--height", type=int, default=720, 
        help="Camera resolution height (default: 720)")
    
    # Common arguments
    parser.add_argument("--save", action="store_true", help="Save the output video")
    
    args = parser.parse_args()
    
    # Handle different camera types
    if args.camera_type == "ip":
        process_android_camera(args.ip, args.port, args.save)
    elif args.camera_type == "usb":
        process_usb_camera(args.id, args.save)
    elif args.camera_type == "csi":
        process_csi_camera(args.id, args.width, args.height, args.save)
    else:
        # Default to USB camera if no arguments provided
        print("No camera type specified, defaulting to USB camera (ID: 0)")
        process_usb_camera(0, args.save)

if __name__ == "__main__":
    main()