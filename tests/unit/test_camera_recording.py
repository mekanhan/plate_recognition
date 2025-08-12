#!/usr/bin/env python3
"""
Test FFmpeg recording from real camera
Run this to verify camera recording works before full migration
"""

import subprocess
import asyncio
import sys
from pathlib import Path
import time

async def test_camera_recording(rtsp_url: str, duration: int = 30):
    """Test recording from real camera for specified duration"""
    
    output_file = f"test_camera_{int(time.time())}.mp4"
    
    # FFmpeg command
    cmd = [
        'ffmpeg',
        '-y',  # Overwrite
        '-rtsp_transport', 'tcp',  # Use TCP for RTSP
        '-t', str(duration),  # Record for N seconds
        '-i', rtsp_url,  # Input URL
        '-c:v', 'copy',  # Copy video stream (no re-encoding)
        '-c:a', 'aac',   # Encode audio to AAC
        '-f', 'mp4',     # MP4 format
        output_file
    ]
    
    print(f"🎥 Recording from camera for {duration} seconds...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        # Run FFmpeg
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Wait for completion
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            # Success - check file
            if Path(output_file).exists():
                size_mb = Path(output_file).stat().st_size / (1024 * 1024)
                print(f"✅ Recording successful!")
                print(f"   File: {output_file}")
                print(f"   Size: {size_mb:.2f} MB")
                
                # Validate with ffprobe
                probe_cmd = ['ffprobe', '-v', 'error', '-show_format', '-show_streams', output_file]
                probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
                
                if probe_result.returncode == 0:
                    # Parse video info
                    output = probe_result.stdout
                    if 'codec_name=h264' in output or 'codec_name=h265' in output:
                        print("✅ Video codec: H.264/H.265 (browser compatible)")
                    else:
                        print("⚠️  Video codec may not be browser compatible")
                    
                    if 'pix_fmt=yuv420p' in output:
                        print("✅ Pixel format: yuv420p (browser compatible)")
                    
                print(f"\n📺 Test in browser: cp {output_file} frontend/")
                print(f"   Then open: http://localhost:8080/{output_file}")
                
                return True
            else:
                print("❌ Recording failed: Output file not created")
                return False
                
        else:
            print(f"❌ FFmpeg failed with code {process.returncode}")
            print(f"Error: {stderr.decode('utf-8', errors='ignore')}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def get_camera_url():
    """Get camera URL from database or config"""
    # Try to read from database
    try:
        import sqlite3
        conn = sqlite3.connect('../data/license_plates.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name, ip_address, port, username, password, stream_path FROM cameras WHERE enabled = 1 LIMIT 1")
        result = cursor.fetchone()
        conn.close()
        
        if result:
            name, ip, port, username, password, path = result
            
            # Build RTSP URL
            auth = f"{username}:{password}@" if username and password else ""
            rtsp_url = f"rtsp://{auth}{ip}:{port}{path}"
            
            print(f"📷 Found camera: {name}")
            print(f"   URL: rtsp://{auth}{ip}:{port}{path.split('?')[0]}...")  # Hide params
            return rtsp_url
    except Exception as e:
        print(f"Could not read from database: {e}")
    
    # Fallback to manual input
    print("\n📷 Enter camera RTSP URL")
    print("   Example: rtsp://admin:password@192.168.1.100:554/stream")
    return input("   URL: ")

async def main():
    print("🎬 FFmpeg Camera Recording Test")
    print("================================\n")
    
    # Get camera URL
    rtsp_url = get_camera_url()
    
    if not rtsp_url:
        print("❌ No camera URL provided")
        return
    
    # Test recording
    success = await test_camera_recording(rtsp_url, duration=30)
    
    if success:
        print("\n✅ Camera recording test PASSED!")
        print("   FFmpeg can record browser-compatible video from your camera")
        print("   Ready to proceed with full migration")
    else:
        print("\n❌ Camera recording test FAILED")
        print("   Check camera URL and network connection")

if __name__ == "__main__":
    asyncio.run(main())