#!/usr/bin/env python3
"""
Monitor Deduplication Performance
Shows why images are being saved or skipped
"""
import requests
import time
import json
from datetime import datetime
from collections import defaultdict


def monitor_deduplication(duration_seconds=60):
    """Monitor deduplication in real-time"""
    print(f"🔍 Monitoring Deduplication for {duration_seconds} seconds")
    print("=" * 70)
    
    start_time = time.time()
    last_stats = None
    save_reasons = defaultdict(int)
    skip_reasons = defaultdict(int)
    plate_frequency = defaultdict(int)
    
    while time.time() - start_time < duration_seconds:
        try:
            # Get current stats
            response = requests.get("http://localhost:8001/api/storage/stats")
            if response.status_code == 200:
                data = response.json()
                dedup = data.get('deduplication', {})
                
                if dedup and last_stats:
                    # Calculate changes
                    new_detections = dedup.get('total_detections', 0) - last_stats.get('total_detections', 0)
                    new_saved = dedup.get('detections_saved', 0) - last_stats.get('detections_saved', 0)
                    new_skipped = dedup.get('detections_skipped', 0) - last_stats.get('detections_skipped', 0)
                    
                    if new_detections > 0:
                        save_rate = (new_saved / new_detections * 100) if new_detections > 0 else 0
                        
                        # Get recent detections to analyze reasons
                        det_response = requests.get("http://localhost:8001/api/detections/recent?limit=20")
                        if det_response.status_code == 200:
                            recent = det_response.json()
                            
                            # Count plate frequencies
                            for det in recent:
                                plate_frequency[det['plate_text']] += 1
                        
                        # Display real-time stats
                        print(f"\r[{datetime.now().strftime('%H:%M:%S')}] "
                              f"Detections: {new_detections} | "
                              f"Saved: {new_saved} ({save_rate:.0f}%) | "
                              f"Skipped: {new_skipped} | "
                              f"Active groups: {dedup.get('active_groups', 0)} | "
                              f"Tracked plates: {dedup.get('tracked_plates', 0)}", end='')
                
                last_stats = dedup
                
            time.sleep(2)  # Check every 2 seconds
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            break
    
    # Summary
    print("\n\n" + "=" * 70)
    print("📊 MONITORING SUMMARY")
    print("=" * 70)
    
    if last_stats:
        total = last_stats.get('total_detections', 0)
        saved = last_stats.get('detections_saved', 0)
        skipped = last_stats.get('detections_skipped', 0)
        
        print(f"Total detections processed: {total}")
        print(f"Images saved: {saved} ({saved/total*100:.1f}%)")
        print(f"Images skipped: {skipped} ({skipped/total*100:.1f}%)")
        print(f"Reduction rate: {100 - (saved/total*100):.1f}%")
        
        # Show most frequent plates
        print(f"\n📋 Most Frequent Plates:")
        for plate, count in sorted(plate_frequency.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   {plate}: {count} times")
        
        # Check configuration
        print(f"\n⚙️ Current Configuration:")
        try:
            with open('config/storage_config.json', 'r') as f:
                config = json.load(f)
                dedup_config = config.get('deduplication', {})
                print(f"   Cooldown: {dedup_config.get('cooldown_minutes', 'N/A')} minutes")
                print(f"   Max per hour: {dedup_config.get('max_per_plate_per_hour', 'N/A')}")
                print(f"   Window: {dedup_config.get('window_seconds', 'N/A')/60:.0f} minutes")
        except:
            print("   Could not load config")


def check_recent_saves():
    """Analyze why recent detections were saved"""
    print("\n🔍 Analyzing Recent Saves...")
    print("=" * 70)
    
    try:
        # Get recent detections from database
        response = requests.get("http://localhost:8001/api/detections/recent?limit=50")
        if response.status_code == 200:
            detections = response.json()
            
            # Group by plate text
            plate_groups = defaultdict(list)
            for det in detections:
                plate_groups[det['plate_text']].append(det)
            
            # Analyze each plate group
            for plate, dets in sorted(plate_groups.items(), key=lambda x: len(x[1]), reverse=True):
                if len(dets) > 1:
                    print(f"\n📌 Plate: {plate}")
                    print(f"   Occurrences: {len(dets)}")
                    
                    # Calculate time differences
                    times = [datetime.fromisoformat(d['detected_at']) for d in dets]
                    times.sort()
                    
                    if len(times) > 1:
                        time_diffs = []
                        for i in range(1, len(times)):
                            diff = (times[i] - times[i-1]).total_seconds()
                            time_diffs.append(diff)
                        
                        avg_interval = sum(time_diffs) / len(time_diffs)
                        min_interval = min(time_diffs)
                        
                        print(f"   Min interval: {min_interval:.0f} seconds")
                        print(f"   Avg interval: {avg_interval:.0f} seconds")
                        
                        # Check if images were saved
                        with_images = sum(1 for d in dets if d.get('plate_image'))
                        print(f"   With images: {with_images}/{len(dets)}")
                        
                        if min_interval < 60:
                            print(f"   ⚠️ WARNING: Saving too frequently! (< 1 minute)")
                        elif min_interval < 300:
                            print(f"   ⚡ Fast saves detected (< 5 minutes)")
    except Exception as e:
        print(f"❌ Error analyzing saves: {e}")


def main():
    """Run monitoring"""
    print("🚀 Deduplication Monitor")
    print("=" * 70)
    
    # Check if API is running
    try:
        response = requests.get("http://localhost:8001/health")
        if response.status_code != 200:
            print("❌ API is not running. Please start the API first.")
            return
    except:
        print("❌ Cannot connect to API at http://localhost:8001")
        return
    
    # Run analysis
    check_recent_saves()
    
    # Monitor in real-time
    print("\n" + "=" * 70)
    user_input = input("Monitor deduplication in real-time? (y/n): ")
    if user_input.lower() == 'y':
        duration = input("Duration in seconds (default 60): ")
        duration = int(duration) if duration else 60
        monitor_deduplication(duration)
    
    print("\n✅ Monitoring complete!")
    print("\n💡 If saving too frequently, check:")
    print("   1. Cooldown period in config/storage_config.json")
    print("   2. Noise patterns being detected as valid plates")
    print("   3. Object tracker creating new tracks too often")


if __name__ == "__main__":
    main()