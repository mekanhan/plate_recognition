"""
Shared pytest fixtures and configuration for all tests
"""
import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Test environment setup
os.environ['TESTING'] = 'true'
os.environ['JWT_SECRET_KEY'] = 'test_secret_key_for_testing_only'

# ================== Common Fixtures ==================

@pytest.fixture(scope='session')
def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope='function')
def temp_dir():
    """Create a temporary directory for test files"""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path, ignore_errors=True)

@pytest.fixture(scope='function')
def test_image_path():
    """Path to a test image for testing"""
    # Create a simple test image
    import numpy as np
    import cv2
    
    temp_path = tempfile.mktemp(suffix='.jpg')
    test_image = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(test_image, "TEST123", (200, 240), 
                cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
    cv2.imwrite(temp_path, test_image)
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)

# ================== Database Fixtures ==================

@pytest.fixture(scope='function')
async def test_db():
    """Create a test database for testing"""
    from database.service import DatabaseService
    
    # Use in-memory database for tests
    db_service = DatabaseService("sqlite+aiosqlite:///:memory:")
    await db_service.init_db()
    
    yield db_service
    
    await db_service.close()

@pytest.fixture(scope='function')
async def sample_camera_data():
    """Sample camera data for testing"""
    return {
        'camera_id': 'test_camera_001',
        'name': 'Test Camera',
        'ip_address': '192.168.1.100',
        'port': 554,
        'connection_type': 'rtsp',
        'stream_path': '/stream1',
        'username': 'admin',
        'password': 'password',
        'status': 'active'
    }

@pytest.fixture(scope='function')
async def sample_detection_data():
    """Sample detection data for testing"""
    return {
        'camera_id': 'test_camera_001',
        'plate_text': 'ABC1234',
        'confidence': 0.95,
        'vehicle_type': 'car',
        'detected_at': datetime.now(),
        'vehicle_bbox': [100, 100, 300, 300],
        'plate_bbox': [150, 150, 250, 200],
        'ocr_confidence': 0.92,
        'is_best_shot': True
    }

# ================== API Fixtures ==================

@pytest.fixture(scope='function')
def api_client():
    """Create FastAPI test client"""
    from fastapi.testclient import TestClient
    from api.main import app
    
    client = TestClient(app)
    return client

@pytest.fixture(scope='function')
def auth_headers():
    """Generate authentication headers for API tests"""
    from auth.auth_service import AuthService
    
    auth_service = AuthService()
    token = auth_service.create_access_token(
        data={"sub": "test_user", "role": "admin"}
    )
    
    return {"Authorization": f"Bearer {token}"}

# ================== Mock Fixtures ==================

@pytest.fixture(scope='function')
def mock_camera_stream(monkeypatch):
    """Mock camera stream for testing without hardware"""
    def mock_read():
        import numpy as np
        # Return a dummy frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        return True, frame
    
    import cv2
    monkeypatch.setattr(cv2.VideoCapture, 'read', lambda self: mock_read())
    monkeypatch.setattr(cv2.VideoCapture, 'isOpened', lambda self: True)
    monkeypatch.setattr(cv2.VideoCapture, 'release', lambda self: None)

@pytest.fixture(scope='function')
def mock_yolo_model(monkeypatch):
    """Mock YOLO model for testing without loading actual weights"""
    class MockYOLO:
        def __init__(self, *args, **kwargs):
            pass
        
        def predict(self, *args, **kwargs):
            # Return mock detection results
            class MockResult:
                def __init__(self):
                    self.boxes = type('obj', (object,), {
                        'data': [[100, 100, 300, 300, 0.95, 0]],
                        'xyxy': [[100, 100, 300, 300]],
                        'conf': [0.95],
                        'cls': [0]
                    })()
            return [MockResult()]
    
    import sys
    if 'ultralytics' in sys.modules:
        monkeypatch.setattr('ultralytics.YOLO', MockYOLO)

# ================== Performance Fixtures ==================

@pytest.fixture(scope='function')
def benchmark_timer():
    """Simple benchmark timer for performance tests"""
    import time
    
    class Timer:
        def __init__(self):
            self.times = []
        
        def start(self):
            self.start_time = time.perf_counter()
        
        def stop(self):
            elapsed = time.perf_counter() - self.start_time
            self.times.append(elapsed)
            return elapsed
        
        def average(self):
            return sum(self.times) / len(self.times) if self.times else 0
        
        def report(self):
            if self.times:
                return {
                    'min': min(self.times),
                    'max': max(self.times),
                    'avg': self.average(),
                    'total': sum(self.times),
                    'count': len(self.times)
                }
            return {}
    
    return Timer()

# ================== Cleanup Fixtures ==================

@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Automatically cleanup test files after each test"""
    yield
    
    # Clean up any test files created
    test_patterns = [
        'test_*.jpg',
        'test_*.mp4',
        'test_*.db',
        'temp_*.log'
    ]
    
    for pattern in test_patterns:
        for file in Path('.').glob(pattern):
            try:
                file.unlink()
            except:
                pass

# ================== Markers Configuration ==================

def pytest_configure(config):
    """Configure custom markers"""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
    config.addinivalue_line(
        "markers", "requires_gpu: mark test as requiring GPU"
    )
    config.addinivalue_line(
        "markers", "requires_camera: mark test as requiring camera hardware"
    )