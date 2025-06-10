# License Plate Recognition System - V2 Architecture

**Version:** 2.0  
**Last Updated:** 2025-06-10  
**Authors:** Development Team  

## Overview

This document describes the enhanced V2 architecture of the License Plate Recognition System, featuring interface-based design, dependency injection, dual storage capabilities, and enhanced video recording with confidence overlays.

## Architecture Principles

### 1. Interface-Based Design
All major components implement well-defined interfaces to ensure loose coupling and high testability.

### 2. Dependency Injection
Services receive their dependencies through initialization rather than creating them directly.

### 3. Composite Repository Pattern
Dual storage approach using both SQL database and JSON files for redundancy and flexibility.

### 4. Service Factory Pattern
Centralized service creation and lifecycle management.

## System Architecture Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Camera        │    │  Detection      │    │  Enhancement    │
│   Service       │───▶│  Service V2     │───▶│  Service        │
│                 │    │                 │    │                 │
└─────────────────┘    └────────┬────────┘    └─────────────────┘
                                │                        │
                                ▼                        │
                       ┌─────────────────┐              │
                       │  Video Recording│              │
                       │  Service        │              │
                       │                 │              │
                       └────────┬────────┘              │
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Composite      │    │  Composite      │
                       │  Detection      │    │  Enhancement    │
                       │  Repository     │    │  Repository     │
                       └────────┬────────┘    └────────┬────────┘
                                │                        │
                    ┌───────────┼───────────┐           │
                    ▼           ▼           ▼           ▼
            ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
            │   SQLite    │ │    JSON     │ │   SQLite    │ │    JSON     │
            │ Detection   │ │ Detection   │ │Enhancement  │ │Enhancement  │
            │ Repository  │ │ Repository  │ │ Repository  │ │ Repository  │
            └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
                    │           │                   │           │
                    ▼           ▼                   ▼           ▼
            ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
            │   SQLite    │ │    JSON     │ │   SQLite    │ │    JSON     │
            │  Database   │ │    Files    │ │  Database   │ │    Files    │
            └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
```

## Core Components

### Service Layer

#### **DetectionServiceV2**
- **Purpose**: Main orchestrator for license plate detection workflow
- **Key Features**:
  - Processes video frames with configurable intervals
  - Integrates with video recording service
  - Manages dual storage through composite repositories
  - Supports enhancement pipeline
- **Dependencies**: Camera, LicensePlateDetector, DetectionRepository, EnhancementRepository, VideoRecordingService

#### **LicensePlateRecognitionService**
- **Purpose**: Core detection and recognition engine
- **Key Features**:
  - YOLO model integration for plate detection
  - EasyOCR for text recognition
  - Enhanced text filtering and validation
  - Confidence-based color coding
  - Bounding box analysis for improved accuracy
- **Enhancements**: Texas plate specific improvements, dealer text filtering

#### **VideoRecordingService**
- **Purpose**: Records video clips with enhanced overlays
- **Key Features**:
  - Pre/post event recording (5s before, 15s after detection)
  - Annotated frame recording with confidence overlays
  - Color-coded bounding boxes (Green ≥80%, Yellow ≥60%, Red <60%)
  - System performance metrics display
  - WSL-compatible file paths

#### **EnhancerService**
- **Purpose**: Post-processes detections for improved accuracy
- **Key Features**:
  - Character confusion correction
  - State-specific validation
  - Confidence boosting algorithms
  - Known plates matching

### Repository Layer

#### **Composite Pattern Implementation**
The V2 system uses composite repositories that handle both SQL and JSON storage:

```python
class CompositeDetectionRepository(DetectionRepository):
    def __init__(self, sql_repository, json_repository):
        self.sql_repository = sql_repository
        self.json_repository = json_repository
    
    async def add_detections(self, detections):
        # Write to both repositories
        await self.sql_repository.add_detections(detections)
        await self.json_repository.add_detections(detections)
