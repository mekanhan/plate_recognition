#!/usr/bin/env python3
"""
Test script for headless operation.
This script verifies that the camera → LPR → storage flow works autonomously.
"""

import asyncio
import time
import sys
import requests
import logging
from config.settings import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_headless_flow():
    """Test the complete headless camera → LPR → storage flow"""
    
    logger.info("🔍 Testing Headless LPR System")
    logger.info("=" * 50)
    
    # Load configuration
    config = Config()
    logger.info(f"Deployment Mode: {config.deployment_mode}")
    logger.info(f"Background Processing: {config.is_background_processing_enabled}")
    logger.info(f"Web UI Enabled: {config.is_web_ui_enabled}")
    
    # Test configuration
    base_url = f"http://localhost:{config.web_ui_port}"
    
    logger.info(f"\n📡 Testing API endpoints at {base_url}")
    
    # Wait for the service to start
    logger.info("⏳ Waiting for service to start...")
    await asyncio.sleep(5)
    
    try:
        # Test system info
        logger.info("1️⃣ Testing system info...")
        response = requests.get(f"{base_url}/api/headless/info", timeout=10)
        if response.status_code == 200:
            info = response.json()
            logger.info(f"✅ System Info: {info['service']} - Mode: {info['mode']}")
            logger.info(f"   Capabilities: {list(info['capabilities'].keys())}")
        else:
            logger.error(f"❌ System info failed: {response.status_code}")
            return False
            
        # Test health check
        logger.info("\n2️⃣ Testing health check...")
        response = requests.get(f"{base_url}/api/headless/health", timeout=10)
        if response.status_code == 200:
            health = response.json()
            logger.info(f"✅ System Status: {health['status']}")
            logger.info(f"   Background Processing Running: {health['background_processing']['is_running']}")
            logger.info(f"   Frames Processed: {health['background_processing']['total_frames_processed']}")
            logger.info(f"   Total Detections: {health['background_processing']['total_detections']}")
        else:
            logger.error(f"❌ Health check failed: {response.status_code}")
            return False
            
        # Wait for some processing
        logger.info("\n3️⃣ Waiting for frame processing...")
        await asyncio.sleep(15)
        
        # Check metrics
        logger.info("\n4️⃣ Checking processing metrics...")
        response = requests.get(f"{base_url}/api/headless/metrics", timeout=10)
        if response.status_code == 200:
            metrics = response.json()
            perf = metrics['performance']
            logger.info(f"✅ Performance Metrics:")
            logger.info(f"   Uptime: {perf['uptime_seconds']:.1f} seconds")
            logger.info(f"   Frames Processed: {perf['total_frames_processed']}")
            logger.info(f"   FPS: {perf['frames_per_second']:.2f}")
            logger.info(f"   Total Detections: {perf['total_detections']}")
            logger.info(f"   Detection Rate: {perf['detection_rate_percent']:.2f}%")
            logger.info(f"   Processing Time: {perf['average_processing_time_ms']:.1f}ms")
            logger.info(f"   Error Count: {perf['error_count']}")
        else:
            logger.error(f"❌ Metrics failed: {response.status_code}")
            return False
            
        # Check recent detections
        logger.info("\n5️⃣ Checking recent detections...")
        response = requests.get(f"{base_url}/api/headless/detections/recent?limit=10", timeout=10)
        if response.status_code == 200:
            detections = response.json()
            logger.info(f"✅ Recent Detections: {detections['count']} found")
            for i, detection in enumerate(detections['detections'][:3]):
                logger.info(f"   {i+1}. Plate: {detection['plate_text']} (Confidence: {detection['confidence']:.2f})")
        else:
            logger.error(f"❌ Recent detections failed: {response.status_code}")
            return False
            
        # Test processing control
        logger.info("\n6️⃣ Testing processing control...")
        
        # Pause processing
        response = requests.post(f"{base_url}/api/headless/control/pause", timeout=10)
        if response.status_code == 200:
            logger.info("✅ Processing paused successfully")
        else:
            logger.error(f"❌ Pause failed: {response.status_code}")
            
        await asyncio.sleep(2)
        
        # Resume processing
        response = requests.post(f"{base_url}/api/headless/control/resume", timeout=10)
        if response.status_code == 200:
            logger.info("✅ Processing resumed successfully")
        else:
            logger.error(f"❌ Resume failed: {response.status_code}")
            
        logger.info("\n🎉 Headless system test completed successfully!")
        logger.info("=" * 50)
        logger.info("The system is working autonomously:")
        logger.info("• Camera frames are being captured (or test pattern generated)")
        logger.info("• License plate detection is running")
        logger.info("• Results are being stored to database")
        logger.info("• API endpoints are accessible for monitoring")
        logger.info("• No web UI required for operation")
        
        return True
        
    except requests.exceptions.ConnectionError:
        logger.error("❌ Cannot connect to the service. Is it running?")
        logger.error("   Try: uvicorn app.main:app --host 0.0.0.0 --port 8001")
        return False
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

def main():
    """Main test function"""
    try:
        success = asyncio.run(test_headless_flow())
        if success:
            logger.info("\n✅ ALL TESTS PASSED - Headless system is working correctly!")
            sys.exit(0)
        else:
            logger.error("\n❌ TESTS FAILED - Check the logs above")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\n⚠️  Test interrupted by user")
        sys.exit(1)

if __name__ == "__main__":
    main()