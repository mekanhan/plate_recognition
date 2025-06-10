from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import cv2
import asyncio
import time
import uuid
from typing import Dict, List, Any
from app.services.camera_service import CameraService
from app.services.detection_service import DetectionService
import logging

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# This will be initialized in the main app
camera_service = None
detection_service = None
video_recording_service = None

# License plate tracking for deduplication
plate_tracker = {
    "last_seen": {},       # Maps plate text to last seen timestamp
    "cooldown_period": 5.0, # Only store the same plate again after 5 seconds
    "confidence_threshold": 0.5, # Minimum confidence to store a plate
    "last_process_time": 0, # Last time we processed the queue
    "process_interval": 2.0, # Process queue every 2 seconds
    "detection_queue": [],   # Queue of detections waiting to be processed
    "processing_lock": asyncio.Lock()  # Lock to prevent concurrent processing
}

# Frame processing control
frame_processor = {
    "frame_count": 0,
    "process_every_n_frames": 5,  # Only process every Nth frame - increased from 3 to 5
    "last_frame_time": 0,
    "processing_time_ms": 0,
    "total_detections": 0,  # Track total detections in session
    "session_start_time": time.time()
}

async def get_camera_service():
    """Dependency to get the camera service"""
    return camera_service

async def get_detection_service():
    """Dependency to get the detection service"""
    return detection_service

async def process_detection_queue():
    """Process any pending detections in the queue"""
    global plate_tracker

    current_time = time.time()

    # Only process if enough time has passed since last processing
    if current_time - plate_tracker["last_process_time"] < plate_tracker["process_interval"]:
        return

    # Try to acquire the lock, but don't block if already processing
    if plate_tracker["processing_lock"].locked():
        return  # Skip if already processing

    async with plate_tracker["processing_lock"]:
        # Update last process time
        plate_tracker["last_process_time"] = current_time

        # Get the current queue and clear it
        queue = plate_tracker["detection_queue"].copy()
        plate_tracker["detection_queue"] = []

        if not queue:
            return

        logger.info(f"Processing {len(queue)} detections from queue")

        # Group by plate text to find the best confidence for each plate
        plates_to_process = {}
        for detection in queue:
            plate_text = detection.get("plate_text", "").upper()
            if not plate_text:
                continue

            # Check if this is a better detection than what we already have
            current_confidence = detection.get("confidence", 0)
            if (plate_text not in plates_to_process or
                current_confidence > plates_to_process[plate_text].get("confidence", 0)):
                plates_to_process[plate_text] = detection

        # Process each unique plate (best confidence version)
        for plate_text, detection in plates_to_process.items():
            # Skip low confidence detections
            confidence = detection.get("confidence", 0)
            if confidence < plate_tracker["confidence_threshold"]:
                logger.debug(f"Skipping low confidence detection: {plate_text} ({confidence:.2f})")
                continue

            # Check cooldown period
            last_seen = plate_tracker["last_seen"].get(plate_text, 0)
            if current_time - last_seen < plate_tracker["cooldown_period"]:
                logger.debug(f"Skipping plate in cooldown: {plate_text}")
                continue

            # Update last seen time
            plate_tracker["last_seen"][plate_text] = current_time

            # Process this detection (which also saves it to storage)
            if detection_service:
                try:
                    detection_id = str(uuid.uuid4())
                    logger.info(f"Processing plate: {plate_text} (Confidence: {confidence:.2f})")

                    # Create a background task for processing to avoid blocking
                    asyncio.create_task(detection_service.process_detection(detection_id, detection))
                except Exception as e:
                    logger.error(f"Error processing detection: {e}")

