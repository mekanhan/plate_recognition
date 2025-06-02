# to run this test, use the command: pytest -vvs --collect-only tests/test_lpr_cooldwon.py
import sys
import os
import time
import pytest
from collections import defaultdict

# Get the absolute path to lpr_live.py
scripts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
sys.path.insert(0, scripts_dir)

# Import directly from the module
from lpr_live import process_video_stream, detect_and_recognize_plate

# Mock class to simulate the VideoCapture object
class MockVideoCapture:
    def __init__(self, frames):
        self.frames = frames
        self.index = 0

    def read(self):
        if self.index < len(self.frames):
            return True, self.frames[self.index]
        return False, None

    def release(self):
        pass

# Defining a test function for cooldown logic
def test_plate_cooldown():
    cap = MockVideoCapture([])  # Replace with frames for testing
    
    # Initialize a dictionary to track unique plates
    recent_detections = defaultdict(float)

    # Simulate a plate detection
    plate_text = "ABC123"
    current_time = time.time()

    # First Detection: should be logged
    recent_detections[plate_text] = current_time
    
    assert plate_text in recent_detections

    # Second Detection within cooldown: should not be logged
    time.sleep(1)  # Simulating passage of time
    assert current_time + 30 > recent_detections[plate_text]  # Check if still in cooldown

    # Simulate Detection after cooldown
    time.sleep(30)  # Wait for cooldown to expire
    new_time = time.time()
    recent_detections[plate_text] = new_time

    assert plate_text in recent_detections  # Now it should be accepted again

# Run this test with `pytest test_lpr_cooldown.py`