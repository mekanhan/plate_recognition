import urllib.request
model_url = "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11m.pt"
urllib.request.urlretrieve(model_url, "models/yolov11m.pt")