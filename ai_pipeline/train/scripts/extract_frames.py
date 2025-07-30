#!/usr/bin/env python
"""
Script to extract frames from a video file at a specified frame rate.
"""
import cv2
import os
    import sys

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
    if len(sys.argv) < 3:
        print("Usage: python train/scripts/extract_frames.py <video_path> <output_dir> [fps]")
        print("Example: python train/scripts/extract_frames.py train/videos/sample.mp4 train/dataset/images/train 5")
        sys.exit(1)
    
    video_path = sys.argv[1]
    output_dir = sys.argv[2]
    fps = 5 if len(sys.argv) < 4 else float(sys.argv[3])
    
    extract_frames(video_path, output_dir, fps)

