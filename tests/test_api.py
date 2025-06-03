from fastapi.testclient import TestClient
from app.main import app
from app.dependencies.detection import get_detection_service

class DummyDetectionService:
    detections_processed = 0
    last_detection_time = 0

    async def detect_from_camera(self):
        return {"plate_text": "TEST123", "confidence": 0.9}

    async def process_detection(self, detection_id: str, detection_result):
        self.detections_processed += 1

    async def get_latest_detections(self):
        return [{"plate_text": "TEST123"}]

dummy_service = DummyDetectionService()
app.dependency_overrides[get_detection_service] = lambda: dummy_service

client = TestClient(app)


def test_detection_status():
    response = client.get("/detection/status")
    assert response.status_code == 200
    assert response.json()["status"] == "running"

