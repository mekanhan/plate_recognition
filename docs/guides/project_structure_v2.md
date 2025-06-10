# Project Structure Guide - V2 License Plate Recognition System

**Version:** 2.0  
**Last Updated:** 2025-06-10  
**Authors:** Development Team  

## Overview

This document provides a comprehensive guide to the V2 project structure, explaining the organization, purpose, and relationships between different directories and files in the License Plate Recognition System.

## Root Directory Structure

```
plate_recognition/                          # Project root
├── .env                                   # Environment configuration
├── .env.example                           # Environment template
├── .gitignore                             # Git ignore patterns
├── .venv/                                 # Virtual environment (created)
├── README.md                              # Project overview
├── requirements.txt                       # Python dependencies
├── docker-compose.yml                     # Docker composition
├── Dockerfile                             # Docker container definition
├── app/                                   # Main application code
├── config/                                # Configuration modules
├── data/                                  # Runtime data storage
├── docs/                                  # Documentation
├── logs/                                  # Application logs
├── static/                                # Web assets
├── templates/                             # HTML templates
├── tests/                                 # Test suite
├── train/                                 # ML training code
├── scripts/                               # Utility scripts
└── images/                                # Sample images
```

## Application Structure (`app/`)

The main application code follows a layered architecture with clear separation of concerns:

```
app/
├── __init__.py                            # Package initialization
├── main.py                                # V1 application entry point
├── main_v2.py                             # V2 application entry point (primary)
├── database.py                            # Database configuration
├── models.py                              # SQLAlchemy data models
├── dependencies/                          # Dependency injection
│   ├── __init__.py
│   ├── camera.py                         # Camera dependency
│   ├── detection.py                      # Detection service dependency
│   └── services.py                       # V2 service dependencies
├── factories/                             # Factory pattern implementations
│   ├── __init__.py
│   └── service_factory.py                # Service factory for DI
├── interfaces/                            # Interface definitions
│   ├── __init__.py
│   ├── camera.py                         # Camera interface
│   ├── detector.py                       # Detector interface
│   ├── enhancer.py                       # Enhancer interface
│   └── storage.py                        # Storage interfaces
├── models/                                # ML models directory
│   ├── yolo11m_best.pt                   # Custom trained model
│   ├── yolo11n.pt                        # YOLO11 nano
│   ├── yolov11m.pt                       # YOLO11 medium
│   ├── yolov8m.pt                        # YOLO8 medium
│   └── yolov8n.pt                        # YOLO8 nano
├── repositories/                          # Data access layer
│   ├── __init__.py
│   ├── json_repository.py                # JSON file storage
│   └── sql_repository.py                 # SQLite database storage
├── routers/                               # API route definitions
│   ├── __init__.py
│   ├── detection.py                      # V1 detection endpoints
│   ├── detection_v2.py                   # V2 detection endpoints
│   ├── results.py                        # V1 results endpoints
│   ├── results_v2.py                     # V2 results endpoints
│   ├── stream.py                         # V1 streaming endpoints
│   ├── stream_v2.py                      # V2 streaming endpoints
│   └── video.py                          # Video management endpoints
├── services/                              # Business logic layer
│   ├── __init__.py
│   ├── camera_service.py                 # Camera operations
│   ├── detection_service.py              # V1 detection service
│   ├── detection_service_v2.py           # V2 detection service
│   ├── enhancer_service.py               # Detection enhancement
│   ├── license_plate_recognition_service.py  # Core LPR engine
│   ├── plate_processor.py                # Plate processing logic
│   ├── service_factory.py                # Service creation
│   ├── storage_service.py                # V1 storage service
│   ├── storage_service_v2.py             # V2 storage service
│   ├── tracker.py                        # Object tracking
│   └── video_service.py                  # Video recording service
└── utils/                                 # Utility modules
    ├── __init__.py
    ├── config.py                         # Configuration helpers
    ├── convert_to_tensorboard.py         # ML utilities
    ├── convert_videos.py                 # Video conversion
    ├── file_helpers.py                   # File operations
    ├── license_plate_processor.py        # Plate processing
    ├── logging_config.py                 # Logging setup
    ├── plate_database.py                 # Database utilities
    ├── scrcpy.py                         # Screen capture utilities
    ├── us_states.py                      # US state patterns
    └── verify_pytorch_installation.py    # PyTorch verification
```

