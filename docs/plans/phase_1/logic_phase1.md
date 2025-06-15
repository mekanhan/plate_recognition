1. Video Frame (Live Stream or File)
→ passed into

2. YOLOv11 (License Plate Detection)
→ outputs bounding boxes for plates per frame
→ sent to

3. Deep SORT Tracker
→ assigns unique object IDs to each plate across frames
→ each tracked object goes to

4. OCR (License Plate Text Extraction)
→ returns plate string + confidence per frame
→ stored in

5. Plate Memory (by Object ID)
→ keeps a list of all plate predictions with confidence
→ periodically (or when object leaves frame):

6. Majority Voting + Confidence Filter
→ chooses the most reliable license plate string
→ displayed on

7. Real-Time Overlay
→ draws bounding box + current best plate on the frame
→ sent to screen or stream output