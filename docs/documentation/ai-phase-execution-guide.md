# AI Agent Phase Execution Guide - Step by Step

## 🎯 YOUR MISSION

Build a License Plate Recognition system following these phases IN ORDER. Do NOT skip ahead.

**Repository**: https://github.com/mekanhan/plate_recognition/tree/clean-architecture

## 📚 PHASE 0: MANDATORY READING (30 minutes)

**DO NOT WRITE ANY CODE YET!**

### Read these documents in `docs/documentation/` IN THIS ORDER:

1. ✅ **READ**: `01-overview-architecture.md` - Understand why no browser streaming
2. ✅ **READ**: `02-camera-integration.md` - Learn camera capture approach  
3. ✅ **READ**: `03-ai-processing-pipeline.md` - Understand AI pipeline
4. ✅ **READ**: `08-troubleshooting-faq.md` - Learn common mistakes

### Checkpoint Questions (Answer before proceeding):
- [ ] Why can't we stream RTSP to browsers?
- [ ] What should browsers display instead of video?
- [ ] Where should video processing happen?
- [ ] What tool should be used for live viewing?

**If you can't answer these, RE-READ THE DOCUMENTATION!**

---

## 🔨 PHASE 1: PROJECT SETUP (Day 1)

### Step 1.1: Verify Structure
```bash
# You should see:
plate_recognition/
├── frontend/          # EXISTS - DO NOT DELETE
├── docs/             # EXISTS - Contains documentation
│   └── documentation/  # YOUR GUIDES ARE HERE
├── ai_pipeline/      # CREATE THIS
├── database/         # CREATE THIS
├── api/             # CREATE THIS
└── deployment/      # CREATE THIS
```

### Step 1.2: Create requirements.txt
Copy EXACTLY from `docs/documentation/ai-agent-instructions.md` Step 1

### Step 1.3: Setup Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Step 1.4: Create __init__.py files
```bash
touch ai_pipeline/__init__.py
touch database/__init__.py
touch api/__init__.py
```

### ✅ Phase 1 Checklist:
- [ ] Folder structure created
- [ ] requirements.txt created and installed
- [ ] Virtual environment working
- [ ] Can import cv2, fastapi, ultralytics

**STOP! Do not proceed until ALL boxes checked.**

---

## 💻 PHASE 2: CAMERA INTEGRATION (Day 2)

### Step 2.1: Create Camera Manager
1. Copy code from `docs/documentation/02-camera-integration.md`
2. Create `ai_pipeline/camera_manager.py`
3. DO NOT modify for browser streaming!

### Step 2.2: Test Camera Connection
Create `test_camera.py`:
```python
from ai_pipeline.camera_manager import CameraManager, CameraConfig

# Test with ONE camera first
config = CameraConfig(
    camera_id="test1",
    name="Test Camera",
    ip_address="YOUR_CAMERA_IP",  # Update this!
    username="admin",
    password="password"
)

manager = CameraManager()
manager.add_camera(config)

# Wait 5 seconds
import time
time.sleep(5)

# Get frame
camera = manager.get_camera("test1")
frame = camera.get_snapshot()

if frame is not None:
    print("✅ Camera working!")
    import cv2
    cv2.imwrite("test_snapshot.jpg", frame)
else:
    print("❌ Camera not working - check IP/credentials")

manager.stop_all()
```

### Step 2.3: Verify with VLC
```bash
# Test same URL in VLC
vlc rtsp://username:password@YOUR_CAMERA_IP:554/stream
```

### ✅ Phase 2 Checklist:
- [ ] camera_manager.py created
- [ ] Test script captures frame
- [ ] test_snapshot.jpg shows camera view
- [ ] VLC can open camera stream

**STOP! Fix camera connection before proceeding.**

---

## 🤖 PHASE 3: AI DETECTION (Day 3)

### Step 3.1: Download YOLO Model
```python
# download_model.py
from ultralytics import YOLO

# This downloads the model
model = YOLO('yolov8m.pt')
print("Model downloaded!")
```

### Step 3.2: Create AI Processor
1. Copy code from `docs/documentation/03-ai-processing-pipeline.md`
2. Create `ai_pipeline/processors.py`
3. For initial testing, use vehicle detection as placeholder for plates

### Step 3.3: Test Detection
Create `test_detection.py`:
```python
from ai_pipeline.processors import LicensePlateDetector
import cv2

detector = LicensePlateDetector()

# Use your test snapshot
frame = cv2.imread("test_snapshot.jpg")

# Detect vehicles
vehicles = detector.detect_vehicles(frame)
print(f"Found {len(vehicles)} vehicles")

# Draw boxes
for v in vehicles:
    x1, y1, x2, y2 = v['bbox']
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

cv2.imwrite("test_detection.jpg", frame)
print("Check test_detection.jpg for results")
```

