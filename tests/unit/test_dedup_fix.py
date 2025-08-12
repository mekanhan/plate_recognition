#!/usr/bin/env python3
"""
Test Deduplication Fix
Verify the enhanced pipeline is being used with aggressive deduplication
"""
import time
import os
import requests
from datetime import datetime


def check_api_status():
    """Check if API is running"""
    try:
        response = requests.get("http://localhost:8001/health")
        return response.status_code == 200
    except:
        return False


def monitor_detections(duration=120):
    """Monitor for 2 minutes to see if deduplication is working"""
    print(f"🔍 Monitoring deduplication for {duration} seconds...")
    print("Starting with clean detection folders...")
    print("=" * 60)
    
    start_time = time.time()
    initial_files = count_detection_files()
    last_count = initial_files
    save_events = []
    
    while time.time() - start_time < duration:
        current_time = datetime.now().strftime('%H:%M:%S')
        current_files = count_detection_files()
        
        # Check for new files
        if current_files > last_count:
            new_files = current_files - last_count
            save_events.append({
                'time': current_time,
                'count': current_files,
                'new': new_files
            })
            print(f"[{current_time}] 📸 NEW IMAGES SAVED: {new_files} (total: {current_files})")
            last_count = current_files
        else:
            print(f"\r[{current_time}] ✅ No new images - deduplication working (total: {current_files})", end='')
        
        time.sleep(5)  # Check every 5 seconds
    
    print(f"\n\n" + "=" * 60)
    print("📊 DEDUPLICATION TEST RESULTS")
    print("=" * 60)
    
    final_files = count_detection_files()
    total_saves = len(save_events)
    
    print(f"Duration: {duration} seconds ({duration/60:.1f} minutes)")
    print(f"Total images saved: {final_files}")
    print(f"Save events: {total_saves}")
    print(f"Average time between saves: {duration/total_saves:.0f} seconds" if total_saves > 0 else "No saves!")
    
    if total_saves == 0:
        print("🎉 EXCELLENT: No images saved - deduplication working perfectly!")
        return True
    elif total_saves <= 3:
        print("✅ GOOD: Very few images saved - deduplication mostly working")
        return True
    elif total_saves <= 10:
        print("⚠️ MODERATE: Some images saved - deduplication partially working")
        return False
    else:
        print("❌ BAD: Many images saved - deduplication failing")
        return False


def count_detection_files():
    """Count total detection files"""
    frame_count = len([f for f in os.listdir('detections/frames') if f.endswith('.jpg')]) if os.path.exists('detections/frames') else 0
    plate_count = len([f for f in os.listdir('detections/plates') if f.endswith('.jpg')]) if os.path.exists('detections/plates') else 0
    return frame_count + plate_count


def check_config():
    """Check configuration"""
    print("⚙️ Checking Configuration...")
    print("=" * 60)
    
    config_path = 'config/storage_config.json'
    if os.path.exists(config_path):
        try:
            import json
            with open(config_path, 'r') as f:
                config = json.load(f)
                dedup_config = config.get('deduplication', {})
                
                print(f"✅ Configuration loaded:")
                print(f"   Cooldown period: {dedup_config.get('cooldown_minutes', 'N/A')} minutes")
                print(f"   Max per hour: {dedup_config.get('max_per_plate_per_hour', 'N/A')}")
                print(f"   Window: {dedup_config.get('window_seconds', 'N/A')/60:.0f} minutes")
                print(f"   Min improvement: {dedup_config.get('min_confidence_improvement', 'N/A')*100:.0f}%")
                
                return True
        except Exception as e:
            print(f"❌ Error reading config: {e}")
    else:
        print(f"❌ Config file not found: {config_path}")
    
    return False


def check_api_integration():
    """Check if enhanced pipeline is being used"""
    print("\n🔧 Checking API Integration...")
    print("=" * 60)
    
    try:
        response = requests.get("http://localhost:8001/api/storage/stats")
        if response.status_code == 200:
            data = response.json()
            if 'deduplication' in data:
                print("✅ Enhanced pipeline active - deduplication stats available")
                dedup = data['deduplication']
                if dedup:
                    print(f"   Total detections: {dedup.get('total_detections', 0)}")
                    print(f"   Images saved: {dedup.get('detections_saved', 0)}")
                    print(f"   Images skipped: {dedup.get('detections_skipped', 0)}")
                    print(f"   Reduction rate: {dedup.get('reduction_percentage', 0):.1f}%")
                else:
                    print("⚠️ Enhanced pipeline active but no deduplication data yet")
                return True
            else:
                print("❌ Old pipeline still active - no deduplication stats")
                return False
        else:
            print(f"❌ API error: {response.status_code}")
    except Exception as e:
        print(f"❌ API check failed: {e}")
    
    return False


def main():
    """Run deduplication test"""
    print("🚀 Deduplication Fix Test")
    print("=" * 60)
    
    # Check API
    if not check_api_status():
        print("❌ API not running. Please start with: python3 start_lpr.py")
        return
    
    print("✅ API is running")
    
    # Check configuration
    config_ok = check_config()
    
    # Check API integration
    api_ok = check_api_integration()
    
    if not config_ok or not api_ok:
        print("\n⚠️ Issues detected. System may not work optimally.")
        user_input = input("Continue with monitoring test anyway? (y/n): ")
        if user_input.lower() != 'y':
            return
    
    # Start monitoring
    print(f"\n🎯 Starting deduplication monitoring...")
    print(f"Expected behavior with new settings:")
    print(f"   - Same plate: Max 1 save per 30 minutes")
    print(f"   - Max 2 saves per hour per unique plate")
    print(f"   - Noise plates (TEXAS, etc.) should be skipped")
    print(f"\nPress Ctrl+C to stop early...")
    
    try:
        success = monitor_detections(120)  # 2 minutes
        
        print(f"\n{'='*60}")
        if success:
            print("🎉 SUCCESS: Deduplication is working!")
        else:
            print("❌ FAILED: Deduplication needs more tuning")
            
        print(f"\n💡 Next steps:")
        print(f"   - Adjust config/storage_config.json if needed")
        print(f"   - Restart API after config changes")
        print(f"   - Use python3 monitor_dedup.py for detailed monitoring")
        
    except KeyboardInterrupt:
        print(f"\n\n⏹️ Test stopped by user")
        final_count = count_detection_files()
        print(f"Images saved during partial test: {final_count}")


if __name__ == "__main__":
    main()