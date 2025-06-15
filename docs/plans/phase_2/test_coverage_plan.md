# Comprehensive Feature Analysis for Test Coverage

Below is the same content reformatted as a Markdown document.

---

## 1. API Endpoints

### Detection Router&nbsp;`/detection`

| Method | Endpoint            | Purpose                                         |
| ------ | ------------------- | ----------------------------------------------- |
| POST   | `/detect`           | Detect license plates from current camera frame |
| POST   | `/detect/upload`    | Detect license plates from uploaded image       |
| GET    | `/status`           | Get detection-service status & metrics          |
| GET    | `/test-storage`     | Test storage functionality with dummy detection |

### Stream Router&nbsp;`/stream`

| Method / Channel | Endpoint / Description                             | Purpose                                                  |
| ---------------- | -------------------------------------------------- | -------------------------------------------------------- |
| GET              | `/`                                                | Stream page (Web UI)                                     |
| GET              | `/video`                                           | Video-streaming endpoint with real-time detection        |
| WebSocket        | _live frame streaming_                             | Real-time license-plate detection overlay                |

### Results Router&nbsp;`/results`

| Method | Endpoint           | Purpose                                           |
| ------ | ------------------ | ------------------------------------------------- |
| GET    | `/latest`          | Latest detections (Web UI)                        |
| GET    | `/latest/json`     | Latest detections (JSON API)                      |
| GET    | `/all`             | All detections (Web UI)                           |
| GET    | `/all/json`        | All detections (JSON API)                         |
| GET    | `/enhanced`        | Enhanced detection results (Web UI)               |
| GET    | `/enhanced/json`   | Enhanced detection results (JSON API)             |
| GET    | `/health`          | Storage & database health check                   |
| GET    | `/detections`      | Advanced filtered search with pagination          |
| GET    | `/detections/export`| Export detections to CSV                          |
| GET    | `/database/json`   | Direct database-query endpoint                    |
| —      | _Debug endpoints_  | Search-testing utilities                          |

### System Router&nbsp;`/api/system`

| Method | Endpoint           | Purpose                                      |
| ------ | ------------------ | -------------------------------------------- |
| GET    | `/health`          | Comprehensive system-health metrics          |
| GET    | `/metrics`         | Detailed performance metrics                 |
| GET    | `/logs`            | System logs with filtering                   |
| GET    | `/config`          | Current system configuration                 |
| PUT    | `/config`          | Update system configuration                  |
| GET    | `/status`          | Overall system status                        |
| POST   | `/restart`         | Restart system components                    |
| GET    | `/activity/recent` | Recent system activity                       |

### Headless Router&nbsp;`/api/headless`

| Method / Verb | Endpoint / Control                           | Purpose                                   |
| ------------- | -------------------------------------------- | ----------------------------------------- |
| GET           | `/health`                                    | Headless-mode system health               |
| GET           | `/status`                                    | Background-processing status              |
| POST          | `/control/start|stop|pause|resume`           | Background-processing control             |
| GET           | `/detections/recent`                         | Recent detections from API buffer         |
| DELETE        | `/detections/clear`                          | Clear detection buffer                    |
| GET           | `/metrics`                                   | Performance metrics                       |
| PUT           | `/config`                                    | Runtime configuration updates             |
| GET           | `/info`                                      | System information & capabilities         |

### Video Router&nbsp;`/video`

| Method | Endpoint                             | Purpose                                   |
| ------ | ------------------------------------ | ----------------------------------------- |
| GET    | `/segments`                          | List video segments with pagination       |
| GET    | `/segments/{id}`                     | Get specific video-segment info           |
| GET    | `/segments/{id}/download`            | Download video segment                    |
| GET    | `/by-detection/{id}`                 | Get videos containing a specific detection|
| POST   | `/cleanup`                           | Clean up old video recordings             |
| GET    | `/stats`                             | Video-recording statistics                |

---

## 2. Web UI Features

### Main Dashboard `index.html`

- System-metrics display  
- Detection statistics  
- Real-time activity feed  
- Quick-navigation cards  
- System-status indicators  

### Live Stream `stream.html`

- Real-time video stream with annotations  
- Start/stop stream controls  
- Full-screen mode  
- Frame-capture functionality  
- Detection overlay & bounding boxes  
- Performance-metrics display  

### Results Pages `results.html`

- Detection results with search & filtering  
- Pagination controls  
- Export to CSV  
- Fuzzy search  
- Time-range filters (today, yesterday, last hour …)  
- Advanced filters (confidence, date range, time of day)  
- Real-time search with ranking  

### System Monitoring `system_monitoring.html`

- System-health dashboard  
- Performance charts  
- Resource-usage monitoring  
- Service-status indicators  

### System Configuration `system_config.html`

- Configuration-management interface  
- Real-time configuration updates  
- Validation & error handling  

### Detection Test `detection_test.html`

- Manual detection-testing interface  
- Image-upload & test functionality  

### Video Browser `video_browser.html`

- Video-segment browsing  
- Playback controls  
- Download functionality  

---

## 3. Core Services

| Service                | Key Responsibilities                                                                                 |
| ---------------------- | ----------------------------------------------------------------------------------------------------- |
| **Camera Service**     | Initialization (USB / RTSP / file) • Frame capture & buffering • Test-pattern generation • FPS/Res control • Error handling |
| **Detection Service**  | YOLO model init & inference • Real-time plate detection • Frame annotation • Metrics tracking • Background processing |
| **Storage Service**    | Dual storage (JSON + SQLite) • Session management • File organization & cleanup • Async saves • Retrieval & filtering |
| **Video Recording**    | Continuous recording • Rolling buffer • Segment creation • Detection-triggered clips • Cleanup & archival |
| **Enhancement Service**| Plate-image enhancement • OCR via EasyOCR • Text normalization/state detection • Confidence scoring   |
| **Background Stream**  | Headless processing • Queue management • Health monitoring • Error recovery                           |
| **Output Channel Mgr** | Multi-channel output (storage, API, WS, webhook) • Real-time distribution • Buffer & channel configs |

---

## 4. Database Operations

| Model  | Operations                                                                                           |
| ------ | ----------------------------------------------------------------------------------------------------- |
| **Detection** | CRUD • Advanced filtering & fuzzy text match • Pagination • Export                             |
| **Video**     | Segment storage & retrieval • Detection-to-video links • Cleanup & archival                   |

---

## 5. Real-time Features

| Area            | Details                                               |
| --------------- | ----------------------------------------------------- |
| **WebSocket**   | Live video feed • Real-time detection updates • Dashboard notifications • Connection mgmt  |
| **Background**  | Continuous frame processing • Detection queue • Real-time output • Health monitoring & recovery |

---

## 6. File Upload / Processing

| Feature          | Details                                                    |
| ---------------- | ---------------------------------------------------------- |
| **Image Upload** | Single-image detection • Format validation • Processing & result generation |
| **Video Files**  | Upload support • Frame extraction & analysis • Batch processing |

---

## 7. Camera Integration

| Area              | Details                                                    |
| ----------------- | ---------------------------------------------------------- |
| **Sources**       | USB • RTSP • Video-file playback • Test-pattern generation |
| **Controls**      | Resolution • FPS • Camera switching • Error handling       |

---

_This list captures every user-facing feature and critical business logic area that requires thorough test coverage._
