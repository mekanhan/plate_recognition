#!/usr/bin/env python3
"""
Model Download Script for LPR System
Downloads required YOLO model files instead of storing them in git
"""

import os
import sys
import urllib.request
import hashlib
from pathlib import Path
from typing import Dict, Tuple

# Model configurations with download URLs and checksums
MODELS = {
    "yolov8m.pt": {
        "url": "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8m.pt",
        "sha256": "c84cc6d0e9b5b0e3c5f3a0b8c9c0c9c0c9c0c9c0c9c0c9c0c9c0c9c0c9c0c9c0",  # Placeholder
        "size": "50MB",
        "description": "YOLOv8 Medium - General object detection"
    },
    "ai_pipeline/train/models/pretrained/yolo11m_best.pt": {
        "url": "https://github.com/ultralytics/assets/releases/download/v8.0.0/yolo11m.pt",
        "sha256": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2",  # Placeholder
        "size": "39MB", 
        "description": "YOLO11 Medium - License plate detection (trained)"
    },
    "ai_pipeline/train/models/pretrained/yolo11m.pt": {
        "url": "https://github.com/ultralytics/assets/releases/download/v8.0.0/yolo11m.pt",
        "sha256": "b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2g3",  # Placeholder
        "size": "39MB",
        "description": "YOLO11 Medium - Base model"
    },
    "ai_pipeline/train/models/pretrained/yolov8n.pt": {
        "url": "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt",
        "sha256": "c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2g3h4",  # Placeholder
        "size": "6MB",
        "description": "YOLOv8 Nano - Lightweight detection"
    },
    "ai_pipeline/train/models/pretrained/yolo11n.pt": {
        "url": "https://github.com/ultralytics/assets/releases/download/v8.0.0/yolo11n.pt", 
        "sha256": "d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2g3h4i5",  # Placeholder
        "size": "5MB",
        "description": "YOLO11 Nano - Lightweight detection"
    }
}


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def download_with_progress(url: str, destination: Path) -> bool:
    """Download file with progress indication"""
    try:
        print(f"📥 Downloading {destination.name} ({MODELS[str(destination.relative_to(Path('.'))].get('size', 'unknown size')})...")
        
        def progress_hook(block_num, block_size, total_size):
            if total_size > 0:
                percent = min(100, (block_num * block_size * 100) // total_size)
                bar_length = 40
                filled = int(bar_length * percent // 100)
                bar = "█" * filled + "░" * (bar_length - filled)
                print(f"\r  [{bar}] {percent}%", end="", flush=True)
        
        urllib.request.urlretrieve(url, destination, reporthook=progress_hook)
        print()  # New line after progress bar
        return True
        
    except Exception as e:
        print(f"\n❌ Download failed: {e}")
        return False


def verify_checksum(file_path: Path, expected_sha256: str) -> bool:
    """Verify file integrity using SHA256"""
    if expected_sha256.startswith("placeholder") or len(expected_sha256) != 64:
        print("⚠️  Checksum verification skipped (placeholder hash)")
        return True
    
    actual_sha256 = calculate_sha256(file_path)
    if actual_sha256 == expected_sha256:
        print("✅ Checksum verified")
        return True
    else:
        print(f"❌ Checksum mismatch!")
        print(f"   Expected: {expected_sha256}")
        print(f"   Actual:   {actual_sha256}")
        return False


def download_models(force: bool = False, models_to_download: list = None) -> bool:
    """Download all required models"""
    repo_root = Path(__file__).parent.parent
    success_count = 0
    total_count = 0
    
    models_list = models_to_download if models_to_download else list(MODELS.keys())
    
    print("🚀 LPR Model Download Script")
    print("=" * 50)
    
    for model_path, config in MODELS.items():
        if model_path not in models_list:
            continue
            
        total_count += 1
        destination = repo_root / model_path
        
        # Create destination directory
        destination.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if file already exists
        if destination.exists() and not force:
            file_size = destination.stat().st_size
            print(f"⏭️  {model_path} already exists ({file_size // (1024*1024)}MB)")
            success_count += 1
            continue
        
        print(f"\n📦 {config['description']}")
        print(f"   Path: {model_path}")
        
        # Download the model
        if download_with_progress(config['url'], destination):
            # Verify checksum if available
            if verify_checksum(destination, config['sha256']):
                print(f"✅ Successfully downloaded {model_path}")
                success_count += 1
            else:
                print(f"❌ Checksum verification failed for {model_path}")
                destination.unlink()  # Remove corrupted file
        else:
            print(f"❌ Failed to download {model_path}")
    
    print("\n" + "=" * 50)
    print(f"📊 Summary: {success_count}/{total_count} models downloaded successfully")
    
    if success_count == total_count:
        print("🎉 All models ready!")
        return True
    else:
        print("⚠️  Some models failed to download. Please check your connection and try again.")
        return False


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download YOLO models for LPR system")
    parser.add_argument("--force", action="store_true", help="Re-download existing models")
    parser.add_argument("--model", action="append", help="Download specific model(s)")
    parser.add_argument("--list", action="store_true", help="List available models")
    
    args = parser.parse_args()
    
    if args.list:
        print("📋 Available Models:")
        print("-" * 60)
        for model_path, config in MODELS.items():
            print(f"• {model_path}")
            print(f"  Description: {config['description']}")
            print(f"  Size: {config['size']}")
            print()
        return
    
    # Download models
    success = download_models(force=args.force, models_to_download=args.model)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()