async def generate_frames(camera: CameraService, detection_svc=None):
    """Generate video frames for streaming with license plate detection"""
    global frame_processor

    while True:
        try:
            start_time = time.time()

            # Get raw frame from camera
            raw_frame, timestamp = await camera.get_frame()

            # Default to raw frame
            frame = raw_frame
            annotated_frame = None

            # Increment frame counter
            frame_processor["frame_count"] += 1

            # Only process every Nth frame to improve performance
            should_process = frame_processor["frame_count"] % frame_processor["process_every_n_frames"] == 0

            if detection_svc and should_process:
                try:
                    # Process frame with license plate detection
                    process_task = asyncio.create_task(detection_svc.process_frame(raw_frame))
                    
                    # Set a timeout to avoid blocking for too long
                    try:
                        processed_frame, detections = await asyncio.wait_for(process_task, timeout=0.5)
                        
                        # Use the processed frame (with annotations)
                        frame = processed_frame
                        annotated_frame = processed_frame  # Save annotated frame for video recording
                        
                        # Add valid detections to the queue
                        if detections:
                            for detection in detections:
                                if detection.get("plate_text") and detection.get("confidence", 0) > 0:
                                    # Add timestamp if not present
                                    if "timestamp" not in detection:
                                        detection["timestamp"] = time.time()
                                    
                                    # Add to queue
                                    plate_tracker["detection_queue"].append(detection)
                                    
                                    # Increment detection counter
                                    frame_processor["total_detections"] += 1
                        
                        # Process the detection queue in a separate task (non-blocking)
                        asyncio.create_task(process_detection_queue())
                        
                    except asyncio.TimeoutError:
                        logger.warning("Frame processing timed out - using raw frame")
                        # Already using raw_frame as default
                    
                    # Calculate processing time
                    frame_processor["processing_time_ms"] = (time.time() - start_time) * 1000
                    
                except Exception as e:
                    logger.error(f"Error in license plate detection: {e}")
                    # Fall back to the original frame if detection fails
                    # Already using raw_frame as default

            # Send frame to video recording service
            # Use annotated frame if available, otherwise use raw frame
            frame_for_video = annotated_frame if annotated_frame is not None else raw_frame
            
            if video_recording_service:
                try:
                    await video_recording_service.add_frame(frame_for_video, timestamp)
                except Exception as e:
                    logger.error(f"Error adding frame to video recording: {e}")

            # Add timestamp overlay (always visible)
            import datetime
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Include milliseconds
            cv2.putText(frame, current_time, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Add system info overlay
            session_duration = time.time() - frame_processor["session_start_time"]
            hours = int(session_duration // 3600)
            minutes = int((session_duration % 3600) // 60)
            seconds = int(session_duration % 60)
            
            system_info = f"LPR System | Frame: {frame_processor['frame_count']} | Detections: {frame_processor['total_detections']}"
            cv2.putText(frame, system_info, (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Add session uptime
            uptime_info = f"Session: {hours:02d}:{minutes:02d}:{seconds:02d}"
            cv2.putText(frame, uptime_info, (10, 85),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

            # Add performance metrics to the frame
            if should_process:
                # Add processing time
                processing_time = frame_processor["processing_time_ms"]
                perf_text = f"Processing: {processing_time:.1f}ms"
                cv2.putText(frame, perf_text, (10, frame.shape[0] - 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

                # Add frame processing info
                fps_info = f"Process Rate: Every {frame_processor['process_every_n_frames']} frames"
                cv2.putText(frame, fps_info, (10, frame.shape[0] - 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

            # Convert the frame to JPEG
            success, jpeg_buffer = cv2.imencode('.jpg', frame)
            jpeg_bytes = jpeg_buffer.tobytes()

            # Yield the frame in multipart format
            frame_data = b'--frame\r\n'
            frame_data += b'Content-Type: image/jpeg\r\n\r\n'
            frame_data += jpeg_bytes
            frame_data += b'\r\n'
            yield frame_data

            # Calculate frame processing time for metrics
            frame_time = time.time() - start_time
            frame_processor["last_frame_time"] = frame_time

            # Adaptive sleep to maintain target frame rate
            target_frame_time = 0.03  # ~30 fps
            sleep_time = max(0.001, target_frame_time - frame_time)
            await asyncio.sleep(sleep_time)

        except Exception as e:
            logger.error(f"Error in frame generation: {e}")
            await asyncio.sleep(0.1)  # Wait a bit longer on error

@router.get("/", response_class=HTMLResponse)
async def stream_page(request: Request):
    """Stream page"""
    return templates.TemplateResponse("stream.html", {"request": request})

@router.get("/video")
async def video_feed(
    camera: CameraService = Depends(get_camera_service),
    detection_svc = Depends(get_detection_service)
):
    """Video streaming endpoint with license plate detection"""
    return StreamingResponse(
        generate_frames(camera, detection_svc),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )