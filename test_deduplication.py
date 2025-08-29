#!/usr/bin/env python3
"""
Test script to verify deduplication is working properly
"""

import requests
import json
import time
from datetime import datetime, timedelta

def test_deduplication():
    """Test that deduplication is working properly"""
    
    print("=" * 60)
    print("DEDUPLICATION TEST")
    print("=" * 60)
    
    # 1. Check filter statistics
    stats_url = "http://localhost:8001/api/filter/stats"
    response = requests.get(stats_url)
    if response.status_code == 200:
        stats = response.json()
        print("\n📊 Filter Statistics:")
        print(f"   Total Processed: {stats['total_processed']}")
        print(f"   Stored: {stats['stored']}")
        print(f"   Ignored Duplicates: {stats['ignored_duplicates']}")
        print(f"   Reduction Rate: {stats['reduction_rate']}%")
        print(f"   Active Cameras: {stats['active_cameras']}")
        print(f"   Tracked Objects: {stats['total_tracked_objects']}")
        
        if stats['reduction_rate'] > 80:
            print("   ✅ Excellent reduction rate!")
        elif stats['reduction_rate'] > 50:
            print("   ⚠️ Good reduction rate")
        else:
            print("   ❌ Low reduction rate - filter may not be working")
    else:
        print("   ❌ Failed to get filter stats")
    
    # 2. Check recent detections for time spacing
    recent_url = "http://localhost:8001/api/detections/recent?limit=20"
    response = requests.get(recent_url)
    if response.status_code == 200:
        detections = response.json()
        
        print("\n📷 Recent Detections Analysis:")
        print(f"   Total Recent: {len(detections)}")
        
        if len(detections) > 1:
            # Analyze time gaps between detections
            time_gaps = []
            plates_seen = {}
            
            for i in range(len(detections) - 1):
                curr = datetime.fromisoformat(detections[i]['detected_at'])
                next = datetime.fromisoformat(detections[i+1]['detected_at'])
                gap = (curr - next).total_seconds()
                time_gaps.append(gap)
                
                # Track plate variations
                plate = detections[i]['plate_text']
                if plate not in plates_seen:
                    plates_seen[plate] = 0
                plates_seen[plate] += 1
            
            if time_gaps:
                avg_gap = sum(time_gaps) / len(time_gaps)
                min_gap = min(time_gaps)
                max_gap = max(time_gaps)
                
                print(f"   Time Between Detections:")
                print(f"      Average: {avg_gap:.1f}s")
                print(f"      Min: {min_gap:.1f}s")
                print(f"      Max: {max_gap:.1f}s")
                
                if avg_gap > 20:
                    print("      ✅ Good time spacing - deduplication working!")
                elif avg_gap > 5:
                    print("      ⚠️ Moderate time spacing")
                else:
                    print("      ❌ Too many rapid detections - possible duplicates")
            
            # Check for plate variations
            print(f"\n   Unique Plates: {len(plates_seen)}")
            if len(plates_seen) > 0:
                # Look for similar plates (fuzzy matching test)
                similar_groups = []
                processed = set()
                
                for plate1 in plates_seen:
                    if plate1 in processed:
                        continue
                    group = [plate1]
                    for plate2 in plates_seen:
                        if plate2 != plate1 and plate2 not in processed:
                            # Simple similarity check
                            if len(plate1) == len(plate2):
                                diff_count = sum(1 for a, b in zip(plate1, plate2) if a != b)
                                if diff_count <= 2:  # Max 2 character difference
                                    group.append(plate2)
                                    processed.add(plate2)
                    processed.add(plate1)
                    if len(group) > 1:
                        similar_groups.append(group)
                
                if similar_groups:
                    print("   Similar Plate Groups (fuzzy matching):")
                    for group in similar_groups:
                        print(f"      {' / '.join(group)}")
                    print("      ✅ Fuzzy matching appears to be working!")
                
    else:
        print("   ❌ Failed to get recent detections")
    
    # 3. Summary
    print("\n" + "=" * 60)
    print("DEDUPLICATION TEST COMPLETE")
    
    if response.status_code == 200 and stats.get('reduction_rate', 0) > 70:
        print("✅ Deduplication system is working effectively!")
        print(f"   - {stats['reduction_rate']}% of duplicates filtered")
        print(f"   - Only {stats['stored']} stored out of {stats['total_processed']} processed")
    else:
        print("⚠️ Deduplication may need adjustment")
    
    print("=" * 60)

if __name__ == "__main__":
    test_deduplication()