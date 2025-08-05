# Test Directory

This directory contains all testing files and resources for the License Plate Recognition (LPR) system.

## Directory Structure

```
test/
├── unit/           # Unit tests for individual components
├── integration/    # Integration tests for system components
├── html/          # HTML test files and prototypes
├── media/         # Test media files (videos, images)
├── scripts/       # Test scripts and utilities
└── README.md      # This file
```

## Unit Tests

### Core Tests
- `test_imports.py` - Verify all dependencies are properly installed
- `test_database.py` - Database operations and CRUD functionality  
- `test_api.py` - API endpoint testing
- `test_ai.py` - AI detection pipeline testing
- `test_camera.py` - Camera connection and snapshot testing

### Camera Tests
- `test_camera_fixed.py` - Test camera with working configuration
- `test_camera_recording.py` - FFmpeg recording from real camera
- `test_hikvision_streams.py` - Hikvision-specific stream testing

### Utility Tests
- `diagnose_camera.py` - Comprehensive camera diagnostics tool
- `find_rtsp_url.py` - RTSP URL discovery utility
- `full_test.py` - Complete system integration test

## HTML Test Files

- `test_video.html` - Video playback testing
- `test_video_playback.html` - Advanced video playback controls
- `test_recording_playback.html` - Recording system playback testing
- `test_today_recording.html` - Today's recordings viewer

## Media Files

Test media files for video playback, camera testing, and format validation:
- Various MP4 test files with different formats and durations
- Test images for image processing validation
- Debug recordings for troubleshooting

## Running Tests

### Prerequisites
Make sure the project dependencies are installed and services are running:

```bash
# Install dependencies
pip install -r requirements.txt

# Start services (from project root)
python3 start_lpr.py
```

### Individual Test Execution

```bash
# Run from project root directory
cd /path/to/plate_recognition

# Test imports and dependencies
python3 test/unit/test_imports.py

# Test database operations
python3 test/unit/test_database.py

# Test API endpoints
python3 test/unit/test_api.py

# Test AI pipeline
python3 test/unit/test_ai.py

# Test camera connections
python3 test/unit/test_camera.py

# Run camera diagnostics
python3 test/unit/diagnose_camera.py 192.168.1.100 -u admin -P password
```

### HTML Tests
Open HTML files in browser:
- Navigate to `http://localhost:8080/test/html/[filename].html`
- Or open files directly in browser from file system

## Test Data Paths

Tests use relative paths from the test directory:
- Database: `../data/license_plates.db`  
- Models: `../ai_pipeline/train/models/pretrained/`
- Recordings: `../recordings/`

## Notes

- All Python tests include proper import path handling for project modules
- Database tests create separate test databases to avoid affecting production data
- Media files are used for format validation and playback testing
- HTML tests can be run independently or through the main frontend server