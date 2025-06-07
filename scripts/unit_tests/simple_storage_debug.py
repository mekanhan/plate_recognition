#!/usr/bin/env python
"""
Simple debugging script to test only the storage service without any dependencies.
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

async def main():
    """Main test function"""
    print("\n=== Storage Service Debug ===\n")
    
    # Use the default data directories
    license_plates_dir = "data/license_plates"
    enhanced_plates_dir = "data/enhanced_plates"
    
    # Ensure directories exist
    os.makedirs(license_plates_dir, exist_ok=True)
    os.makedirs(enhanced_plates_dir, exist_ok=True)
    
    # Initialize storage service
    print("Initializing storage service...")
    storage_service = StorageService()
    await storage_service.initialize(
        license_plates_dir=license_plates_dir,
        enhanced_plates_dir=enhanced_plates_dir
    )
    
    print(f"Storage service initialized")
    print(f"Session file: {storage_service.session_file}")
    
    # Create test detection
    detection = {
        "detection_id": f"debug-{uuid.uuid4()}",
        "plate_text": "TEST123",
        "confidence": 0.95,
        "timestamp": time.time(),
        "box": [100, 100, 300, 200],
        "raw_text": "TEST 123"
    }
    
    # Add detection
    print("\nAdding test detection...")
    await storage_service.add_detections([detection])
    
    # Check in-memory state
    print("\nChecking in-memory state:")
    detection_count = len(storage_service.plate_database["detections"])
    print(f"Detections in memory: {detection_count}")
    
    if detection_count > 0:
        print("✓ Detection was added to in-memory database")
    else:
        print("✗ Detection was NOT added to in-memory database")
    
    # Force immediate save
    print("\nForcing immediate save...")
    await storage_service._save_data()
    
    # Check file
    session_file = storage_service.session_file
    print(f"\nChecking session file: {session_file}")
    
    if os.path.exists(session_file):
        file_size = os.path.getsize(session_file)
        print(f"✓ File exists ({file_size} bytes)")
        
        # Read file content
        try:
            with open(session_file, 'r') as f:
                data = json.load(f)
                saved_count = len(data.get("detections", []))
                print(f"✓ File contains {saved_count} detections")
                
                if saved_count > 0:
                    print("✓ TEST PASSED: Detections were saved to file")
                    # Print the first detection
                    print("\nFirst detection in file:")
                    print(json.dumps(data["detections"][0], indent=2))
                else:
                    print("✗ TEST FAILED: No detections in file")
        except Exception as e:
            print(f"✗ Error reading file: {e}")
    else:
        print(f"✗ File does not exist")
        
        # Check directory contents
        print("\nChecking directory contents:")
        dir_files = os.listdir(license_plates_dir)
        if dir_files:
            print(f"Directory contains {len(dir_files)} files:")
            for file in dir_files:
                print(f"  {file}")
        else:
            print(f"Directory is empty")
    
    # Test periodic save
    print("\nTesting periodic save functionality...")
    print(f"Current save interval: {storage_service.save_interval} seconds")
    
    # Add another detection
    detection2 = {
        "detection_id": f"debug-{uuid.uuid4()}",
        "plate_text": "XYZ789",
        "confidence": 0.9,
        "timestamp": time.time(),
        "box": [200, 200, 400, 300],
        "raw_text": "XYZ 789"
    }
    
    print(f"Adding second test detection...")
    await storage_service.add_detections([detection2])
    
    # Wait for periodic save
    wait_time = storage_service.save_interval + 0.5
    print(f"Waiting {wait_time} seconds for periodic save to occur...")
    await asyncio.sleep(wait_time)
    
    # Check file again
    print("\nChecking if file was updated by periodic save...")
    if os.path.exists(session_file):
        with open(session_file, 'r') as f:
            data = json.load(f)
            saved_count = len(data.get("detections", []))
            print(f"File now contains {saved_count} detections")
            
            if saved_count >= 2:
                print("✓ TEST PASSED: Periodic save is working")
            else:
                print("✗ TEST FAILED: Periodic save did not update the file")
    else:
        print("✗ TEST FAILED: File does not exist after periodic save")
    
    # Shutdown
    print("\nShutting down storage service...")
    await storage_service.shutdown()
    print("Storage service shutdown complete")
    
    print("\nTest complete!")

if __name__ == "__main__":
    asyncio.run(main())