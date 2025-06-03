# License Plate Recognition Framework Guide

## Table of Contents
- Environment Setup
- Project Structure
- Configuration Files
- Running the Application
- Working with the Framework
- Advanced Usage
- Troubleshooting
- Maintenance

---

## Environment Setup

### Create and Activate Virtual Environment

```bash
# Create a new virtual environment
python -m venv venv

# Activate the environment

# On Windows (Command Prompt)
venv\Scripts\activate

# On Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# On Linux/macOS
source venv/bin/activate

# You should now see (venv) at the beginning of your command prompt
```

### Install Dependencies

```bash
# Install from the optimized requirements file
pip install -r requirements.txt

# If you want to install packages individually (for troubleshooting)
pip install fastapi uvicorn[standard] python-multipart jinja2 pydantic pydantic-settings
pip install opencv-python easyocr torch torchvision ultralytics
pip install numpy scikit-image matplotlib pandas pillow scipy
```

### Verify Installation

```bash
# Check installed packages
pip list

# Verify Python version (should be 3.7+)
python --version
```

---

## Project Structure

Ensure your project structure looks like this:

```
license_plate_recognition/
│
├── app/
│   ├── __init__.py
│   ├── main.py                   # FastAPI main application
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── stream.py             # Video streaming endpoints
│   │   ├── detection.py          # LPR detection endpoints
│   │   └── results.py            # Results and reporting endpoints
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── camera_service.py     # Camera management
│   │   ├── detection_service.py  # LPR detection wrapper
│   │   ├── enhancer_service.py   # Real-time enhancement
│   │   └── storage_service.py    # Data storage management
│   │
│   └── utils/
│       ├── __init__.py
│       └── config.py             # Configuration management
│
├── data/
│   ├── license_plates/           # Raw detection output
│   ├── enhanced_plates/          # Enhanced results
│   └── known_plates.json         # Database of known plates
│
├── models/
│   └── yolo11m_best.pt           # YOLO model file
│
├── static/
│   └── js/
│       └── stream.js             # JavaScript for video streaming
│
├── templates/
│   ├── index.html                # Main dashboard
│   └── stream.html               # Streaming page
│
├── scripts/
│   ├── lpr_live.py               # Standalone script (can keep for direct use)
│   └── enhance_plates.py         # Post-processing script
│
├── tests/                        # Test files (optional)
│
├── requirements.txt              # Package dependencies
├── .env                          # Environment variables (create this)
└── README.md                     # Documentation
```

### Create any missing directories

```bash
# Create necessary directories
mkdir -p app/routers app/services app/utils
mkdir -p data/license_plates data/enhanced_plates
mkdir -p static/js templates models scripts tests
```

---

## Configuration Files

### Create `.env` File

```bash
# Create a .env file with configuration settings
cat > .env << EOF
# Camera settings
CAMERA_ID=0
CAMERA_WIDTH=1280
CAMERA_HEIGHT=720

# Model settings
MODEL_PATH=models/yolo11m_best.pt

# Directory settings
LICENSE_PLATES_DIR=data/license_plates
ENHANCED_PLATES_DIR=data/enhanced_plates
KNOWN_PLATES_PATH=data/known_plates.json
EOF
```

### Create `known_plates.json`

```bash
# Create initial known plates database
cat > data/known_plates.json << EOF
{
  "plates": [
    {
      "plate_number": "VBR7660",
      "first_seen": "$(date +%Y-%m-%d)",
      "metadata": {}
    }
  ],
  "last_updated": "$(date +%Y-%m-%d)"
}
EOF
```

---

## Running the Application

### Start the FastAPI Server

```bash
# Method 1: Using uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Method 2: If uvicorn is not in PATH
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Method 3: Create a run.py file for easier execution
cat > run.py << EOF
import uvicorn

if __name__ == "__main__":
  uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
EOF

python run.py
```

### Access the Application

- Main dashboard: <http://localhost:8000/>
- API documentation: <http://localhost:8000/docs>
- Live video stream: <http://localhost:8000/stream/>
- Latest detection results: <http://localhost:8000/results/latest>

---

## Working with the Framework

### Deactivating the Virtual Environment

```bash
# Deactivate the virtual environment
deactivate
```

### Updating Dependencies

