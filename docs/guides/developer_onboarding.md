
## 4. Developer Onboarding Guide

### `/docs/guides/developer_onboarding.md`:

~~~markdown
# Developer Onboarding Guide

**Version:** 1.0
**Last Updated:** 2023-07-20
**Authors:** [Your Name]

## Overview

This guide helps new developers get up to speed with the License Plate Recognition System codebase, with a focus on the database and video recording functionality.

## 1. Development Environment Setup

### 1.1 Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git
- OpenCV dependencies (for video encoding)

### 1.2 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-organization/license-plate-recognition.git
   cd license-plate-recognition

Create a virtual environment:

Bash
Run
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Install dependencies:

Bash
Run
pip install -r requirements.txt
1.3 Configuration
Create a .env file based on the example:

Bash
Run
cp .env.example .env
Edit the .env file with your configuration settings.

2. Project Structure
Key directories and files for the database and video recording functionality:


Apply
/app
├── database.py                  # Database connection setup
├── models.py                    # SQLAlchemy models
├── interfaces/                  # Abstract interfaces
├── repositories/
│   └── sql_repository.py        # SQL data access
├── services/
│   └── video_service.py         # Video recording
├── routers/
│   └── video.py                 # Video API endpoints
```

## 3. Key Concepts

### 3.1 Database Design

The system uses SQLite with SQLAlchemy ORM. Key models:

- `Detection`: License plate detection records
- `EnhancedResult`: Post-processed detection results
- `VideoSegment`: Video recording metadata

See [Database Schema](../technical/database.md) for details.

### 3.2 Repository Pattern

Data access is abstracted through repositories:

- `SQLiteDetectionRepository`: Detection data access
- `SQLiteEnhancementRepository`: Enhanced result data access
- `SQLiteVideoRepository`: Video metadata access

### 3.3 Video Recording

Video recording is handled by:

- `VideoRecorder`: Low-level recording functionality
- `VideoRecordingService`: High-level service

See [Video Recording System](../technical/video_recording.md) for details.

## 4. Common Development Tasks

### 4.1 Adding a New Database Field

1. Add the field to the model in `app/models.py`:
   ```python
   class Detection(Base):
       # Existing fields...
       new_field = Column(String)
   ```

2. Update the repository implementation in `app/repositories/sql_repository.py`:
   ```python
   def _detection_to_dict(self, detection: Detection) -> Dict[str, Any]:
       return {
           # Existing fields...
           "new_field": detection.new_field,
       }
   ```

3. If needed, update API endpoints to include the new field.

### 4.2 Modifying Video Recording Settings

1. Update the `VideoRecorder` initialization in `app/services/video_service.py`:
   ```python
   self.recorder = VideoRecorder(
       buffer_seconds=10,  # Changed from 5
       post_event_seconds=20,  # Changed from 15
       fps=30  # Changed from 15
   )
   ```

2. Update documentation to reflect the new settings.

### 4.3 Adding a New API Endpoint

1. Add the endpoint to `app/routers/video.py`:
   ```python
   @router.get("/my-new-endpoint")
   async def my_new_endpoint():
       # Implementation...
       return {"result": "success"}
   ```

2. Update API documentation.

## 5. Testing

### 5.1 Running Tests

```bash
# Run all tests
pytest

# Run specific tests
pytest tests/test_video_service.py
```

### 5.2 Adding Tests

1. Create test files in the `tests` directory
2. Use pytest fixtures for common setup
3. Mock external dependencies

Example test for video repository:

```python
def test_add_video_segment(db_session):
    # Setup
    repo = SQLiteVideoRepository(db_session)
    
    # Execute
    segment_id = await repo.add_video_segment(
        file_path="test/path.mp4",
        start_time=datetime.now(),
        end_time=datetime.now() + timedelta(seconds=20),
        duration_seconds=20.0,
        file_size_bytes=1024,
        resolution="640x480",
        detection_ids="test-id"
    )
    
    # Verify
    segment = await repo.get_video_segment_by_id(segment_id)
    assert segment is not None
    assert segment["file_path"] == "test/path.mp4"
```

## 6. Debugging Tips

### 6.1 Database Inspection

Use SQLite command-line tools:

```bash
# Open SQLite shell
sqlite3 data/license_plates.db

# List tables
.tables

# Show schema
.schema detections

# Query data
SELECT * FROM detections LIMIT 10;
```

### 6.2 Video Recording Troubleshooting

- Check logs for OpenCV errors
- Verify codec compatibility
- Ensure directories are writable
- Check for disk space issues

## 7. Code Style and Conventions

- Follow PEP 8 guidelines
- Use type hints consistently
- Write docstrings for all functions and classes
- Follow existing patterns for consistency

## 8. References

- [Project Architecture](../technical/architecture.md)
- [Database Schema](../technical/database.md)
- [Video Recording System](../technical/video_recording.md)
- [API Reference](../technical/api_reference.md)
```