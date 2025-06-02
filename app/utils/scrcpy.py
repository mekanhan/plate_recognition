import subprocess
import os

def start_scrcpy():
    """Start scrcpy for Android screen streaming and record to temp MP4 file"""
    # Create a temporary file for recording the stream
    temp_file = os.path.join(os.getcwd(), "temp_stream.mp4")

    print(f"Starting scrcpy and recording stream to {temp_file}...")

    # Start scrcpy and record to temp file
    subprocess.Popen(["scrcpy", "--record", temp_file])

    # Return the path to the recorded file for OpenCV to read
    return temp_file