### Key Architectural Layers

#### **1. Interface Layer (`interfaces/`)**
Defines contracts for all major components:

```python
# interfaces/detector.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
import numpy as np

class LicensePlateDetector(ABC):
    @abstractmethod
    async def detect_and_recognize(self, image: np.ndarray) -> Tuple[List[Dict[str, Any]], np.ndarray]:
        """Detect and recognize license plates in an image"""
        pass
```

#### **2. Service Layer (`services/`)**
Contains business logic and orchestration:

- **`detection_service_v2.py`**: Main detection orchestrator
- **`license_plate_recognition_service.py`**: Core detection engine  
- **`video_service.py`**: Video recording with overlays
- **`enhancer_service.py`**: Post-processing improvements

#### **3. Repository Layer (`repositories/`)**
Data access abstraction with multiple implementations:

- **`sql_repository.py`**: SQLite database operations
- **`json_repository.py`**: JSON file operations
- **Composite pattern**: Dual storage approach

#### **4. Router Layer (`routers/`)**
API endpoint definitions with versioning:

- **V1 Routers**: Backward compatibility (`detection.py`, `results.py`, `stream.py`)
- **V2 Routers**: Enhanced features (`detection_v2.py`, `results_v2.py`, `stream_v2.py`)

## Data Directory Structure (`data/`)

Runtime data organized by type and date:

```
data/
├── enhanced_plates/                       # Enhanced detection results
│   ├── enhanced_session_20250531_232811.json
│   ├── enhanced_session_20250602_125018.json
│   └── ...
├── license_plates/                        # Raw detection results
│   ├── lpr_session_20250610_140523.json
│   ├── lpr_session_20250610_141205.json
│   └── ...
├── videos/                                # Video recordings
│   ├── 2025-06-09/                       # Date-based organization
│   │   ├── det_abc123_1749537429.mp4
│   │   └── det_xyz789_1749538747.mp4
│   └── 2025-06-10/
│       ├── test_annotated_1749540407.mp4
│       └── simple_test_1749540684.mp4
├── known_plates.json                      # Known plates database
└── license_plates.db                      # SQLite database
```

### Data Storage Patterns

#### **JSON Session Files**
```json
{
  "session_info": {
    "session_id": "session_20250610_140523",
    "start_time": 1733881523.456,
    "version": "2.0"
  },
  "detections": [
    {
      "detection_id": "det_abc123",
      "timestamp": 1733881525.123,
      "plate_text": "ABC123",
      "confidence": 0.87,
      "state": "TX"
    }
  ]
}
```

#### **Video File Naming**
- **Format**: `{detection_id}_{timestamp}.mp4`
- **Example**: `det_abc123_1749537429.mp4`
- **Organization**: Date-based subdirectories

## Documentation Structure (`docs/`)

Comprehensive documentation organized by type:

```
docs/
├── README.md                              # Documentation index
├── class_diagram/                         # UML diagrams
│   ├── improved_class_diagram.puml       # V1 class diagram
│   └── v2_enhanced_diagram.puml          # V2 enhanced diagram
├── flowcharts/                            # System workflows
│   ├── overview.md                       # V1 workflow
│   └── v2_system_flow.md                 # V2 enhanced workflow
├── guides/                                # Implementation guides
│   ├── dependencies.md                   # Dependency guide
│   ├── developer_onboarding.md           # Developer guide
│   ├── developer_resources.md            # Resource guide
│   ├── installation_v2.md                # V2 installation
│   ├── LPR_FRAMEWORK_GUIDE.md           # Framework guide
│   ├── project_structure_v2.md           # This document
│   ├── v2_migration_guide.md             # Migration guide
│   └── instructions.sh                   # Setup scripts
├── plans/                                 # Development plans
│   ├── database_and_video_recording_implementation_plan.md
│   └── plan_p1.md
├── technicals/                            # Technical specifications
│   ├── api.md                            # V1 API reference
│   ├── api_reference.md                  # API documentation
│   ├── architecture.md                   # V1 architecture
│   ├── architecture_v2.md                # V2 architecture
│   ├── code_structure_and_system_architecture_overview.md
│   ├── database.md                       # Database design
│   ├── enhanced_features_v2.md           # V2 enhancements
│   ├── improved_architecture.md          # Architecture improvements
│   ├── technology_stack_v2.md            # Technology overview
│   └── video_recording.md                # Video system design
├── logic_phase1.md                       # Phase 1 logic
└── rules.md                              # Development rules
```

