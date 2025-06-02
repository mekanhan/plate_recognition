import urllib.request
model_url = "https://www.google.com/url?sa=t&source=web&rct=j&opi=89978449&url=https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8m.pt&ved=2ahUKEwiIxprj-M-LAxWfKkQIHZTkFywQFnoECBwQAQ&usg=AOvVaw3j49E7_mCX_6iU24ft1v0Z"
urllib.request.urlretrieve(model_url, "models/yolov8m.pt")