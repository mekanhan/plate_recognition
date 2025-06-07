#!/usr/bin/env python
"""
Test script for verifying storage service integration with detection and enhancer
"""
import asyncio
import sys
import os
import time
import uuid
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.storage_service import StorageService
from app.services.enhancer_service import EnhancerService

async def test_enhancer_storage_integration():
    """Test the integration between enhancer and storage services"""
    print("\n=== Testing Enhancer-Storage Integration ===\n")
    
    # Create and initialize services
    storage_service = StorageService()
    await storage_service.initialize()
    print(f"Storage service initialized")
    
    enhancer_service = EnhancerService()
    await enhancer_service.initialize(storage_service=storage_service)
    print(f"Enhancer service initialized and connected to storage")
    
    # Create a test detection
    test_detection = {
        "detection_id": str(uuid.uuid4()),
        "plate_text": "VBR7660",  # This is in known_plates
        "confidence": 0.75,
        "ocr_confidence": 0.75,
        "timestamp": time.time(),
        "box": [100, 100, 300, 200]
    }
    
    print(f"\nEnhancing test detection with plate: {test_detection['plate_text']}")
    enhanced_result = await enhancer_service.enhance_detection(test_detection)
    
    print(f"Enhanced result: {enhanced_result['plate_text']} "
          f"(Confidence: {enhanced_result['confidence']:.2f}, "
          f"Category: {enhanced_result['confidence_category']})")
    
    # Wait a moment for any async operations to complete
    await asyncio.sleep(1)
    
    # Check if the enhanced result was saved
    enhanced_results = await storage_service.get_enhanced_results()
    
    if enhanced_results:
        print(f"\nFound {len(enhanced_results)} enhanced result(s) in storage")
        for result in enhanced_results:
            print(f"- {result['plate_text']} (Confidence: {result['confidence']:.2f}, "
                  f"Category: {result['confidence_category']})")
        
        # Check if the file was created
        if os.path.exists(storage_service.enhanced_session_file):
            file_size = os.path.getsize(storage_service.enhanced_session_file)
            print(f"\nEnhanced results file created: {storage_service.enhanced_session_file}")
            print(f"File size: {file_size} bytes")
            print("\nTEST PASSED! Enhanced results were properly saved to storage.")
        else:
            print(f"\nTEST FAILED. Enhanced results file was not created: {storage_service.enhanced_session_file}")
    else:
        print("\nTEST FAILED. No enhanced results found in storage.")
    
    # Shutdown services
    await storage_service.shutdown()
    print("\nTest complete!")

if __name__ == "__main__":
    asyncio.run(test_enhancer_storage_integration())