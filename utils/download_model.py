from ultralytics import YOLO

# Load a YOLO model trained specifically for license plates
model = YOLO("license_plate_detector.pt")
model.fuse()  # Optimize model for inference
print("Model downloaded and ready!")
