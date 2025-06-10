# check_videos.py
import os
import datetime

VIDEO_DIR = "data/videos"

# Check if base directory exists
if not os.path.exists(VIDEO_DIR):
    print(f"Video directory not found: {VIDEO_DIR}")
    exit(1)

# List date subdirectories
date_dirs = [d for d in os.listdir(VIDEO_DIR) if os.path.isdir(os.path.join(VIDEO_DIR, d))]
print(f"Date directories: {date_dirs}")

# Get today's directory
today = datetime.datetime.now().strftime("%Y-%m-%d")
today_dir = os.path.join(VIDEO_DIR, today)

if today in date_dirs and os.path.exists(today_dir):
    # List video files in today's directory
    video_files = [f for f in os.listdir(today_dir) if f.endswith('.mp4')]
    print(f"\nFound {len(video_files)} videos for today ({today}):")
    
    for video_file in video_files:
        file_path = os.path.join(today_dir, video_file)
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # Convert to MB
        print(f"- {video_file} ({file_size:.2f} MB)")
else:
    print(f"\nNo videos found for today ({today})")

# Count total videos
total_videos = 0
total_size_mb = 0

for date_dir in date_dirs:
    dir_path = os.path.join(VIDEO_DIR, date_dir)
    video_files = [f for f in os.listdir(dir_path) if f.endswith('.mp4')]
    total_videos += len(video_files)
    
    for video_file in video_files:
        file_path = os.path.join(dir_path, video_file)
        total_size_mb += os.path.getsize(file_path) / (1024 * 1024)

print(f"\nTotal videos: {total_videos}")
print(f"Total size: {total_size_mb:.2f} MB")