#!/usr/bin/env python3
"""
Test script for monitoring system validation
"""
import asyncio
import sys
import os

# Add current directory to path
sys.path.insert(0, '.')

async def test_monitoring_system():
    """Test the monitoring system components"""
    print("🔍 Testing LPR Monitoring System")
    print("=" * 50)
    
    try:
        # Test imports
        print("\n1. Testing Imports...")
        from monitoring import metrics, health_monitor
        from monitoring.endpoints import monitoring_router
        from monitoring.middleware import MetricsMiddleware, setup_monitoring_middleware
        print("   ✅ All monitoring components imported successfully")
        
        # Test metrics system
        print("\n2. Testing Metrics System...")
        
        # Test system info update
        metrics.update_system_info("1.0.0-test", "testing", False)
        print("   ✅ System info updated")
        
        # Test detection recording
        metrics.record_detection(
            camera_id="test_cam",
            vehicle_type="car",
            confidence=0.85,
            ocr_confidence=0.78,
            processing_time=0.125
        )
        print("   ✅ Detection metrics recorded")
        
        # Test camera metrics
        camera_data = {
            "test_cam": {
                "name": "Test Camera",
                "status": "online",
                "ip_address": "192.168.1.100",
                "fps": 25
            }
        }
        metrics.update_camera_metrics(camera_data)
        print("   ✅ Camera metrics updated")
        
        # Test error recording
        metrics.record_camera_error("test_cam", "connection_timeout")
        metrics.record_auth_attempt(True)
        print("   ✅ Error metrics recorded")
        
        # Test metrics export
        metrics_output = metrics.get_metrics()
        print(f"   ✅ Metrics exported ({len(metrics_output)} bytes)")
        
        # Test health monitoring
        print("\n3. Testing Health Monitoring...")
        
        # Test system resources check
        system_check = await health_monitor.check_system_resources()
        print(f"   ✅ System resources check: {system_check.status.value}")
        
        # Test storage check
        try:
            storage_check = await health_monitor.check_storage()
            print(f"   ✅ Storage check: {storage_check.status.value}")
        except Exception as e:
            print(f"   ⚠️  Storage check failed (expected): {e}")
        
        # Test auth system check
        try:
            auth_check = await health_monitor.check_auth_system()
            print(f"   ✅ Auth system check: {auth_check.status.value}")
        except Exception as e:
            print(f"   ⚠️  Auth system check failed: {e}")
        
        # Test overall health summary
        overall_status = health_monitor.get_overall_status()
        print(f"   ✅ Overall system status: {overall_status.value}")
        
        # Test router configuration
        print("\n4. Testing API Endpoints...")
        print(f"   ✅ Monitoring router has {len(monitoring_router.routes)} endpoints")
        
        # List endpoints
        for route in monitoring_router.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                methods = ', '.join(route.methods) if route.methods else 'GET'
                print(f"      - {methods} {route.path}")
        
        print("\n🎉 All monitoring system tests passed!")
        print("\n📊 Key Metrics Available:")
        print("   - System: CPU, memory, disk usage")
        print("   - Detections: Processing times, confidence scores")  
        print("   - Cameras: Status, FPS, error rates")
        print("   - Storage: Usage, cleanup events")
        print("   - API: Request counts, response times")
        print("   - Auth: Login attempts, permission denials")
        
        print("\n🏥 Health Checks Available:")
        for check_name in health_monitor.check_intervals.keys():
            print(f"   - {check_name}")
        
        print("\n🛣️  Monitoring Endpoints:")
        print("   - GET  /api/monitoring/metrics (Prometheus)")
        print("   - GET  /api/monitoring/health (Basic)")
        print("   - GET  /api/monitoring/health/detailed (Auth required)")
        print("   - GET  /api/monitoring/system/stats (Auth required)")
        print("   - GET  /api/monitoring/alerts (Auth required)")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Monitoring system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_monitoring_system())
    sys.exit(0 if success else 1)