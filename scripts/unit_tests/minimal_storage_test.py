#!/usr/bin/env python
"""
Minimal script to test storage functionality in isolation.
This script bypasses all detection logic and directly tests the storage service.
"""
import os
import sys
import asyncio
import time
import json
import uuid
from pathlib import Path
import shutil

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.storage_service import StorageService

async def test_minimal_storage():
    """Test storage functionality with minimal dependencies"""
    print("\n=== Minimal Storage Test ===\n")

    # Create output directory in tests folder
    output_dir = "tests/output"
    os.makedirs(output_dir, exist_ok=True)

    # Create a clean data directory for this test with timestamp
    test_timestamp = str(int(time.time()))
    test_dir = os.path.join(output_dir, f"test_storage_{test_timestamp}")
    license_plates_dir = os.path.join(test_dir, "license_plates")
    enhanced_plates_dir = os.path.join(test_dir, "enhanced_plates")
    
    os.makedirs(license_plates_dir, exist_ok=True)
    os.makedirs(enhanced_plates_dir, exist_ok=True)
    
    print(f"Created test directories:")
    print(f"  {license_plates_dir}")
    print(f"  {enhanced_plates_dir}")
    
    # Create log file
    log_file = os.path.join(output_dir, f"storage_test_log_{test_timestamp}.txt")
    print(f"Log will be saved to: {log_file}")

    try:
        # Initialize storage service
        print("\nInitializing storage service...")
        storage_service = StorageService()
        await storage_service.initialize(
            license_plates_dir=license_plates_dir,
            enhanced_plates_dir=enhanced_plates_dir
        )
        
        # Set a shorter save interval for testing
        storage_service.save_interval = 1.0
        
        print(f"Storage service initialized.")
        print(f"Session file: {storage_service.session_file}")
        
        # Create test detections
        test_detections = [
            {
                "detection_id": f"test-{uuid.uuid4()}",
                "plate_text": f"ABC{i}23",
                "confidence": 0.9,
                "timestamp": time.time(),
                "box": [100, 100, 300, 200],
                "raw_text": f"ABC {i}23"
            } for i in range(5)
        ]
        
        # Add detections
        print(f"\nAdding {len(test_detections)} test detections...")
        await storage_service.add_detections(test_detections)
        
        # Force immediate save
        print("Forcing immediate save...")
        await storage_service._save_data()
        
        # Wait a moment
        print("Waiting for file operations to complete...")
        await asyncio.sleep(2)
        
        # Check if file exists and has content
        session_file = storage_service.session_file
        test_results = []

        if os.path.exists(session_file):
            file_size = os.path.getsize(session_file)
            result = f"\nSuccess! File created: {session_file} ({file_size} bytes)"
            print(result)
            test_results.append(result)
            
            # Read and verify content
            with open(session_file, 'r') as f:
                data = json.load(f)
                detection_count = len(data.get("detections", []))
                result = f"File contains {detection_count} detections"
                print(result)
                test_results.append(result)
                
                if detection_count == len(test_detections):
                    result = "\nSTORAGE TEST PASSED! All detections were saved correctly."
                    print(result)
                    test_results.append(result)
                else:
                    result = f"\nSTORAGE TEST FAILED. Expected {len(test_detections)} detections but found {detection_count}."
                    print(result)
                    test_results.append(result)

                # Copy the session file to output directory for reference
                output_json = os.path.join(output_dir, f"storage_test_results_{test_timestamp}.json")
                shutil.copy(session_file, output_json)
                print(f"Copied results to: {output_json}")
        else:
            result = f"\nSTORAGE TEST FAILED. File was not created: {session_file}"
            print(result)
            test_results.append(result)
            
            # Check directory contents
            dir_files = os.listdir(license_plates_dir)
            if dir_files:
                result = f"Directory contains {len(dir_files)} files:"
                print(result)
                test_results.append(result)
                for file in dir_files:
                    result = f"  {file}"
                    print(result)
                    test_results.append(result)
            else:
                result = f"Directory is empty: {license_plates_dir}"
                print(result)
                test_results.append(result)
        
        # Save test results to log file
        with open(log_file, 'w') as f:
            f.write("=== Minimal Storage Test Results ===\n\n")
            f.write(f"Test timestamp: {test_timestamp}\n")
            f.write(f"Test directory: {test_dir}\n\n")
            f.write("\n".join(test_results))

        # Shutdown
        print("\nShutting down storage service...")
        await storage_service.shutdown()
        print("Storage service shutdown complete")
        
    except Exception as e:
        error_msg = f"\nERROR: {e}"
        print(error_msg)

        # Save error to log file
        with open(log_file, 'a') as f:
            f.write("\n\n=== ERROR ===\n")
            f.write(error_msg)
            f.write("\n\nStacktrace:\n")
        import traceback
        traceback.print_exc(file=f)
    
        import traceback
        traceback.print_exc()

    finally:
        print(f"\nTest complete! Results saved to {log_file}")
        return test_dir  # Return the test directory path for reference

if __name__ == "__main__":
    # Parse command-line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Test storage functionality")
    parser.add_argument("--keep", action="store_true", help="Keep test files after completion")
    args = parser.parse_args()

    # Run the test
    test_dir = asyncio.run(test_minimal_storage())

    # Clean up test files unless --keep is specified
    if not args.keep and test_dir and os.path.exists(test_dir):
        print(f"Cleaning up test directory: {test_dir}")
        shutil.rmtree(test_dir)
    elif args.keep and test_dir:
        print(f"Test files kept at: {test_dir}")

