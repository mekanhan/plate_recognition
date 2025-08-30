# AI Models Setup Guide

## Overview

This LPR system uses YOLO models for license plate detection. Models are **not stored in git** to keep the repository lightweight and secure.

## Quick Setup

```bash
# Download all required models
python3 scripts/download_models.py

# Or download specific models
python3 scripts/download_models.py --model yolov8m.pt

# List available models
python3 scripts/download_models.py --list

# Force re-download existing models
python3 scripts/download_models.py --force
```

## Required Models

### Primary Detection Models
- **`yolo11m_best.pt`** - Main license plate detection model (trained)
- **`yolov8m.pt`** - Backup general object detection model

### Development/Testing Models
- **`yolov8n.pt`** - Lightweight model for testing
- **`yolo11m.pt`** - Base YOLO11 model for training
- **`yolo11n.pt`** - Lightweight YOLO11 for edge devices

## Model Storage Structure

```
ai_pipeline/train/models/pretrained/
├── yolo11m_best.pt      # Primary LPR model
├── yolo11m.pt           # Base YOLO11 
├── yolo11n.pt           # Lightweight YOLO11
├── yolov8m.pt           # YOLOv8 medium
└── yolov8n.pt           # YOLOv8 nano

# AI Pipeline models directory
ai_pipeline/models/
├── yolov8m.pt           # Main detection model
└── yolov8n.pt           # Lightweight testing model
```

## Model Usage in Code

```python
from ultralytics import YOLO

# Load the primary LPR model
model = YOLO("ai_pipeline/train/models/pretrained/yolo11m_best.pt")

# Or load fallback model
model = YOLO("ai_pipeline/models/yolov8m.pt")
```

## Security Notes

🔒 **Models are excluded from git for security and performance:**
- Prevents large files in repository
- Avoids potential model licensing issues  
- Keeps repository clone times fast
- Allows model updates without git bloat

## Troubleshooting

### Download Issues
```bash
# Check internet connection
curl -I https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8m.pt

# Download manually if script fails
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8m.pt
```

### Missing Models Error
If you see import errors about missing models:

1. **Run the download script:**
   ```bash
   python3 scripts/download_models.py
   ```

2. **Check model paths in code:**
   - Ensure paths match the downloaded file locations
   - Verify model files have `.pt` extension

3. **Verify downloads:**
   ```bash
   ls -la ai_pipeline/train/models/pretrained/
   ls -la ai_pipeline/models/
   ```

## Custom Models

To use your own trained models:

1. **Place model in appropriate directory**
2. **Update model path in configuration**
3. **Add to download script if sharing with team**

## Performance Notes

- **yolo11m_best.pt**: Best accuracy for license plates
- **yolov8m.pt**: Good balance of speed and accuracy  
- **yolo11n.pt**: Fastest, suitable for edge devices
- **GPU**: All models support CUDA acceleration when available

## Training Your Own Models

See `ai_pipeline/train/README.md` for training instructions.