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
import difflib
from collections import Counter, defaultdict
from ultralytics import YOLO
import argparse
from typing import Optional, Tuple, List, Dict, Any, Set
from app.utils.plate_database import PlateDatabase

class LicensePlateValidator:
    """
    Validates and improves license plate detection accuracy
    using multiple techniques and a known plates database.
    """
    
    def __init__(self, known_plates=None):
        """Initialize with optional known plates database"""
        self.known_plates = known_plates or []
        # Common OCR substitution patterns
        self.substitutions = {
            '0': 'O', 'O': '0',
            '1': 'I', 'I': '1', 
            '8': 'B', 'B': '8',
            '5': 'S', 'S': '5',
            '2': 'Z', 'Z': '2',
            'D': '0', 'Q': '0',
            'U': 'V', 'V': 'U'
        }
        
    def add_known_plate(self, plate: str) -> None:
        """Add a known plate to the local DB"""
        if plate not in self.known_plates:
            self.known_plates.append(plate)
            
    def get_plate_variations(self, plate_text: str) -> List[str]:
        """Generate possible variations of a plate based on common OCR errors"""
        plate = plate_text.upper().strip()
        variations = [plate]
        
        # Generate variations with single character substitutions
        for i, char in enumerate(plate):
            if char in self.substitutions:
                new_plate = plate[:i] + self.substitutions[char] + plate[i+1:]
                variations.append(new_plate)
        
        return variations
    
    def calculate_similarity(self, plate1: str, plate2: str) -> float:
        """Calculate string similarity between two plate texts"""
        return difflib.SequenceMatcher(None, plate1, plate2).ratio()
    
    def match_with_known_plates(self, plate_text: str, threshold: float = 0.8) -> Tuple[Optional[str], float]:
        """Check if plate is similar to any known plate"""
        if not self.known_plates:
            return None, 0
            
        best_match = None
        best_score = 0
        
        # Check each variation of the input plate
        for variation in self.get_plate_variations(plate_text):
            for known_plate in self.known_plates:
                similarity = self.calculate_similarity(variation, known_plate)
                if similarity > best_score:
                    best_score = similarity
                    best_match = known_plate
        
        if best_score >= threshold:
            return best_match, best_score
        return None, best_score
    
    def enhance_detections(self, detections: List[Dict[str, Any]], min_confidence: float = 0.3) -> Dict[str, Any]:
        """
        Process multiple detections and determine the most likely plate
        with confidence levels
        """
        if not detections:
            return None
            
        # First pass: weight by confidence and find consensus
        valid_detections = [d for d in detections if d["ocr_confidence"] >= min_confidence]
        
        if not valid_detections:
            valid_detections = detections  # Fall back to all detections
            
        # Create weighted votes based on OCR confidence
        votes = Counter()
        for detection in valid_detections:
            weight = max(1, int(detection["ocr_confidence"] * 10))
            plate_text = detection["plate_text"].upper().strip()
            
            # Add votes for this plate and its variations
            for variation in self.get_plate_variations(plate_text):
                votes[variation] += weight
        
        # Get top candidates
        top_candidates = votes.most_common(3)
        
        # Second pass: check against known plates
        for candidate, vote_count in top_candidates:
            known_match, match_score = self.match_with_known_plates(candidate)
            if known_match and match_score >= 0.8:
                # We found a strong match with a known plate
                consensus_confidence = match_score
                return {
                    "plate_text": known_match,
                    "confidence": consensus_confidence,
                    "confidence_category": self._get_confidence_category(consensus_confidence),
                    "match_type": "known_plate",
                    "original_detections": detections
                }
        
        # If no known match, use the consensus from votes
        if top_candidates:
            best_plate = top_candidates[0][0]
            vote_confidence = top_candidates[0][1] / sum(votes.values())
            
            return {
                "plate_text": best_plate,
                "confidence": vote_confidence,
                "confidence_category": self._get_confidence_category(vote_confidence),
                "match_type": "consensus",
                "original_detections": detections
            }
            
        # Fallback to the highest confidence detection
        best_detection = max(detections, key=lambda x: x["ocr_confidence"])
        return {
            "plate_text": best_detection["plate_text"],
            "confidence": best_detection["ocr_confidence"],
            "confidence_category": self._get_confidence_category(best_detection["ocr_confidence"]),
            "match_type": "single_best",
            "original_detections": detections
        }
    
    def _get_confidence_category(self, confidence: float) -> str:
        """Categorize confidence scores"""
        if confidence >= 0.7:
            return "HIGH"
        elif confidence >= 0.4:
            return "MEDIUM"
        else:
            return "LOW"