```bash
# Activate the environment first
source venv/bin/activate  # or equivalent for your OS

# Install new package
pip install new_package_name

# Update requirements.txt
pip freeze > requirements.txt
```

### Removing the Virtual Environment

```bash
# Deactivate first if it's active
deactivate

# Remove the virtual environment
# On Windows
rmdir /s /q venv

# On Linux/macOS
rm -rf venv
```

---

## Advanced Usage

### Running with Different Camera Sources

```bash
# Use USB camera with ID 1
CAMERA_ID=1 uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Use IP camera
# Edit camera_service.py to support IP cameras
```

### Using the Standalone Script

```bash
# USB camera
python scripts/lpr_live.py usb --id 0 --save

# IP camera (like Android phone)
python scripts/lpr_live.py ip --ip 192.168.1.100 --port 8080
```

### Post-Processing Existing Files

```bash
python scripts/enhance_plates.py file --file data/license_plates/lpr_session_YYYYMMDD_HHMMSS.json
```

---

## Troubleshooting

### Camera Issues

```bash
# Check available cameras
python -c "import cv2; print([i for i in range(10) if cv2.VideoCapture(i).isOpened()])"
```

### Model Issues

```bash
# Verify model file exists
ls -la models/

# Download the model if missing (for YOLOv8)
python -c "from ultralytics import YOLO; YOLO('yolov8m.pt').save('models/yolo11m_best.pt')"
```

### Permission Issues

```bash
# On Linux, you might need camera permissions:
# Add user to video group
sudo usermod -a -G video $USER

# Log out and back in for changes to take effect
```

---

## Maintenance

### Backing Up Data

```bash
# Back up known plates database
cp data/known_plates.json data/known_plates_backup_$(date +%Y%m%d).json

# Back up all detection data
zip -r data_backup_$(date +%Y%m%d).zip data/
```

### Updating the Model

```bash
# Activate environment
source venv/bin/activate

# Download new model (example)
python -c "from ultralytics import YOLO; YOLO('yolov8l.pt').save('models/yolo11m_best_new.pt')"

# Update .env to point to the new model
sed -i 's/MODEL_PATH=.*/MODEL_PATH=models\/yolo11m_best_new.pt/' .env
```

---

## Dependencies

### Core Web Framework

```text
fastapi>=0.95.0            # Primary web framework
uvicorn[standard]>=0.22.0  # ASGI server
python-multipart>=0.0.6    # For handling multipart form data
pydantic>=2.0.0            # Data validation
pydantic-settings>=2.0.0   # Settings management
Jinja2>=3.1.2              # Template engine
MarkupSafe>=2.1.3          # Required by Jinja2
python-dotenv>=1.0.0       # Environment variable loading
```

### Computer Vision & License Plate Recognition

```text
opencv-python>=4.8.0.74          # Computer vision library
easyocr>=1.7.0                   # OCR for license plates
torch>=2.0.1,<2.6.0              # Deep learning framework
torchvision>=0.15.2,<0.21.0      # Computer vision extensions for PyTorch
ultralytics>=8.0.0,<8.4.0        # YOLO implementation
numpy>=1.25.2,<2.0.0             # Numerical computing
```

### Image Processing & Data Science

```text
scikit-image>=0.21.0      # Image processing algorithms
matplotlib>=3.7.2         # Visualization
pandas>=2.0.3,<2.2.0      # Data manipulation
pillow>=10.0.0,<11.0.0    # Image processing library
scipy>=1.11.1             # Scientific computing
```

### Machine Learning Support

```text
scikit-learn>=1.3.0        # Machine learning algorithms
networkx>=3.1              # Network analysis
onnx>=1.14.0               # Model exchange format
onnxruntime>=1.15.1        # Runtime for ONNX models
```

### Utilities & Helpers

```text
tqdm>=4.65.0               # Progress bars
requests>=2.31.0           # HTTP requests
PyYAML>=6.0.1              # YAML parsing
coloredlogs>=15.0.1        # Better log formatting
psutil>=5.9.5              # System monitoring
joblib>=1.3.1              # Parallelization
```

### Testing & Development

```text
pytest>=7.4.0              # Testing framework
pytest-mock>=3.11.1        # Mocking for tests
iniconfig>=2.0.0           # Configuration for pytest
pluggy>=1.2.0              # Plugin system for pytest
```
