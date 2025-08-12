#!/usr/bin/env python3
"""
Test script to verify all dependencies are properly installed
"""
import sys

print("🔍 Testing LPR System Dependencies...\n")

# Test core dependencies
print("Testing core dependencies:")
try:
    import cv2
    print(f"✅ OpenCV imported - Version: {cv2.__version__}")
except ImportError as e:
    print(f"❌ OpenCV import failed: {e}")
    sys.exit(1)

try:
    import torch
    cuda_available = torch.cuda.is_available()
    device = "CUDA" if cuda_available else "CPU"
    print(f"✅ PyTorch imported - Version: {torch.__version__} (Device: {device})")
    if cuda_available:
        print(f"   GPU: {torch.cuda.get_device_name(0)}")
except ImportError as e:
    print(f"❌ PyTorch import failed: {e}")
    sys.exit(1)

try:
    from ultralytics import YOLO
    print("✅ YOLO (Ultralytics) imported")
except ImportError as e:
    print(f"❌ YOLO import failed: {e}")
    sys.exit(1)

try:
    import easyocr
    print("✅ EasyOCR imported")
except ImportError as e:
    print(f"❌ EasyOCR import failed: {e}")
    sys.exit(1)

# Test web framework dependencies
print("\nTesting web framework dependencies:")
try:
    from fastapi import FastAPI
    print("✅ FastAPI imported")
except ImportError as e:
    print(f"❌ FastAPI import failed: {e}")
    sys.exit(1)

try:
    import uvicorn
    print(f"✅ Uvicorn imported - Version: {uvicorn.__version__}")
except ImportError as e:
    print(f"❌ Uvicorn import failed: {e}")
    sys.exit(1)

# Test database dependencies
print("\nTesting database dependencies:")
try:
    from sqlalchemy import create_engine
    import sqlalchemy
    print(f"✅ SQLAlchemy imported - Version: {sqlalchemy.__version__}")
except ImportError as e:
    print(f"❌ SQLAlchemy import failed: {e}")
    sys.exit(1)

try:
    import aiosqlite
    print("✅ aiosqlite imported")
except ImportError as e:
    print(f"❌ aiosqlite import failed: {e}")
    sys.exit(1)

# Test other dependencies
print("\nTesting other dependencies:")
try:
    import numpy as np
    print(f"✅ NumPy imported - Version: {np.__version__}")
except ImportError as e:
    print(f"❌ NumPy import failed: {e}")
    sys.exit(1)

try:
    import yaml
    print("✅ PyYAML imported")
except ImportError as e:
    print(f"❌ PyYAML import failed: {e}")
    sys.exit(1)

try:
    import aiofiles
    print("✅ aiofiles imported")
except ImportError as e:
    print(f"❌ aiofiles import failed: {e}")
    sys.exit(1)

# Add project root to path for local imports
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Test local modules
print("\nTesting local modules:")
try:
    from ai_pipeline.camera_manager import CameraManager, CameraConfig
    print("✅ camera_manager module imported")
except ImportError as e:
    print(f"❌ camera_manager import failed: {e}")

try:
    from ai_pipeline.processors import LicensePlateDetector, ProcessingPipeline
    print("✅ processors module imported")
except ImportError as e:
    print(f"❌ processors import failed: {e}")

try:
    from database.models import Base, Camera, Detection
    print("✅ database models imported")
except ImportError as e:
    print(f"❌ database models import failed: {e}")

try:
    from database.service import DatabaseService
    print("✅ database service imported")
except ImportError as e:
    print(f"❌ database service import failed: {e}")

try:
    from api.main import app
    print("✅ API main module imported")
except ImportError as e:
    print(f"❌ API main import failed: {e}")

print("\n" + "="*50)
print("✅ ALL IMPORTS SUCCESSFUL! System dependencies are ready.")
print("="*50)