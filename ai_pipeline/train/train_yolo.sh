#!/bin/bash
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
    cp ~/.cache/torch/hub/ultralytics_yolov8_master/yolov8n.pt models/pretrained/ 2>/dev/null || \
    cp $(python -c "import os; from pathlib import Path; print(Path(os.path.expanduser('~/.cache/torch/hub')).glob('**/yolov8n.pt').__next__())") models/pretrained/ 2>/dev/null || \
    echo "Could not automatically copy the model. Please manually download yolov8n.pt and place it in train/models/pretrained/"
fi

# Make sure ultralytics is installed
pip install ultralytics

# Train the model
echo "Starting YOLOv8 training..."
yolo task=detect mode=train model=models/pretrained/yolov8n.pt data=dataset/data.yaml epochs=50 imgsz=640 project=models/trained name=license_plate_detector

echo "Training complete! Model saved to models/trained/license_plate_detector/weights/best.pt"
echo "To use the model in your application, copy it to your app/models directory."
