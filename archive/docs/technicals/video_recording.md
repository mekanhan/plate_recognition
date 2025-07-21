# Video Recording System

**Version:** 1.0
**Last Updated:** 2023-07-20

## Overview

This document describes the video recording functionality implemented in the License Plate Recognition System. The system automatically records video clips when license plates are detected, capturing both pre-event and post-event footage.

## Recording Architecture

### Key Components

- **VideoRecorder**: Low-level class that handles frame buffering and video writing
- **VideoRecordingService**: High-level service that coordinates recording with detection events and manages metadata

### Recording Process

1. The system maintains a rolling buffer of recent frames (default: 5 seconds)
2. When a license plate is detected with sufficient confidence, recording is triggered
3. Pre-event buffer frames are written to the video file first
4. Recording continues for a set duration after the last detection (default: 15 seconds)
5. Video metadata is stored in the database for future reference and retrieval

## Implementation Details

### VideoRecorder Class

The `VideoRecorder` class handles the core recording functionality:

```python
class VideoRecorder:
    """Low-level class for recording video frames"""
    
    def __init__(self, buffer_seconds: int = 5, post_event_seconds: int = 15, fps: int = 15):
        self.frame_buffer = []
        self.buffer_seconds = buffer_seconds
        self.post_event_seconds = post_event_seconds
        self.fps = fps
        self.buffer_frames = self.buffer_seconds * self.fps
        
        # Recording state
        self.recording = False
        self.current_output = None
        self.current_video_path = None
        self.post_event_frames = 0
        
        # Performance monitoring
        self.frames_written = 0
        self.recording_start_time = None
```

#### Key Methods

- **add_frame()**: Adds a frame to the rolling buffer and recording
- **start_recording()**: Starts recording to a specified path
- **stop_recording()**: Stops the current recording

### VideoRecordingService Class

The `VideoRecordingService` class provides a higher-level interface:

```python
class VideoRecordingService:
    """Service for managing video recording of license plate detections"""
    
    def __init__(self, detection_repository, video_repository):
        self.detection_repository = detection_repository
        self.video_repository = video_repository
        
        # Create recorder
        self.recorder = VideoRecorder(buffer_seconds=5, post_event_seconds=15, fps=15)
        
        # Recording state
        self.current_segment_id = None
        self.current_detection_ids = []
        self.last_frame_time = None
        
        # Ensure video directory exists
        self.base_video_dir = "data/videos"
        os.makedirs(self.base_video_dir, exist_ok=True)
```

#### Key Methods

- **add_frame()**: Adds a frame to the recorder
- **trigger_recording()**: Starts recording based on a detection event
- **stop_recording()**: Stops the current recording and updates metadata
- **cleanup_old_videos()**: Archives and deletes old video recordings

## Configuration Options

### Recording Parameters

| Parameter         | Default Value | Description                                     |
|-------------------|---------------|-------------------------------------------------|
| buffer_seconds    | 5             | Seconds of footage to keep in pre-event buffer  |
| post_event_seconds| 15            | Seconds to continue recording after detection   |
| fps               | 15            | Frames per second for recorded video            |

### Video Quality

| Parameter         | Value         | Description                                     |
|-------------------|---------------|-------------------------------------------------|
| codec             | mp4v          | Video codec (MPEG-4)                            |
| container         | mp4           | Video container format                          |
| resolution        | Camera native | Matches input camera resolution                 |

## Storage Structure

### Directory Organization

Videos are stored in date-based directories:
For example:
/data /videos /2023-07-20 /550e8400-e29b-41d4-a716-446655440000_1689765432.mp4


### Metadata Storage

Video metadata is stored in the `video_segments` table in the database:

- **id**: Unique identifier (UUID)
- **file_path**: Path to the video file
- **start_time**: Recording start timestamp
- **end_time**: Recording end timestamp
- **duration_seconds**: Duration in seconds
- **file_size_bytes**: File size in bytes
- **resolution**: Video resolution (e.g., "1280x720")
- **archived**: Whether video is archived
- **detection_ids**: Comma-separated list of detection IDs in this video

## Retention Policy

By default, videos are kept for 30 days. The cleanup process:

1. Marks videos older than the retention period as "archived" in the database
2. Physically deletes archived video files to free up disk space

```python
async def cleanup_old_videos(self, retention_days: int = 30) -> int:
    """Clean up old video recordings"""
    # Mark old videos as archived in database
    archived_count = await self.video_repository.cleanup_old_videos(days=retention_days)
    
    # Get list of archived videos and delete the files
    # ...
    
    return archived_count

Integration with Detection Service
The video recording service is integrated with the detection service:

# In detection_service_v2.py
async def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    # ...
    
    # Process frames for video recording if service is available
    if self.video_recording_service:
        # Always add frame to the buffer
        await self.video_recording_service.add_frame(frame, time.time())
        
        # If we have a good detection, trigger recording
        if valid_detections:
            # Find the best detection based on confidence
            best_detection = max(valid_detections, key=lambda d: d.get("confidence", 0))
            if best_detection.get("confidence", 0) > 0.5:  # Higher threshold for recording
                await self.video_recording_service.trigger_recording(
                    best_detection.get("detection_id"))
    
    # ...

API Integration
The system provides API endpoints for video management:

GET /v2/video/segments: List video segments with pagination
GET /v2/video/segments/{id}: Get video segment details
GET /v2/video/segments/{id}/download: Download video file
GET /v2/video/by-detection/{id}: Get videos for a detection
POST /v2/video/cleanup: Clean up old videos
GET /v2/video/stats: Get video statistics
Performance Considerations
Storage Requirements
For a medium-sized apartment complex:

Event-Based Recording (recommended):
~740MB per day (100 events × 20 seconds each at 1080p/15fps/3Mbps)
~22GB for 30-day retention
Optimization Techniques
Hardware Acceleration: Use GPU acceleration for video encoding when available
Downscaling: Consider reducing resolution for storage
Compression: Use efficient codecs (H.264/H.265)
Frame Rate Reduction: Lower fps for storage vs. analysis
Troubleshooting
Common Issues
Issue	Possible Causes	Solutions
No videos being recorded	Insufficient detection confidence	Lower confidence threshold
Storage directory not writable	Check permissions on video directory
OpenCV video writer failure	Ensure codec is installed
Corrupted video files	Process terminated during recording	Implement recovery for incomplete recordings
Missing video files	Mismatched database records and files	Run consistency check to reconcile data