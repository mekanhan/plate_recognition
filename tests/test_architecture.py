#!/usr/bin/env python3
"""
Basic architecture verification test

This script verifies that the headless architecture files are properly structured
and contain the expected components without requiring external dependencies.
"""

import os
import sys
from pathlib import Path

def test_file_exists(file_path, description):
    """Test if a file exists"""
    if os.path.exists(file_path):
        print(f"✓ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} - NOT FOUND")
        return False

def test_file_contains(file_path, patterns, description):
    """Test if a file contains expected patterns"""
    if not os.path.exists(file_path):
        print(f"❌ {description}: {file_path} - FILE NOT FOUND")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        missing_patterns = []
        for pattern in patterns:
            if pattern not in content:
                missing_patterns.append(pattern)
        
        if not missing_patterns:
            print(f"✓ {description}: {file_path}")
            return True
        else:
            print(f"❌ {description}: {file_path} - Missing: {missing_patterns}")
            return False
            
    except Exception as e:
        print(f"❌ {description}: {file_path} - Error reading file: {e}")
        return False

def run_architecture_tests():
    """Run architecture verification tests"""
    print("Starting headless architecture verification...")
    print("=" * 60)
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Core configuration file
    tests_total += 1
    if test_file_contains(
        "config/settings.py",
        ["DeploymentMode", "ProcessingMode", "is_headless_mode", "is_background_processing_enabled"],
        "Configuration with headless support"
    ):
        tests_passed += 1
    
    # Test 2: Background Stream Manager
    tests_total += 1
    if test_file_contains(
        "app/services/background_stream_manager.py",
        ["BackgroundStreamManager", "StreamConfig", "ProcessingMode", "async def start", "async def stop"],
        "Background Stream Manager"
    ):
        tests_passed += 1
    
    # Test 3: Output Channel Manager
    tests_total += 1
    if test_file_contains(
        "app/services/output_channel_manager.py",
        ["OutputChannelManager", "OutputChannel", "StorageOutputChannel", "WebSocketOutputChannel", "APIOutputChannel"],
        "Output Channel Manager"
    ):
        tests_passed += 1
    
    # Test 4: Stream Processor
    tests_total += 1
    if test_file_contains(
        "app/services/stream_processor.py",
        ["StreamProcessor", "PlateTracker", "process_frame_with_detection", "add_detections"],
        "Stream Processor"
    ):
        tests_passed += 1
    
    # Test 5: Updated main.py with headless support
    tests_total += 1
    if test_file_contains(
        "app/main.py",
        ["is_headless_mode", "is_background_processing_enabled", "BackgroundStreamManager", "OutputChannelManager"],
        "Main app with headless support"
    ):
        tests_passed += 1
    
    # Test 6: Updated routers with mode checks
    tests_total += 1
    if test_file_contains(
        "app/routers/stream.py",
        ["config.is_web_ui_enabled", "HTTPException", "headless mode"],
        "Stream router with headless checks"
    ):
        tests_passed += 1
    
    # Test 7: Configuration examples
    tests_total += 1
    if test_file_exists(".env.headless.example", "Headless configuration example"):
        tests_passed += 1
    
    # Test 8: Check for headless API endpoints in main.py
    tests_total += 1
    if test_file_contains(
        "app/main.py",
        ["/api/headless", "headless_router", "get_background_status", "pause_background_processing"],
        "Headless API endpoints"
    ):
        tests_passed += 1
    
    # Test 9: Verify lifecycle management
    tests_total += 1
    if test_file_contains(
        "app/main.py",
        ["background_stream_manager.stop()", "output_channel_manager.close()", "shutdown_event"],
        "Lifecycle management in main.py"
    ):
        tests_passed += 1
    
    # Test 10: Verify conditional web UI initialization
    tests_total += 1
    if test_file_contains(
        "app/main.py",
        ["if config.is_web_ui_enabled:", "templates = None", "headless mode"],
        "Conditional web UI initialization"
    ):
        tests_passed += 1
    
    print("=" * 60)
    print(f"Architecture Test Results: {tests_passed}/{tests_total} passed")
    
    if tests_passed == tests_total:
        print("🎉 All architecture tests passed!")
        print("\nHeadless architecture implementation verified:")
        print("✓ Configuration-driven deployment modes")
        print("✓ Background stream processing")
        print("✓ Multiple output channels")
        print("✓ Decoupled stream processing")
        print("✓ Lifecycle management")
        print("✓ API endpoints for headless control")
        print("✓ Conditional web UI components")
        print("\nTo test functionality:")
        print("1. Copy .env.headless.example to .env")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Run in headless mode: python -m uvicorn app.main:app --host 0.0.0.0 --port 8001")
        print("4. Test API: curl http://localhost:8001/api/headless/health")
        return True
    else:
        print("❌ Some architecture components are missing or incomplete")
        return False

if __name__ == "__main__":
    success = run_architecture_tests()
    sys.exit(0 if success else 1)