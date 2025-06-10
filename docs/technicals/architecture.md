## 3. System Architecture Document

### `/docs/technical/architecture.md`:

~~~markdown
# System Architecture

**Version:** 1.0
**Last Updated:** 2023-07-20
**Authors:** [Your Name]

## Overview

This document describes the overall architecture of the License Plate Recognition System, focusing on the relationships between components and the data flow through the system.

## 1. Architecture Diagram

~~~
┌───────────────────┐      ┌───────────────────┐      ┌───────────────────┐
│                   │      │                   │      │                   │
│  Camera Service   │──────▶  Detection Service│──────▶ Enhancer Service │
│                   │      │                   │      │                   │
└─────────┬─────────┘      └────────┬──────────┘      └────────┬──────────┘
          │                         │                          │
          │                         │                          │
          │                         ▼                          │
          │              ┌───────────────────┐                 │
          └──────────────▶                   │◀───────────────┘
                         │ Video Recording   │
                         │     Service       │
                         │                   │
                         └────────┬──────────┘
                                  │
                                  │
                                  ▼
                         ┌───────────────────┐
                         │                   │
                         │  SQL Repositories │
                         │                   │
                         └────────┬──────────┘
                                  │
                                  │
                                  ▼
                         ┌───────────────────┐
                         │                   │
                         │  SQLite Database  │
                         │                   │
                         └───────────────────┘

~~~


### Component Descriptions

#### Camera Service
- **Responsibility**: Captures frames from camera and provides them to other services
- **Implementation**: `CameraService` class implementing `Camera` interface
- **Dependencies**: None (root component)

#### Detection Service
- **Responsibility**: Processes frames to detect license plates
- **Implementation**: `DetectionServiceV2` class
- **Dependencies**: Camera Service, License Plate Detector

#### Enhancer Service
- **Responsibility**: Post-processes detections to improve accuracy
- **Implementation**: `EnhancerService` class implementing `LicensePlateEnhancer` interface
- **Dependencies**: Detection Repository

#### Video Recording Service
- **Responsibility**: Records video clips when license plates are detected
- **Implementation**: `VideoRecordingService` and `VideoRecorder` classes
- **Dependencies**: Detection Repository, Video Repository

#### SQL Repositories
- **Responsibility**: Provide data access abstraction
- **Implementation**: `SQLiteDetectionRepository`, `SQLiteEnhancementRepository`, `SQLiteVideoRepository` classes
- **Dependencies**: SQLite Database

## Data Flow

### License Plate Detection Flow

1. Camera Service captures frame
2. Frame is passed to Detection Service
3. Detection Service processes frame using license plate detector
4. If license plate is detected:
   - Detection is stored in database via Detection Repository
   - Detection triggers video recording via Video Recording Service
   - Detection is enhanced via Enhancer Service
   - Enhanced result is stored via Enhancement Repository

### Video Recording Flow

1. Frames are continuously buffered in Video Recorder
2. When a license plate is detected with sufficient confidence:
   - Pre-event buffer frames are written to video file
   - Recording continues for post-event period
   - Video metadata is stored in database

## Design Principles

### Interface-Based Design

The system uses interfaces to define contracts between components:

- `Camera` interface for camera operations
- `LicensePlateDetector` interface for detection
- `LicensePlateEnhancer` interface for enhancement
- `DetectionRepository` and `EnhancementRepository` interfaces for storage

### Repository Pattern

Data access is abstracted through repository interfaces:

- Repositories provide data access methods
- Concrete implementations handle database interactions
- Business logic doesn't directly interact with the database

### Service Pattern

Business logic is organized into service classes:

- Services implement specific functionality domains
- Services depend on interfaces, not concrete implementations
- Services can be tested independently with mock dependencies

## Technology Stack

- **Language**: Python 3.8+
- **Web Framework**: FastAPI
- **Database**: SQLite with SQLAlchemy ORM
- **Video Processing**: OpenCV
- **License Plate Detection**: YOLO model with EasyOCR