```

#### **Storage Features**:
- **Redundancy**: Data saved to both SQL and JSON
- **Fallback**: JSON repository as backup if SQL fails
- **Performance**: SQL for queries, JSON for debugging/export
- **Compatibility**: Maintains V1 JSON format support

### Interface Layer

#### **Core Interfaces**
- `Camera`: Frame capture operations
- `LicensePlateDetector`: Detection and recognition
- `LicensePlateEnhancer`: Post-processing enhancement
- `DetectionRepository`: Detection data persistence
- `EnhancementRepository`: Enhanced result persistence

## Enhanced Features

### 1. Video Recording with Overlays
- **Confidence Display**: Shows OCR and detection confidence percentages
- **Color Coding**: Visual confidence indicators
- **System Metrics**: Timestamp, frame count, session uptime
- **Performance Info**: Processing time, frame rate

### 2. Dual Storage System
- **SQL Database**: Primary storage for queries and relationships
- **JSON Files**: Secondary storage for debugging and data export
- **Automatic Sync**: Both repositories updated simultaneously
- **Data Integrity**: Fallback mechanisms ensure no data loss

### 3. Enhanced License Plate Recognition
- **Bounding Box Analysis**: Size-based text filtering
- **State-Specific Logic**: Texas plate improvements
- **Dealer Text Filtering**: Removes dealership and frame text
- **Character Correction**: Handles common OCR confusions (I/1, O/0, etc.)

### 4. API Versioning
- **V2 Endpoints**: `/v2/stream`, `/v2/detection`, `/v2/results`
- **Backward Compatibility**: V1 endpoints still functional
- **Progressive Migration**: Gradual transition support

## Data Flow

### Detection Pipeline
1. **Frame Capture**: Camera service provides video frames
2. **Processing Decision**: Every 5th frame processed for performance
3. **Detection**: YOLO model detects license plate regions
4. **Recognition**: EasyOCR extracts text from detected regions
5. **Enhancement**: Text filtering and validation applied
6. **Storage**: Results saved to both SQL and JSON repositories
7. **Video Recording**: Annotated frames recorded to MP4 files
8. **Enhancement**: Optional post-processing for accuracy improvement

### Video Recording Pipeline
1. **Continuous Buffering**: 5-second rolling buffer maintained
2. **Detection Trigger**: High-confidence detection starts recording
3. **Pre-event Recording**: Buffer frames written to video file
4. **Live Recording**: Continues for 15 seconds post-detection
5. **Overlay Application**: Confidence metrics and system info added
6. **File Completion**: Video saved with metadata to database

## Configuration

### Environment Variables
```bash
# Camera Configuration
CAMERA_ID=0
CAMERA_WIDTH=1280
CAMERA_HEIGHT=720

# Model Configuration
MODEL_PATH=app/models/yolo11m_best.pt

# Storage Configuration
LICENSE_PLATES_DIR=data/license_plates
ENHANCED_PLATES_DIR=data/enhanced_plates
```

### Service Factory Configuration
The `ServiceFactory` manages service creation with proper dependency injection:

```python
factory = ServiceFactory()
factory.set_config({
    "camera_id": "0",
    "camera_width": "1280", 
    "camera_height": "720",
    "model_path": "app/models/yolo11m_best.pt",
    "license_plates_dir": "data/license_plates",
    "enhanced_plates_dir": "data/enhanced_plates"
})
```

## Performance Characteristics

### Frame Processing
- **Processing Interval**: Every 5th frame (optimized for performance)
- **Timeout Protection**: 0.5-second timeout prevents blocking
- **Adaptive Frame Rate**: ~30 FPS with dynamic sleep adjustment

### Storage Performance
- **Dual Write**: Parallel writes to SQL and JSON
- **Async Operations**: Non-blocking database operations
- **Batch Processing**: Multiple detections processed efficiently

### Video Recording
- **Codec**: MP4V for compatibility
- **Resolution**: Matches camera input (typically 1280x720)
- **Frame Rate**: 15 FPS for optimal file size/quality balance

## Deployment

### V2 Application Startup
```bash
# Activate virtual environment
python -m venv .venv
source .venv/Scripts/activate  # Windows WSL

# Install dependencies
pip install -r requirements.txt

# Run V2 application
python -m app.main_v2
```

### Service Endpoints
- **Main Application**: `http://localhost:8000/`
- **V2 Stream**: `http://localhost:8000/v2/stream`
- **V2 Results**: `http://localhost:8000/v2/results`
- **Backward Compatibility**: All V1 endpoints still available

## Migration from V1

### Key Differences
1. **Interface-based**: V2 uses dependency injection
2. **Dual Storage**: Both SQL and JSON storage
3. **Enhanced Video**: Confidence overlays and metrics
4. **Service Factory**: Centralized service management
5. **Composite Repositories**: Redundant storage approach

### Migration Strategy
1. **Parallel Deployment**: Run V2 alongside V1
2. **Gradual Testing**: Validate V2 functionality
3. **Data Migration**: Ensure data compatibility
4. **Full Transition**: Switch to V2 as primary system

## Monitoring and Debugging

### Logging
- **Structured Logging**: Component-specific log levels
- **Performance Metrics**: Processing time tracking
- **Error Handling**: Comprehensive exception management

### Testing
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow validation
- **Performance Tests**: Frame processing benchmarks

## Future Enhancements

### Planned Features
1. **Multi-frame Validation**: Confidence improvement through frame comparison
2. **Real-time Analytics**: Live performance dashboards
3. **Cloud Storage**: Optional cloud backup integration
4. **Advanced AI**: Enhanced recognition models

This V2 architecture provides a robust, scalable, and maintainable foundation for license plate recognition with significant improvements in accuracy, reliability, and observability.