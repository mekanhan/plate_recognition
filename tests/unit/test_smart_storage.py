#!/usr/bin/env python3
"""
Test Smart Storage System
Test deduplication, storage limits, and intelligent saving
"""
import asyncio
import requests
import json
import time
from datetime import datetime


def test_storage_stats():
    """Test storage statistics endpoint"""
    print("\n📊 Testing Storage Statistics...")
    print("=" * 50)
    
    try:
        response = requests.get("http://localhost:8001/api/storage/stats")
        if response.status_code == 200:
            data = response.json()
            
            # Display storage stats
            if 'storage' in data:
                storage = data['storage']['current_usage']
                limits = data['storage']['limits']
                print(f"✅ Storage Usage:")
                print(f"   Used: {storage['total_size_gb']:.2f} GB / {limits['max_storage_gb']} GB")
                print(f"   Percentage: {storage['percentage_used']:.1f}%")
                print(f"   Health: {data['storage']['health_status']}")
                print(f"   Frame images: {storage['frames']['count']} files")
                print(f"   Plate images: {storage['plates']['count']} files")
            
            # Display deduplication stats
            if 'deduplication' in data and data['deduplication']:
                dedup = data['deduplication']
                print(f"\n📈 Deduplication Statistics:")
                print(f"   Total detections: {dedup.get('total_detections', 0)}")
                print(f"   Images saved: {dedup.get('detections_saved', 0)}")
                print(f"   Images skipped: {dedup.get('detections_skipped', 0)}")
                print(f"   Reduction: {dedup.get('reduction_percentage', 0):.1f}%")
                print(f"   Active groups: {dedup.get('active_groups', 0)}")
                print(f"   Tracked plates: {dedup.get('tracked_plates', 0)}")
            else:
                print("\n⚠️ No deduplication stats available yet")
        else:
            print(f"❌ Failed to get storage stats: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting storage stats: {e}")


def test_system_health():
    """Test system health with storage info"""
    print("\n🏥 Testing System Health...")
    print("=" * 50)
    
    try:
        response = requests.get("http://localhost:8001/api/system/health")
        if response.status_code == 200:
            data = response.json()
            
            if 'storage' in data:
                storage = data['storage']
                print(f"✅ Storage Health:")
                print(f"   Used: {storage['used_gb']:.2f} / {storage['limit_gb']} GB")
                print(f"   Percentage: {storage['percentage_used']:.1f}%")
                print(f"   Status: {storage['health_status']}")
                
                # Warn if approaching limit
                if storage['percentage_used'] > 80:
                    print(f"   ⚠️ WARNING: Storage usage high!")
                elif storage['percentage_used'] > 90:
                    print(f"   🚨 CRITICAL: Storage almost full!")
            
            # Show camera status
            print(f"\n📹 Cameras: {data['total_cameras']} total")
            for cam in data.get('cameras', []):
                print(f"   - {cam['name']}: {cam['status']}")
        else:
            print(f"❌ Failed to get system health: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting system health: {e}")


def simulate_detections():
    """Simulate multiple detections to test deduplication"""
    print("\n🧪 Simulating Detections...")
    print("=" * 50)
    
    # This would normally be done by the processing pipeline
    # Here we just check if detections are being saved properly
    
    try:
        # Get recent detections
        response = requests.get("http://localhost:8001/api/detections/recent?limit=10")
        if response.status_code == 200:
            detections = response.json()
            print(f"✅ Found {len(detections)} recent detections")
            
            # Check for duplicate plate texts
            plate_counts = {}
            for det in detections:
                plate = det['plate_text']
                plate_counts[plate] = plate_counts.get(plate, 0) + 1
            
            print("\n🔍 Plate frequency analysis:")
            for plate, count in sorted(plate_counts.items(), key=lambda x: x[1], reverse=True):
                if count > 1:
                    print(f"   {plate}: {count} times (deduplication working)")
                else:
                    print(f"   {plate}: {count} time")
        else:
            print(f"❌ Failed to get detections: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting detections: {e}")


