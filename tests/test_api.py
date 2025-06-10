# tests/test_api.py
from fastapi.testclient import TestClient
from app.main_v2 import app  # Import from main_v2 for v2 endpoints
from app.dependencies.detection import get_detection_service
from app.dependencies.services import get_video_recording_service

class DummyDetectionService:
    detections_processed = 0
    last_detection_time = 0

    async def detect_from_camera(self):
        return {"detection_id": "test-123", "plate_text": "TEST123", "confidence": 0.9}

    async def process_detection(self, detection_id: str, detection_result):
        self.detections_processed += 1

    async def get_latest_detections(self):
        return [{"detection_id": "test-123", "plate_text": "TEST123", "confidence": 0.9}]

class DummyVideoRecordingService:
    async def get_videos_for_detection(self, detection_id: str):
        return [{
            "id": "video-123",
            "file_path": "data/videos/2023-07-20/test-123_1689865432.mp4",
            "start_time": 1689865432.567,
            "end_time": 1689865452.123,
            "duration_seconds": 19.556,
            "file_size_bytes": 3145728,
            "resolution": "1280x720",
            "archived": False,
            "detection_ids": ["test-123"]
        }]

    async def cleanup_old_videos(self, retention_days: int = 30):
        return 5

dummy_detection_service = DummyDetectionService()
dummy_video_service = DummyVideoRecordingService()

app.dependency_overrides[get_detection_service] = lambda: dummy_detection_service
app.dependency_overrides[get_video_recording_service] = lambda: dummy_video_service

client = TestClient(app)

# Original API tests
def test_detection_status():
    response = client.get("/detection/status")
    assert response.status_code == 200
    assert response.json()["status"] == "running"

# New v2 API tests
def test_v2_detection_from_camera():
    response = client.post("/v2/detection/detect-from-camera")
    assert response.status_code == 200
    data = response.json()
    assert data["plate_text"] == "TEST123"
    assert data["confidence"] == 0.9

def test_v2_video_by_detection():
    response = client.get("/v2/video/by-detection/test-123")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert len(data["videos"]) == 1
    assert data["videos"][0]["id"] == "video-123"

def test_v2_video_cleanup():
    response = client.post("/v2/video/cleanup?retention_days=30")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["archived_count"] == 5