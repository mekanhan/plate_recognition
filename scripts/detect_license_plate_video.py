import cv2
import os
import time
import torch
from ultralytics import YOLO

def load_model():
    """Load YOLO model from models/ folder and auto-detect GPU availability."""
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}")
    return YOLO(os.path.join(root_folder, 'models', 'yolo11m_best.pt')).to(device)

# Get the root folder of the project
root_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Define input and output folders relative to the project root
input_folder = os.path.join(root_folder, 'input_videos')      # Input folder in root
output_folder = os.path.join(root_folder, 'output_videos')    # Output folder in root
os.makedirs(output_folder, exist_ok=True)

# Load YOLO model with automatic device selection
model = load_model()

def detect_license_plate_in_video(video_path):
    """Detect license plates in a video and save the processed output."""
    video_name = os.path.basename(video_path).split('.')[0]  # Get original video name without extension
    output_video_path = os.path.join(output_folder, f"{video_name}_detected.mp4")

    # Open the video file
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Unable to open video file: {video_path}")
        return

    # Get video properties
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))

    # Define the codec and create a VideoWriter object to save the output video
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (frame_width, frame_height))

    # Process each frame
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Run YOLOv8 inference on the frame
        results = model(frame)[0]

        # Loop through the results and draw bounding boxes
        for result in results.boxes:
            x1, y1, x2, y2 = map(int, result.xyxy[0])
            conf = result.conf[0]
            class_id = int(result.cls[0])
            class_name = model.names[class_id]

            # Draw the bounding box and label on the frame
            label = f"{class_name}: {conf:.2f}"
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Show the frame live
        cv2.imshow('License Plate Detection - Press Q to exit', frame)

        # Save the frame to the output video
        out.write(frame)

        # Press 'q' to exit the video window
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release resources
    cap.release()
    out.release()
    cv2.destroyAllWindows()

    print(f"Processed video saved: {output_video_path}")

def process_folder(folder_path):
    """Process all videos in a given folder."""
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
            video_path = os.path.join(folder_path, filename)
            print(f"Processing video: {video_path}")
            detect_license_plate_in_video(video_path)

# Run detection on all videos in the input_videos folder in the project root
process_folder(input_folder)