def load_model() -> YOLO:
    """
    Load YOLO model from models/ folder and auto-detect GPU availability.
    
    Returns:
        YOLO: Loaded model on the appropriate device
    """
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}")
    return YOLO("app/models/yolo11m_best.pt").to(device)

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

def detect_and_recognize_plate(frame: np.ndarray, model: YOLO, reader: easyocr.Reader, 
                              plate_tracker: 'PlateTracker') -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    """
    Detect license plates and extract text using OCR and YOLO.
    
    Args:
        frame: Current video frame
        model: YOLO model for detection
        reader: EasyOCR reader for text recognition
        plate_tracker: Tracker for enhancing plate detections over time
        
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
                
                # Add to tracking system and get enhanced results
                enhanced_detection = plate_tracker.add_detection(detection)
                
                # Determine display color based on confidence
                if enhanced_detection:
                    if enhanced_detection["confidence_category"] == "HIGH":
                        color = (0, 255, 0)  # Green for high confidence
                    elif enhanced_detection["confidence_category"] == "MEDIUM":
                        color = (0, 165, 255)  # Orange for medium confidence
                    else:
                        color = (0, 0, 255)  # Red for low confidence
                        
                    # Display the enhanced plate text
                    display_text = enhanced_detection["plate_text"]
                    match_type = enhanced_detection.get("match_type", "")
                    confidence = enhanced_detection.get("confidence", 0.0)
                    
                    # Add match type indicator
                    if match_type == "known_plate":
                        display_text += " (KNOWN)"
                    elif match_type == "consensus":
                        display_text += " (CONSENSUS)"
                    
                    # Draw enhanced text on the frame
                    cv2.putText(frame, display_text, (x1, y1 - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                    
                    # Add confidence info
                    conf_text = f"Conf: {confidence:.2f}"
                    cv2.putText(frame, conf_text, (x1, y2 + 20), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                else:
                    # Fallback to raw detection
                    cv2.putText(frame, text_cleaned, (x1, y1 - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                
                detected_plates.append(detection)
                
    return frame, detected_plates

class PlateTracker:
    """
    Tracks license plate detections over time to improve accuracy
    using temporal consensus and validation.
    """
    
    def __init__(self, similarity_threshold: float = 0.7, 
                time_window: float = 10.0,
                enhancement_interval: float = 1.0):
        """
        Initialize the plate tracker.
        
        Args:
            similarity_threshold: Threshold for considering plates similar
            time_window: Time window in seconds to keep detections
            enhancement_interval: Minimum time between enhancements
        """
        self.db = PlateDatabase()
        self.validator = LicensePlateValidator(known_plates=self.db.get_all_plates())
        self.plates_by_group = defaultdict(list)  # Group ID -> list of detections
        self.similarity_threshold = similarity_threshold
        self.time_window = time_window
        self.last_enhancement_time = time.time()
        self.enhancement_interval = enhancement_interval
        self.enhanced_results = {}  # Group ID -> enhanced result
        self.group_counter = 0
        
    def add_detection(self, detection: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Add a new detection and return enhanced result if available.
        
        Args:
            detection: New detection to add
            
        Returns:
            Enhanced detection result or None
        """
        plate_text = detection["plate_text"]
        current_time = time.time()
        
        # Clean up old detections
        self._cleanup_old_detections(current_time)
        
        # Find best matching group
        best_group_id = None
        best_similarity = 0
        
        for group_id, detections in self.plates_by_group.items():
            if not detections:
                continue
                
            # Compare with the first detection in the group
            group_plate = detections[0]["plate_text"]
            similarity = self.validator.calculate_similarity(plate_text, group_plate)
            
            if similarity > best_similarity and similarity >= self.similarity_threshold:
                best_similarity = similarity
                best_group_id = group_id
        
        # If no matching group found, create a new one
        if best_group_id is None:
            best_group_id = f"group_{self.group_counter}"
            self.group_counter += 1
            
        # Add to the group
        self.plates_by_group[best_group_id].append(detection)
        
        # Check if it's time to enhance detections
        if current_time - self.last_enhancement_time >= self.enhancement_interval:
            self._enhance_all_groups()
            self.last_enhancement_time = current_time
            
        # Return the enhanced result for this group if available
        return self.enhanced_results.get(best_group_id)
        
    def _cleanup_old_detections(self, current_time: float) -> None:
        """Remove detections that are older than the time window"""
        for group_id, detections in list(self.plates_by_group.items()):
            # Filter out old detections
            recent_detections = [d for d in detections 
                                if current_time - d["unix_timestamp"] <= self.time_window]
            
            if recent_detections:
                self.plates_by_group[group_id] = recent_detections
            else:
                # Remove empty groups and their enhanced results
                del self.plates_by_group[group_id]
                if group_id in self.enhanced_results:
                    del self.enhanced_results[group_id]
                    
    def _enhance_all_groups(self) -> None:
        """Enhance all detection groups"""
        for group_id, detections in self.plates_by_group.items():
            if not detections:
                continue
                
            # Enhance this group
            enhanced = self.validator.enhance_detections(detections)
            if enhanced:
                self.enhanced_results[group_id] = enhanced
                
                # Auto-add high confidence plates to database
                if enhanced["confidence_category"] == "HIGH":
                    self.db.auto_add_high_confidence_plates(
                        enhanced["plate_text"], 
                        enhanced["confidence"]
                    )
    
    def get_all_enhanced_results(self) -> List[Dict[str, Any]]:
        """Get all current enhanced results"""
        return list(self.enhanced_results.values())

