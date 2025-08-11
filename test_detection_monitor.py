#!/usr/bin/env python3
"""
Detection Monitoring Script
Monitor real-time detection activity to verify the enhanced LPR system
"""
import asyncio
import aiohttp
import time
from datetime import datetime, timedelta
import sys
import json

class DetectionMonitor:
    def __init__(self, api_base_url="http://localhost:8001"):
        self.api_base_url = api_base_url
        self.detection_count = 0
        self.last_detection_time = None
        
    async def check_system_health(self):
        """Check overall system health"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.api_base_url}/api/system/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        return {"error": f"HTTP {response.status}"}
            except Exception as e:
                return {"error": str(e)}
    
    async def check_recent_detections(self):
        """Check for recent detections"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.api_base_url}/api/detections/recent?limit=10") as response:
                    if response.status == 200:
                        detections = await response.json()
                        return detections
                    else:
                        return []
            except Exception as e:
                print(f"Error checking detections: {e}")
                return []
    
    async def get_camera_status(self):
        """Get camera status"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.api_base_url}/v2/api/cameras") as response:
                    if response.status == 200:
                        cameras = await response.json()
                        return cameras
                    else:
                        return []
            except Exception as e:
                print(f"Error checking cameras: {e}")
                return []
    
    async def monitor_continuously(self, duration_minutes=5):
        """Monitor detection activity continuously"""
        print(f"🔍 Starting Detection Monitor for {duration_minutes} minutes...")
        print("=" * 60)
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        last_detection_count = 0
        
        while time.time() < end_time:
            # Check system health
            health = await self.check_system_health()
            
            # Check recent detections
            detections = await self.check_recent_detections()
            current_detection_count = len(detections)
            
            # Check camera status
            cameras = await self.get_camera_status()
            
            # Display status
            current_time = datetime.now().strftime("%H:%M:%S")
            print(f"\n⏰ {current_time} - System Status:")
            
            # System health
            if "error" not in health:
                processing_status = health.get("processing_loop_status", "unknown")
                total_cameras = health.get("total_cameras", 0)
                models_loaded = health.get("ai_models_loaded", {})
                
                print(f"   📊 Processing Loop: {processing_status}")
                print(f"   📹 Total Cameras: {total_cameras}")
                print(f"   🧠 Models: YOLO Vehicle: {models_loaded.get('yolo_vehicle', False)}, "
                      f"YOLO Plate: {models_loaded.get('yolo_plate', False)}, "
                      f"OCR: {models_loaded.get('ocr_reader', False)}")
                
                # Camera details
                active_cameras = 0
                for camera in cameras:
                    status = camera.get('current_status', {})
                    connection_status = status.get('connection_status', 'unknown')
                    if 'Connected' in connection_status or 'online' in connection_status.lower():
                        active_cameras += 1
                
                print(f"   🟢 Active Cameras: {active_cameras}/{len(cameras)}")
                
            else:
                print(f"   ❌ System Health Error: {health['error']}")
            
            # Detection status
            print(f"   🎯 Recent Detections: {current_detection_count}")
            
            if current_detection_count > last_detection_count:
                new_detections = current_detection_count - last_detection_count
                print(f"   ✨ NEW DETECTIONS: +{new_detections} since last check!")
                
                # Show latest detection details
                if detections:
                    latest = detections[0]
                    print(f"      📅 Latest: {latest.get('detected_at', 'unknown')}")
                    print(f"      🔤 Plate: {latest.get('plate_text', 'unknown')}")
                    print(f"      🚗 Vehicle: {latest.get('vehicle_type', 'unknown')}")
                    print(f"      💯 Confidence: {latest.get('confidence', 0):.2f}")
                
            last_detection_count = current_detection_count
            
            # Wait before next check
            await asyncio.sleep(10)  # Check every 10 seconds
        
        print("\n" + "=" * 60)
        print(f"✅ Monitoring completed. Total detections found: {current_detection_count}")
    
    async def single_check(self):
        """Perform a single comprehensive check"""
        print("🔍 Detection System Status Check")
        print("=" * 40)
        
        # System health
        print("\n📊 System Health:")
        health = await self.check_system_health()
        print(json.dumps(health, indent=2))
        
        # Recent detections
        print("\n🎯 Recent Detections:")
        detections = await self.check_recent_detections()
        if detections:
            for i, detection in enumerate(detections[:3]):  # Show top 3
                print(f"   {i+1}. {detection.get('plate_text', 'N/A')} - "
                      f"{detection.get('vehicle_type', 'N/A')} - "
                      f"Confidence: {detection.get('confidence', 0):.2f} - "
                      f"Time: {detection.get('detected_at', 'N/A')}")
        else:
            print("   No recent detections found")
        
        # Camera status
        print("\n📹 Camera Status:")
        cameras = await self.get_camera_status()
        for camera in cameras:
            name = camera.get('name', 'Unknown')
            status = camera.get('current_status', {})
            connection = status.get('connection_status', 'unknown')
            print(f"   📷 {name}: {connection}")

async def main():
    monitor = DetectionMonitor()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "monitor":
            duration = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            await monitor.monitor_continuously(duration)
        elif sys.argv[1] == "check":
            await monitor.single_check()
        else:
            print("Usage: python test_detection_monitor.py [check|monitor] [minutes]")
    else:
        # Default: single check
        await monitor.single_check()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Monitoring stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")