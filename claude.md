# Claude Development Documentation

## Overview

This document serves as a comprehensive guide for working with Claude in our License Plate Recognition (LPR) framework. It outlines the established tech stack, coding standards, and interaction patterns for consistent development practices.

## Tech Stack Reference

### Architecture
- **Primary Pattern**: Monolithic FastAPI application with modular services
- **Architecture Type**: Single application with service-oriented internal structure
- **Deployment**: Docker containerization with volume mounts

### Frontend Stack
- **Framework**: FastAPI with Jinja2 templates
- **Templates**: HTML templates with vanilla JavaScript
- **Styling**: CSS with responsive design
- **Static Files**: Served directly by FastAPI

### Backend Stack
- **Primary**: Python 3.11+ with FastAPI
- **Web Server**: Uvicorn ASGI server
- **Real-time**: WebSocket connections for live streaming
- **Configuration**: Pydantic Settings with .env support

### Database
- **Primary**: SQLite with async support
- **ORM**: SQLAlchemy with async sessions (aiosqlite)
- **File Location**: data/license_plates.db
- **Backup**: Automated daily backups via Docker service

### AI/ML Services
- **Object Detection**: YOLOv11/YOLOv8 models (yolo11m_best.pt, yolov8m.pt)
- **OCR**: EasyOCR for license plate text recognition
- **Computer Vision**: OpenCV for image processing and camera handling
- **ML Framework**: PyTorch with CUDA support for GPU acceleration
- **Model Management**: Ultralytics for YOLO model training and inference

### Infrastructure & DevOps
- **Containerization**: Docker and Docker Compose
- **Development**: Local development with volume mounts
- **Logging**: Structured logging with coloredlogs
- **Testing**: Pytest with comprehensive test coverage
- **File Storage**: Local file system with organized directory structure

## Code Quality Standards

### Python (PEP8 Compliant)
```python
# 4 spaces indentation (converted to tabs per user preference)
# Complete imports at top
# Explicit initialization
# No undefined variables or global state

from typing import Optional, List
import asyncio
from fastapi import FastAPI, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

class DetectionService:
	def __init__(self, model_path: str, confidence_threshold: float = 0.5) -> None:
		self.model_path = model_path
		self.confidence_threshold = confidence_threshold
		self._model = None
	
	async def detect_plates(self, image_data: bytes) -> Optional[List[dict]]:
		if not self._model:
			await self._initialize_model()
		return await self._process_detection(image_data)
```

### HTML/JavaScript Templates
```html
<!-- Jinja2 template with vanilla JavaScript -->
<!DOCTYPE html>
<html>
<head>
	<title>{{ title }}</title>
	<script>
		const ws = new WebSocket('ws://localhost:8001/ws/stream');
		ws.onmessage = function(event) {
			const data = JSON.parse(event.data);
			updateDetectionDisplay(data);
		};
	</script>
</head>
<body>
	<div id="detection-results"></div>
</body>
</html>
```

## Interaction Guidelines

### Communication Style
- **Output**: Minimal, clear responses with brief explanations
- **Python Help**: Provide clarifications for complex syntax
- **Context**: Ask for missing context rather than guessing
- **Indentation**: Use tabs (user preference)

### File Handling Protocol
- Never modify files automatically unless in Agent Mode
- Include file path and language in code blocks
- Present only relevant changes with placeholders
- Restate full headers when modifying functions/classes
- Provide complete files only when explicitly requested

### Code Review Focus
- Framework and architecture alignment
- Performance optimization suggestions
- Security best practices
- Scalability considerations

## Development Workflow

### Project Structure
```
plate_recognition/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── main_v2.py           # Alternative main for v2 API
│   ├── database.py          # SQLAlchemy async database setup
│   ├── models.py            # Pydantic models and SQLAlchemy schemas
│   ├── dependencies/        # FastAPI dependency injection
│   ├── factories/           # Service factory patterns
│   ├── interfaces/          # Abstract base classes
│   ├── repositories/        # Data access layer
│   ├── routers/             # FastAPI route handlers
│   ├── services/            # Business logic services
│   └── utils/               # Utility functions and helpers
├── data/
│   ├── license_plates.db    # SQLite database
│   ├── license_plates/      # Detected plate images
│   ├── enhanced_plates/     # Enhanced/processed images
│   └── videos/              # Recorded video files
├── templates/               # Jinja2 HTML templates
├── static/                  # CSS/JS static files
├── tests/                   # Pytest test suite
├── scripts/                 # Utility and training scripts
├── train/                   # YOLO model training pipeline
└── docker-compose.yml
```

