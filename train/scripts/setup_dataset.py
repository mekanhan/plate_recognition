#!/usr/bin/env python
"""
Script to set up the directory structure for YOLO training dataset
"""
import os
import shutil
    import sys

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
# Get the train directory (parent of scripts directory)
train_dir = os.path.dirname(script_dir)

# Change to the train directory
os.chdir(train_dir)
print(f"Working in directory: {os.getcwd()}")

# Create the necessary directories
directories = [
    "dataset/images/train",
    "dataset/images/val",
    "dataset/labels/train",
    "dataset/labels/val",
    "videos",
    "models/pretrained",
    "models/trained"
]

for directory in directories:
    os.makedirs(directory, exist_ok=True)
    print(f"Created directory: {directory}")

# Create the data.yaml file
data_yaml_content = """train: dataset/images/train
val: dataset/images/val

nc: 1  # number of classes
names: ['license_plate']  # update class names as needed
"""

with open("dataset/data.yaml", "w") as f:
    f.write(data_yaml_content)
    print("Created dataset/data.yaml")

# Create the extract_frames.py file in scripts folder
os.makedirs("scripts", exist_ok=True)
extract_frames_content = """#!/usr/bin/env python
"""
Script to extract frames from a video file at a specified frame rate.
"""
import cv2
import os

def extract_frames(video_path, output_dir, fps=5):
    cap = cv2.VideoCapture(video_path)
    os.makedirs(output_dir, exist_ok=True)
    frame_rate = int(cap.get(cv2.CAP_PROP_FPS))
    count = 0
    index = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if count % int(frame_rate / fps) == 0:
            filename = os.path.join(output_dir, f"frame_{index:04d}.jpg")
            cv2.imwrite(filename, frame)
            index += 1
        count += 1

    cap.release()
    print(f"Extracted {index} frames.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python scripts/extract_frames.py <video_path> <output_dir> [fps]")
        sys.exit(1)

    video_path = sys.argv[1]
    output_dir = sys.argv[2]
    fps = 5 if len(sys.argv) < 4 else float(sys.argv[3])

    extract_frames(video_path, output_dir, fps)
"""
with open("scripts/extract_frames.py", "w") as f:
    f.write(extract_frames_content)
    print("Created/Updated scripts/extract_frames.py")
# Make the script executable
try:
    os.chmod("scripts/extract_frames.py", 0o755)
    print("Made scripts/extract_frames.py executable")
except:
    print("Note: Could not make scripts/extract_frames.py executable. You may need to do this manually.")

# Remove extract_frames.py from root if it exists
if os.path.exists("extract_frames.py"):
    os.remove("extract_frames.py")
    print("Removed extract_frames.py from root directory")

# Create a basic train_yolo.sh script
train_yolo_content = """#!/bin/bash
# Script to train YOLOv8 model

# Make sure you run this script from the train directory
# Usage: bash train_yolo.sh

# Check if we're in the train directory
if [ ! -d "dataset" ] || [ ! -f "dataset/data.yaml" ]; then
    echo "Error: This script must be run from the train directory"
    echo "Please run: cd train && bash train_yolo.sh"
    exit 1
fi

# Create models directories if they don't exist
mkdir -p models/pretrained models/trained

# Check if pre-trained model exists, download if not
if [ ! -f "models/pretrained/yolov8n.pt" ]; then
    echo "Downloading pre-trained YOLOv8n model..."
pip install ultralytics
    python -c "from ultralytics import YOLO; YOLO('yolov8n.pt').predict(source='https://ultralytics.com/images/bus.jpg')" > /dev/null
    cp ~/.cache/torch/hub/ultralytics_yolov8_master/yolov8n.pt models/pretrained/ 2>/dev/null || \\
    cp $(python -c "import os; from pathlib import Path; print(Path(os.path.expanduser('~/.cache/torch/hub')).glob('**/yolov8n.pt').__next__())") models/pretrained/ 2>/dev/null || \\
    echo "Could not automatically copy the model. Please manually download yolov8n.pt and place it in train/models/pretrained/"
fi

# Make sure ultralytics is installed
pip install ultralytics

# Train the model
echo "Starting YOLOv8 training..."
yolo task=detect mode=train model=models/pretrained/yolov8n.pt data=dataset/data.yaml epochs=50 imgsz=640 project=models/trained name=license_plate_detector

echo "Training complete! Model saved to models/trained/license_plate_detector/weights/best.pt"
echo "To use the model in your application, copy it to your app/models directory."
"""

with open("train_yolo.sh", "w") as f:
    f.write(train_yolo_content)
    print("Created train_yolo.sh")

# Make the script executable
try:
    os.chmod("train_yolo.sh", 0o755)
    print("Made train_yolo.sh executable")
except:
    print("Note: Could not make train_yolo.sh executable. You may need to do this manually.")

print("\nSetup complete! Your YOLO training dataset structure is ready.")
print("\nNext steps:")
print("1. Add video files to the 'videos/' directory")
print("2. Extract frames using: python ../scripts/extract_frames.py videos/your_video.mp4 dataset/images/train")
print("3. Annotate the extracted frames (using LabelImg, Roboflow, or CVAT)")
print("4. Split your annotated images between train and val directories")
print("5. Run training with: bash train_yolo.sh")
print("\nAfter training, your model will be saved to: models/trained/license_plate_detector/weights/best.pt")
print("You can copy it to your application with: cp models/trained/license_plate_detector/weights/best.pt ../../app/models/")
