# test_db.py
import sqlite3
import os

# Check if database file exists
db_path = "data/license_plates.db"
if not os.path.exists(db_path):
    print(f"Database file not found at {db_path}")
    exit(1)

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables in database:")
for table in tables:
    print(f"- {table[0]}")

# Check schema for specific tables if they exist
table_names = [table[0] for table in tables]

if "detections" in table_names:
    print("\nSchema for 'detections' table:")
    cursor.execute("PRAGMA table_info(detections);")
    columns = cursor.fetchall()
    for column in columns:
        print(f"- {column[1]} ({column[2]})")

if "video_segments" in table_names:
    print("\nSchema for 'video_segments' table:")
    cursor.execute("PRAGMA table_info(video_segments);")
    columns = cursor.fetchall()
    for column in columns:
        print(f"- {column[1]} ({column[2]})")

# Check for any records
if "video_segments" in table_names:
    cursor.execute("SELECT COUNT(*) FROM video_segments;")
    count = cursor.fetchone()[0]
    print(f"\nNumber of video segments: {count}")
    
    if count > 0:
        cursor.execute("SELECT id, file_path, start_time, duration_seconds FROM video_segments LIMIT 5;")
        videos = cursor.fetchall()
        print("\nSample video segments:")
        for video in videos:
            print(f"- ID: {video[0]}, Path: {video[1]}, Start: {video[2]}, Duration: {video[3]}s")

# Close connection
conn.close()