### ✅ Phase 3 Checklist:
- [ ] YOLO model downloaded
- [ ] processors.py created
- [ ] Vehicles detected in test image
- [ ] Boxes drawn on test_detection.jpg

---

## 🗄️ PHASE 4: DATABASE SETUP (Day 4)

### Step 4.1: Start PostgreSQL
```bash
# Use Docker
docker run -d \
  --name lpr_postgres \
  -e POSTGRES_USER=lpr_user \
  -e POSTGRES_PASSWORD=lpr_password \
  -e POSTGRES_DB=lpr_db \
  -p 5432:5432 \
  postgres:15-alpine
```

### Step 4.2: Create Models
1. Copy code from `docs/documentation/04-database-design.md`
2. Create `database/models.py`

### Step 4.3: Test Database Connection
Create `test_db.py`:
```python
from sqlalchemy import create_engine
from database.models import Base

engine = create_engine("postgresql://lpr_user:lpr_password@localhost:5432/lpr_db")

# Create tables
Base.metadata.create_all(engine)
print("✅ Database tables created!")
```

### ✅ Phase 4 Checklist:
- [ ] PostgreSQL running
- [ ] Can connect to database
- [ ] Tables created successfully

---

## 🌐 PHASE 5: API BACKEND (Day 5)

### Step 5.1: Create FastAPI App
1. Copy code from `api/main.py` in instructions
2. Create the file with ALL endpoints

### Step 5.2: Test API
```bash
# Terminal 1: Run API
uvicorn api.main:app --reload

# Terminal 2: Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/cameras
```

### Step 5.3: Test Snapshot Endpoint
Open browser: http://localhost:8000/api/cameras/test1/snapshot

### ✅ Phase 5 Checklist:
- [ ] API starts without errors
- [ ] /health returns {"status": "healthy"}
- [ ] /api/cameras shows your camera
- [ ] Snapshot endpoint shows image

---

## 🎨 PHASE 6: FRONTEND INTEGRATION (Day 6)

### Step 6.1: Update Frontend Config
Edit `frontend/src/config/api.js`:
```javascript
export const API_BASE_URL = 'http://localhost:8000';

// Remove ANY video streaming endpoints!
export const endpoints = {
  cameras: '/api/cameras',
  snapshot: '/api/cameras/{id}/snapshot',
  detections: '/api/detections/recent',
  vlc: '/api/cameras/{id}/open-vlc'
};
```

### Step 6.2: Update Camera Component
Replace video elements with snapshot images as shown in instructions

### Step 6.3: Test Frontend
```bash
cd frontend
npm install
npm start
```

### ✅ Phase 6 Checklist:
- [ ] Frontend connects to backend
- [ ] Camera snapshots display
- [ ] Snapshots refresh every 5 seconds
- [ ] NO <video> elements in code
- [ ] VLC button works

---

## 🚀 PHASE 7: FULL INTEGRATION (Day 7)

### Step 7.1: Run Everything
```bash
# Terminal 1: Database
docker-compose up postgres redis

# Terminal 2: Backend
python -m uvicorn api.main:app --reload

# Terminal 3: Frontend
cd frontend && npm start
```

### Step 7.2: Final Tests
1. Open http://localhost:3000
2. Verify camera snapshots update
3. Click "View in VLC" - should show RTSP URL
4. Check console for detection logs

### ✅ Phase 7 Checklist:
- [ ] All services running
- [ ] Cameras show snapshots
- [ ] Detections logged in console
- [ ] VLC can open streams
- [ ] No browser streaming errors

---

## 🎯 SUCCESS CRITERIA

You have succeeded when:

1. ✅ **Cameras**: Snapshots display in browser (updating every 5s)
2. ✅ **AI**: License plates detected and logged
3. ✅ **Database**: Detections saved
4. ✅ **Live View**: VLC opens camera streams
5. ✅ **NO BROWSER VIDEO**: No <video> tags, no streaming attempts

---

## ⚠️ CRITICAL REMINDERS

### NEVER:
- Add <video> elements to frontend
- Try to stream RTSP to browser
- Use WebRTC, HLS, or any browser streaming
- Process video over internet

### ALWAYS:
- Display snapshots in browser
- Process video locally
- Use VLC for live viewing
- Read documentation when stuck

---

## 🆘 IF STUCK

1. **First**: Re-read relevant documentation
2. **Second**: Check Phase Checklist - did you miss a step?
3. **Third**: Consult `08-troubleshooting-faq.md`
4. **Fourth**: Verify you're not trying browser streaming

Remember: The architecture is proven. Follow it exactly. Do not "improve" with browser streaming.

---

**FINAL INSTRUCTION**: Complete phases in order. Each phase builds on the previous. Do not skip steps. Test everything before moving on.