### Documentation Categories

#### **Technical Documentation**
- **Architecture**: System design and component relationships
- **API Reference**: Endpoint documentation with examples
- **Database**: Schema design and data models
- **Technology Stack**: Tools and libraries overview

#### **User Guides**
- **Installation**: Setup and configuration instructions
- **Migration**: V1 to V2 upgrade procedures
- **Developer Onboarding**: New developer guide
- **Project Structure**: Codebase organization (this document)

#### **Visual Documentation**
- **Class Diagrams**: PlantUML architecture diagrams
- **Flowcharts**: Mermaid workflow diagrams
- **System Overview**: High-level system understanding

## Configuration Structure (`config/`)

Configuration management with environment-based settings:

```
config/
├── __init__.py
└── settings.py                            # Application settings
```

### Configuration Hierarchy

1. **Environment Variables** (highest priority)
2. **`.env` file** (development)
3. **Default values** (fallback)

```python
# config/settings.py
from pydantic_settings import BaseSettings

class Config(BaseSettings):
    camera_id: str = "0"
    camera_width: str = "1280"
    camera_height: str = "720"
    model_path: str = "app/models/yolo11m_best.pt"
    
    class Config:
        env_file = ".env"
        extra = "ignore"
```

## Test Structure (`tests/`)

Comprehensive test suite with multiple test categories:

```
tests/
├── __init__.py
├── conftest.py                            # Pytest configuration
├── test_api.py                           # V1 API tests
├── test_api_v2.py                        # V2 API tests
├── test_connection.py                    # Connection tests
├── test_e2e_saving.py                    # End-to-end tests
├── test_integration.py                   # Integration tests
├── test_license_plate_recognition.py    # LPR tests
├── test_storage_saving.py               # Storage tests
├── test_storage_service.py              # Service tests
├── check_videos.py                      # Video validation
├── database_testing/                    # Database tests
│   └── test_db.py
└── unit_tests/                          # Unit test utilities
    ├── debug_services.py                # Service debugging
    ├── debug_video_creation.py          # Video creation debug
    ├── test_annotated_video.py          # Annotated video test
    ├── test_texas_plates.py             # Texas plate test
    ├── test_troubleshooting.py          # System troubleshooting
    └── test_video_simple.py             # Simple video test
```

### Test Categories

#### **Unit Tests**
- **Service Tests**: Individual service functionality
- **Repository Tests**: Data access layer testing
- **Utility Tests**: Helper function validation

#### **Integration Tests**
- **API Tests**: Endpoint functionality
- **Storage Tests**: Database and file operations
- **Video Tests**: Recording and playback validation

#### **End-to-End Tests**
- **Complete Workflows**: Full detection pipeline
- **Performance Tests**: System performance validation
- **Regression Tests**: Feature stability verification

## Static Assets (`static/`)

Web interface assets:

```
static/
├── css/                                   # Stylesheets
├── js/                                    # JavaScript files
│   └── stream.js                         # Video streaming client
└── images/                                # Web interface images
```

## Templates (`templates/`)

HTML templates for web interface:

```
templates/
├── detection_test.html                    # Detection testing page
├── index.html                            # Main landing page
├── results.html                          # Results display page
├── stream.html                           # Video streaming page
├── v2_index.html                         # V2 main page
└── video_browser.html                    # Video browsing interface
```

