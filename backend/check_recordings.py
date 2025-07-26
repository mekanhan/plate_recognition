"""
Check recording database
"""
import sqlite3
from datetime import datetime

db_path = "recordings/camera_3/index.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all segments
cursor.execute("SELECT * FROM segments ORDER BY start_time DESC")
segments = cursor.fetchall()

print(f"Total segments: {len(segments)}")
print("\nRecorded segments:")
print("-" * 80)

for segment in segments:
    id, filename, start_time, end_time, duration, frame_count, file_size, created_at = segment
    start_dt = datetime.fromisoformat(start_time)
    end_dt = datetime.fromisoformat(end_time)
    
    print(f"ID: {id}")
    print(f"Filename: {filename}")
    print(f"Start: {start_dt}")
    print(f"End: {end_dt}")
    print(f"Duration: {duration} seconds")
    print(f"File size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
    print("-" * 80)

conn.close()