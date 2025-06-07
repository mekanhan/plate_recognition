
# YOLO Training Guide (Images & Videos)

This guide explains how to train a YOLOv8 model using both **images** and **videos**. It includes everything from dataset preparation to model training and integration into your framework.

---

## 📁 Project Structure

```
project-root/
├── train/
│   ├── dataset/
│   │   ├── images/
│   │   │   ├── train/
│   │   │   ├── val/
│   │   ├── labels/
│   │   │   ├── train/
│   │   │   ├── val/
│   │   └── data.yaml
│   ├── videos/
│   │   └── sample_video.mp4
│   ├── scripts/
│   │   ├── extract_frames.py
│   │   ├── setup_dataset.py
│   ├── scripts/
│   ├── models/
│   │   ├── pretrained/
│   │   └── trained/
│   ├── train_yolo.sh
│   └── README.md
```

---

## ✅ Step-by-Step: Training YOLO with a Video

### 1. 📹 Extract Frames from Video

Install FFmpeg if not already installed:
```bash
sudo apt install ffmpeg   # or use Homebrew on macOS
```

Then run:
```bash
mkdir -p dataset/images/train
ffmpeg -i videos/sample_video.mp4 -vf fps=5 dataset/images/train/frame_%04d.jpg
```

> ⚠️ This extracts 5 frames per second. Adjust `fps=5` as needed.

---

### 2. ✏️ Annotate Images

Use annotation tools like:
- [LabelImg](https://github.com/tzutalin/labelImg)
- [Roboflow](https://roboflow.com/)
- [CVAT](https://github.com/opencv/cvat)

Annotations must be saved in **YOLO format** (`.txt` files with same name as image), like:

```
0 0.5 0.5 0.3 0.2
```

Format:
```
<class_id> <x_center> <y_center> <width> <height>  # all values normalized between 0 and 1
```

---

### 3. 📦 Organize Dataset

- Place images in:
  - `dataset/images/train/` for training
  - `dataset/images/val/` for validation (optional, but recommended)

- Place label `.txt` files in:
  - `dataset/labels/train/`
  - `dataset/labels/val/`

> ❓ **What's `val`?**  
> It's short for **validation** — a smaller set of images used during training to evaluate how well your model generalizes.

---

### 4. 📝 Create `data.yaml`

```yaml
train: dataset/images/train
val: dataset/images/val

nc: 1
names: ['license_plate']
```

---

### 5. 🚀 Train the YOLOv8 Model

Make sure `ultralytics` is installed:

```bash
pip install ultralytics
```

Then run:

```bash
yolo task=detect mode=train model=yolov8n.pt data=dataset/data.yaml epochs=50 imgsz=640
```

- `model=yolov8n.pt`: use pre-trained nano model
- `epochs=50`: train for 50 epochs
- `imgsz=640`: input image size

---

### 6. 💾 Export & Use Trained Model

After training completes, your model is saved here:

```
runs/detect/train/weights/best.pt
```

To use it in Python:

```python
from ultralytics import YOLO

model = YOLO("runs/detect/train/weights/best.pt")
results = model("test.jpg")
results.show()
```

---

### 📌 Tips

- Use different lighting/video angles to improve robustness.
- Split 80% images to `train/`, 20% to `val/`.
- Backup labels regularly.

---

## 🧰 Scripts You Might Add

### `extract_frames.py`
```python
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

# Example
# extract_frames("videos/sample_video.mp4", "dataset/images/train", fps=5)
```

---

## ✅ You're all set!

Once trained, integrate your model into your current framework by loading `best.pt` and running inference as usual.