### Environment Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# Docker development
docker-compose up -d

# Run tests
pytest tests/ -v

# Database initialization (automatic on first run)
# SQLite database created at data/license_plates.db
```

## AI/ML Service Guidelines

### YOLO Model Implementation
```python
from ultralytics import YOLO
import cv2
import numpy as np

class DetectionService:
	def __init__(self, model_path: str = "app/models/yolo11m_best.pt"):
		self.model = YOLO(model_path)
		self.confidence_threshold = 0.5
	
	def detect_license_plates(self, image: np.ndarray) -> list:
		results = self.model(image, conf=self.confidence_threshold, verbose=False)
		detections = []
		
		for result in results:
			for box in result.boxes:
				x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
				confidence = box.conf[0].cpu().numpy()
				detections.append({
					"bbox": [int(x1), int(y1), int(x2), int(y2)],
					"confidence": float(confidence)
				})
		
		return detections
```

### FastAPI Service Template
```python
from fastapi import FastAPI, WebSocket, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db_session

app = FastAPI(title="License Plate Recognition API")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
	await websocket.accept()
	try:
		while True:
			# Real-time plate detection streaming
			data = await websocket.receive_bytes()
			# Process detection and send results
			await websocket.send_json({"status": "processing"})
	except Exception as e:
		await websocket.close()

@app.get("/api/detections")
async def get_detections(db: AsyncSession = Depends(get_db_session)):
	# Database query logic
	pass
```

## Database Operations

### SQLAlchemy Schema Example
```python
from sqlalchemy import Column, Integer, String, DateTime, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Detection(Base):
	__tablename__ = "detections"
	
	id = Column(Integer, primary_key=True, index=True)
	license_plate = Column(String(20), index=True)
	confidence = Column(Float)
	bbox_x1 = Column(Integer)
	bbox_y1 = Column(Integer) 
	bbox_x2 = Column(Integer)
	bbox_y2 = Column(Integer)
	image_path = Column(String(255))
	timestamp = Column(DateTime(timezone=True), server_default=func.now())
	processed = Column(String(10), default="pending")
```

### Database Connection
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite+aiosqlite:///data/license_plates.db"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db_session():
	async with async_session() as session:
		try:
			yield session
		finally:
			await session.close()
```

## Deployment Guidelines

### Docker Configuration
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
	libgl1-mesa-glx \
	libglib2.0-0 \
	libsm6 \
	libxext6 \
	libxrender-dev \
	libgomp1 \
	&& rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Create necessary directories
RUN mkdir -p data/license_plates data/enhanced_plates data/videos logs

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### Local Development
- Use Docker Compose for consistent development environment
- Volume mounts for persistent data and model storage
- GPU support can be enabled with nvidia-docker
- Port 8001 for web interface

## Troubleshooting

### Common Issues
- **Import Errors**: Ensure all dependencies are in requirements.txt
- **CUDA/GPU Issues**: Verify PyTorch CUDA installation with `torch.cuda.is_available()`
- **Model Loading**: Check model file paths in app/models/ directory
- **Database Permissions**: Ensure data/ directory is writable
- **Camera Access**: Verify camera permissions and device availability
- **Docker Build**: Clear cache with `docker system prune`

### Performance Optimization
- Use async/await for I/O operations and database queries
- Implement model caching to avoid reloading YOLO models
- Optimize image processing with OpenCV and numpy
- Monitor memory usage with large video files
- Use GPU acceleration when available for model inference

## Resources

### Documentation Links
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Async Documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Ultralytics YOLO Documentation](https://docs.ultralytics.com/)
- [OpenCV Python Documentation](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html)
- [EasyOCR Documentation](https://github.com/JaidedAI/EasyOCR)
- [PyTorch Documentation](https://pytorch.org/docs/stable/index.html)

### Architecture References
- FastAPI best practices and patterns
- Computer vision pipeline optimization
- Real-time streaming with WebSockets
- SQLite optimization for embedded applications

## Development Notes

- Solo developer workflow optimized for rapid prototyping
- Focus on monolithic architecture with modular services
- Computer vision and ML background assumed
- Minimal output preferred for efficiency
- Performance optimization and GPU utilization prioritized
- Local file storage for simplicity and speed

## Key Commands

### Development
```bash
# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# Run tests
pytest tests/ -v --tb=short

# Check GPU availability
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"

# Train YOLO model
cd train && bash train_yolo.sh
```

### Docker
```bash
# Build and run
docker-compose up --build

# View logs
docker-compose logs -f lpr-app

# Stop services
docker-compose down
```