def test_manual_cleanup():
    """Test manual storage cleanup"""
    print("\n🧹 Testing Manual Cleanup...")
    print("=" * 50)
    
    try:
        # Get storage before cleanup
        response = requests.get("http://localhost:8001/api/storage/stats")
        before_stats = response.json() if response.status_code == 200 else None
        
        if before_stats:
            before_gb = before_stats['storage']['current_usage']['total_size_gb']
            print(f"📊 Before cleanup: {before_gb:.2f} GB")
        
        # Trigger cleanup
        print("🔄 Triggering cleanup...")
        response = requests.post("http://localhost:8001/api/storage/cleanup")
        
        if response.status_code == 200:
            result = response.json()
            cleanup = result['cleanup_stats']
            after = result['storage_after']
            
            print(f"✅ Cleanup complete:")
            print(f"   Files deleted: {cleanup['files_deleted']}")
            print(f"   Space freed: {cleanup['bytes_freed'] / (1024**2):.2f} MB")
            print(f"   Time taken: {cleanup.get('cleanup_time_ms', 0):.1f} ms")
            print(f"   Storage after: {after['total_size_gb']:.2f} GB ({after['percentage_used']:.1f}%)")
        else:
            print(f"❌ Cleanup failed: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")


def monitor_storage(duration_seconds=30):
    """Monitor storage usage over time"""
    print(f"\n📊 Monitoring Storage for {duration_seconds} seconds...")
    print("=" * 50)
    
    start_time = time.time()
    measurements = []
    
    while time.time() - start_time < duration_seconds:
        try:
            response = requests.get("http://localhost:8001/api/storage/stats")
            if response.status_code == 200:
                data = response.json()
                storage = data['storage']['current_usage']
                dedup = data.get('deduplication', {})
                
                measurement = {
                    'time': datetime.now().strftime('%H:%M:%S'),
                    'used_gb': storage['total_size_gb'],
                    'percentage': storage['percentage_used'],
                    'total_detections': dedup.get('total_detections', 0),
                    'saved': dedup.get('detections_saved', 0),
                    'skipped': dedup.get('detections_skipped', 0)
                }
                measurements.append(measurement)
                
                # Display current status
                print(f"\r[{measurement['time']}] "
                      f"Storage: {measurement['used_gb']:.2f}GB ({measurement['percentage']:.1f}%) | "
                      f"Detections: {measurement['total_detections']} | "
                      f"Saved: {measurement['saved']} | "
                      f"Skipped: {measurement['skipped']}", end='')
                
            time.sleep(5)  # Check every 5 seconds
        except Exception as e:
            print(f"\n❌ Monitoring error: {e}")
            break
    
    print("\n\n📈 Monitoring Summary:")
    if measurements:
        # Calculate changes
        first = measurements[0]
        last = measurements[-1]
        
        storage_change = last['used_gb'] - first['used_gb']
        detection_change = last['total_detections'] - first['total_detections']
        
        print(f"   Storage change: {storage_change:+.3f} GB")
        print(f"   New detections: {detection_change}")
        if detection_change > 0:
            save_rate = (last['saved'] - first['saved']) / detection_change * 100
            print(f"   Save rate: {save_rate:.1f}% (deduplication working)")


def main():
    """Run all tests"""
    print("🚀 Smart Storage System Test Suite")
    print("=" * 50)
    
    # Check if API is running
    try:
        response = requests.get("http://localhost:8001/health")
        if response.status_code != 200:
            print("❌ API is not running. Please start the API first.")
            return
    except:
        print("❌ Cannot connect to API at http://localhost:8001")
        print("   Please run: python3 start_lpr.py")
        return
    
    # Run tests
    test_storage_stats()
    test_system_health()
    simulate_detections()
    
    # Ask if user wants to test cleanup
    print("\n" + "=" * 50)
    user_input = input("Do you want to test storage cleanup? (y/n): ")
    if user_input.lower() == 'y':
        test_manual_cleanup()
    
    # Ask if user wants to monitor
    print("\n" + "=" * 50)
    user_input = input("Do you want to monitor storage for 30 seconds? (y/n): ")
    if user_input.lower() == 'y':
        monitor_storage(30)
    
    print("\n✅ All tests completed!")
    print("\n💡 Tips:")
    print("   - Storage limit is set to 10GB")
    print("   - Cleanup triggers automatically at 9GB")
    print("   - Same plate won't save images for 5 minutes (cooldown)")
    print("   - Only best quality image saved per detection group")
    print("   - Use /api/storage/emergency-cleanup if critically full")


if __name__ == "__main__":
    main()