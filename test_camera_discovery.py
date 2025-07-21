#!/usr/bin/env python3
"""
Test script for camera discovery functionality
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.services.camera_discovery_service import CameraDiscoveryService
from app.services.multi_camera_service import MultiCameraService
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_camera_discovery():
    """Test camera discovery functionality"""
    
    print("=== Camera Discovery Test ===")
    
    # Test 1: Direct CameraDiscoveryService
    print("\n1. Testing CameraDiscoveryService directly...")
    discovery_service = CameraDiscoveryService()
    
    try:
        # Test with a specific IP range that includes your camera
        discovered = await discovery_service.discover_cameras_on_network("10.0.0.0/24")
        print(f"✓ CameraDiscoveryService found {len(discovered)} cameras")
        
        for camera in discovered:
            print(f"  - {camera.ip_address}: {camera.manufacturer} {camera.model}")
            
    except Exception as e:
        print(f"✗ CameraDiscoveryService failed: {e}")
    
    # Test 2: MultiCameraService
    print("\n2. Testing MultiCameraService...")
    multi_cam_service = MultiCameraService()
    
    try:
        # Test with the same IP range
        discovered = await multi_cam_service.discover_cameras_on_network("10.0.0.0/24")
        print(f"✓ MultiCameraService found {len(discovered)} cameras")
        
        for camera in discovered:
            print(f"  - {camera['ip_address']}: {camera['manufacturer']} {camera['model']}")
            
    except Exception as e:
        print(f"✗ MultiCameraService failed: {e}")
    
    # Test 3: Test specific IP address
    print("\n3. Testing specific IP address (10.0.0.181)...")
    
    try:
        discovered = await discovery_service.discover_cameras_on_network("10.0.0.181/32")
        print(f"✓ Found {len(discovered)} cameras at 10.0.0.181")
        
        for camera in discovered:
            print(f"  - IP: {camera.ip_address}")
            print(f"  - Manufacturer: {camera.manufacturer}")
            print(f"  - Model: {camera.model}")
            print(f"  - Type: {camera.camera_type}")
            print(f"  - Discovery Method: {camera.discovery_method}")
            print(f"  - Confidence: {camera.confidence}")
            
    except Exception as e:
        print(f"✗ Specific IP test failed: {e}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(test_camera_discovery())