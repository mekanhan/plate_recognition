import cv2
import easyocr
from ultralytics import YOLO

# Load YOLOv8 model
model = YOLO("yolov8n.pt")
reader = easyocr.Reader(['en'])

# Load video
video_path = "input_videos/2.MOV"
cap = cv2.VideoCapture(video_path)
frame_width = int(cap.get(3))
frame_height = int(cap.get(4))

# Output video
out = cv2.VideoWriter("output_videos/result.mp4", cv2.VideoWriter_fourcc(*'MP4V'), 30, (frame_width, frame_height))

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame)[0]  # Run YOLOv8 detection
    
    for result in results.boxes:
        x1, y1, x2, y2 = map(int, result.xyxy[0])
        cropped_plate = frame[y1:y2, x1:x2]

        # Convert to grayscale
        gray_plate = cv2.cvtColor(cropped_plate, cv2.COLOR_BGR2GRAY)

        # Recognize text with EasyOCR
        text_results = reader.readtext(gray_plate)
        plate_text = "".join([res[1] for res in text_results])

        # Draw bounding box and text
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, plate_text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        print(f"Detected Plate: {plate_text}")

    # Write to output
    out.write(frame)

    # Display (optional)
    cv2.imshow("License Plate Recognition", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
out.release()
cv2.destroyAllWindows()