def process_video_stream(cap: cv2.VideoCapture, model: YOLO, reader: easyocr.Reader, save_output: bool = False) -> None:
    """
    Process video stream from any camera source with real-time enhancement.
    
    Args:
        cap: OpenCV VideoCapture object
        model: YOLO model for detection
        reader: EasyOCR reader for text recognition
        save_output: Whether to save the output video
    """
    # Create data directory if it doesn't exist
    data_dir = os.path.join(os.getcwd(), "data", "license_plates")
    os.makedirs(data_dir, exist_ok=True)
    
    # Create enhanced data directory
    enhanced_dir = os.path.join(os.getcwd(), "data", "enhanced_plates")
    os.makedirs(enhanced_dir, exist_ok=True)
    
    # Create session file for storing all detections
    session_timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    session_file = os.path.join(data_dir, f"lpr_session_{session_timestamp}.json")
    enhanced_session_file = os.path.join(enhanced_dir, f"enhanced_session_{session_timestamp}.json")
    
    # Initialize plate tracker for real-time enhancement
    plate_tracker = PlateTracker()
    
    # Initialize dictionary to track unique plates
    plate_database = {
        "session_start": session_timestamp,
        "detections": []
    }
    
    # Initialize enhanced results database
    enhanced_database = {
        "session_start": session_timestamp,
        "enhanced_results": []
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
    cooldown_period = 10.0  # seconds before re-recording the same plate
    
    last_detection_time = time.time()
    detection_interval = 1.0  # Time in seconds between detection runs
    fps_counter = 0
    fps_timer = time.time()
    fps = 0
    save_interval = 10.0  # Save to file every 10 seconds
    last_save_time = time.time()
    
    print(f"License plate data will be saved to: {session_file}")
    print(f"Enhanced results will be saved to: {enhanced_session_file}")
    
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
            processed_frame, plate_detections = detect_and_recognize_plate(frame, model, reader, plate_tracker)
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
            
        # Periodically save detections and enhanced results to file
        if current_time - last_save_time >= save_interval:
            # Save raw detections
            if plate_database["detections"]:
                with open(session_file, 'w') as f:
                    json.dump(plate_database, f, indent=2)
            
            # Save enhanced results
            enhanced_results = plate_tracker.get_all_enhanced_results()
            enhanced_database["enhanced_results"] = enhanced_results
            
            with open(enhanced_session_file, 'w') as f:
                json.dump(enhanced_database, f, indent=2)
                
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
    
    # Save final enhanced results
    enhanced_results = plate_tracker.get_all_enhanced_results()
    enhanced_database["enhanced_results"] = enhanced_results
    
    with open(enhanced_session_file, 'w') as f:
        json.dump(enhanced_database, f, indent=2)
    print(f"Saved {len(enhanced_results)} enhanced results to {enhanced_session_file}")
    
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
    
    # Print enhanced results summary
    if enhanced_results:
        print("\nEnhanced Results Summary:")
        high_conf = [r for r in enhanced_results if r["confidence_category"] == "HIGH"]
        medium_conf = [r for r in enhanced_results if r["confidence_category"] == "MEDIUM"]
        low_conf = [r for r in enhanced_results if r["confidence_category"] == "LOW"]
        
        print(f"High confidence: {len(high_conf)}")
        print(f"Medium confidence: {len(medium_conf)}")
        print(f"Low confidence: {len(low_conf)}")

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