## Training Code (`train/`)

Machine learning model training infrastructure:

```
train/
├── README.md                              # Training documentation
├── dataset/                               # Training datasets
│   ├── data.yaml                         # Dataset configuration
│   ├── images/                           # Training images
│   └── labels/                           # Annotation labels
│       ├── train/                        # Training labels
│       └── val/                          # Validation labels
├── models/                                # Model storage
│   ├── pretrained/                       # Pre-trained models
│   │   ├── yolo11m_best.pt
│   │   ├── yolo11n.pt
│   │   ├── yolov11m.pt
│   │   ├── yolov8m.pt
│   │   └── yolov8n.pt
│   └── trained/                          # Custom trained models
├── scripts/                               # Training utilities
│   ├── extract_frames.py                 # Video frame extraction
│   ├── manage_models.py                  # Model management
│   └── setup_dataset.py                  # Dataset preparation
├── train_yolo.sh                         # Training script
└── videos/                                # Training videos
```

## Utility Scripts (`scripts/`)

Development and operational utilities:

```
scripts/
├── adb_license_plate_recognition.py      # Android debugging
├── detect_license_plate.py               # Single image detection
├── detect_license_plate_video.py         # Video detection
├── enhance_plates.py                     # Plate enhancement
├── fetch_file_from_github.sh             # GitHub file fetching
├── install_pytorch_cuda.py               # CUDA installation
├── lpr_live.py                           # Live detection script
├── unit_tests/                           # Moved to tests/unit_tests/
└── updated_features.py                   # Feature updates
```

## Sample Images (`images/`)

Test images for development and validation:

```
images/
├── 1.jpg                                  # Test image 1
├── 2.jpg                                  # Test image 2
├── ...                                    # Additional test images
└── 16.jpg                                 # Test image 16
```

## File Naming Conventions

### **Python Modules**
- **snake_case**: All Python files use snake_case naming
- **Descriptive Names**: Clear, descriptive filenames
- **Version Suffixes**: V2 files use `_v2` suffix

### **Configuration Files**
- **Lowercase**: Configuration files in lowercase
- **Descriptive Extensions**: Clear file type indicators
- **Environment Specific**: `.env`, `.env.example`

### **Documentation Files**
- **Markdown**: All documentation in `.md` format
- **Version Indicators**: V2-specific docs have `_v2` suffix
- **Descriptive Names**: Clear purpose indication

### **Data Files**
- **Timestamps**: Include creation timestamps
- **Type Indicators**: Clear file type/purpose
- **Date Organization**: Video files organized by date

## Development Workflow

### **Code Organization Principles**

1. **Separation of Concerns**: Each layer has specific responsibilities
2. **Interface-based Design**: Clear contracts between components
3. **Dependency Injection**: Services receive dependencies externally
4. **Configuration-driven**: Behavior controlled through configuration
5. **Testability**: Easy unit and integration testing

### **File Modification Guidelines**

1. **V1 Compatibility**: Maintain existing V1 functionality
2. **V2 Enhancements**: Add new features in V2-specific files
3. **Interface Stability**: Avoid breaking interface changes
4. **Documentation Updates**: Update docs with code changes
5. **Test Coverage**: Add tests for new functionality

### **Directory Usage Patterns**

#### **Development**
- **Active Development**: Modify files in `app/` directory
- **Configuration**: Update `.env` and `config/` files
- **Testing**: Add tests to `tests/` directory
- **Documentation**: Update `docs/` as needed

#### **Runtime**
- **Data Storage**: Files created in `data/` directory
- **Logging**: Log files written to `logs/` directory
- **Temporary Files**: OS-specific temporary directories

#### **Deployment**
- **Production**: Use `requirements.txt` for dependencies
- **Docker**: Use `Dockerfile` and `docker-compose.yml`
- **Scripts**: Deployment automation in `scripts/`

This project structure provides a solid foundation for development, testing, and deployment while maintaining clear separation of concerns and supporting both V1 compatibility and V2 enhancements.