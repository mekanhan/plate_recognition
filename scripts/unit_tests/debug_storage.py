#!/usr/bin/env python
"""
Diagnostic script to debug storage issues
"""
import os
import sys
import asyncio
import time
import json
import uuid
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.storage_service import StorageService

async def debug_storage():
    """Debug storage functionality"""
    print("\n=== Storage Service Diagnostic ===\n")
    
    # Check if directories exist and are writable
    license_plates_dir = "data/license_plates"
    enhanced_plates_dir = "data/enhanced_plates"
    
    print("Checking directories...")
    for directory in [license_plates_dir, enhanced_plates_dir]:
        if os.path.exists(directory):
            print(f"✓ Directory exists: {directory}")
            if os.access(directory, os.W_OK):
                print(f"✓ Directory is writable: {directory}")
            else:
                print(f"✗ Directory is NOT writable: {directory}")
        else:
            print(f"✗ Directory does NOT exist: {directory}")
            try:
                os.makedirs(directory, exist_ok=True)
                print(f"  Created directory: {directory}")
                if os.access(directory, os.W_OK):
                    print(f"✓ Directory is writable: {directory}")
                else:
                    print(f"✗ Directory is still NOT writable: {directory}")
            except Exception as e:
                print(f"✗ Could not create directory: {e}")
    
    # Try to create a simple file in each directory
    print("\nTesting file creation...")
    for directory in [license_plates_dir, enhanced_plates_dir]:
        test_file = os.path.join(directory, f"test_{int(time.time())}.txt")
        try:
            with open(test_file, 'w') as f:
                f.write("Test file")
            print(f"✓ Successfully created test file: {test_file}")
            os.remove(test_file)
            print(f"  Removed test file: {test_file}")
        except Exception as e:
            print(f"✗ Could not create test file: {e}")
    
    # Initialize storage service
    print("\nInitializing storage service...")
    storage_service = StorageService()
    await storage_service.initialize()
    
    print(f"Session file: {storage_service.session_file}")
    print(f"Enhanced session file: {storage_service.enhanced_session_file}")
    
    # Add a test detection
    print("\nAdding test detection...")
    detection = {
        "detection_id": f"test-{uuid.uuid4()}",
        "plate_text": "TEST123",
        "confidence": 0.9,
        "timestamp": time.time(),
        "box": [100, 100, 300, 200]
    }
    
    try:
        await storage_service.add_detections([detection])
        print("✓ Successfully added detection to storage")
    except Exception as e:
        print(f"✗ Error adding detection: {e}")
    
    # Add a test enhanced result
    print("\nAdding test enhanced result...")
    enhanced_result = {
        "enhanced_id": f"enh-{uuid.uuid4()}",
        "plate_text": "ENH123",
        "confidence": 0.95,
        "confidence_category": "HIGH",
        "match_type": "test",
        "timestamp": time.time()
    }
    
    try:
        await storage_service.add_enhanced_results([enhanced_result])
        print("✓ Successfully added enhanced result to storage")
    except Exception as e:
        print(f"✗ Error adding enhanced result: {e}")
    
    # Force immediate save
    print("\nForcing immediate save...")
    try:
        await storage_service._save_data()
        print("✓ Force save completed")
    except Exception as e:
        print(f"✗ Error during force save: {e}")
    
    # Verify files exist
    print("\nVerifying files...")
    for file_path in [storage_service.session_file, storage_service.enhanced_session_file]:
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"✓ File exists: {file_path} ({file_size} bytes)")
            
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                if "detections" in data:
                    print(f"  Contains {len(data['detections'])} detections")
                if "enhanced_results" in data:
                    print(f"  Contains {len(data['enhanced_results'])} enhanced results")
            except Exception as e:
                print(f"✗ Error reading file: {e}")
        else:
            print(f"✗ File does not exist: {file_path}")
    
    # Check memory state
    print("\nChecking in-memory state...")
    print(f"Detections in memory: {len(storage_service.plate_database['detections'])}")
    print(f"Enhanced results in memory: {len(storage_service.enhanced_database['enhanced_results'])}")
    
    # Clean shutdown
    print("\nShutting down storage service...")
    await storage_service.shutdown()
    print("✓ Storage service shutdown complete")

if __name__ == "__main__":
    asyncio.run(debug_storage())