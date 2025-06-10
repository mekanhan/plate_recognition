# Database Schema and Implementation

**Version:** 1.0
**Last Updated:** 2023-07-20

## Overview

This document describes the database schema and implementation details for the License Plate Recognition System. The system uses SQLite with SQLAlchemy for data persistence.

## Database Design

### Entity Relationship Diagram

Detection
├── id (PK)
├── plate_text
├── confidence
├── timestamp
├── ...
└── video_path

EnhancedResult
├── id (PK)
├── original_detection_id (FK) ───────▶ Detection.id
├── plate_text
├── confidence
└── ...

VideoSegment
├── id (PK)
├── file_path ───────────────────────▶ Detection.video_path
├── start_time
├── end_time
└── ...


### Tables

#### Detection Table

Stores license plate detection records:

| Column          | Type      | Description                         | Nullable | Default   |
|-----------------|-----------|-------------------------------------|----------|-----------|
| id              | TEXT      | Primary key (UUID)                  | No       | uuid4()   |
| plate_text      | TEXT      | Detected license plate text         | No       | -         |
| confidence      | REAL      | Detection confidence score (0-1)    | No       | -         |
| timestamp       | DATETIME  | When the detection occurred         | No       | utcnow()  |
| box_x1          | INTEGER   | Left coordinate of bounding box     | Yes      | NULL      |
| box_y1          | INTEGER   | Top coordinate of bounding box      | Yes      | NULL      |
| box_x2          | INTEGER   | Right coordinate of bounding box    | Yes      | NULL      |
| box_y2          | INTEGER   | Bottom coordinate of bounding box   | Yes      | NULL      |
| frame_id        | INTEGER   | ID of the source frame              | Yes      | NULL      |
| raw_text        | TEXT      | Original OCR text before processing | Yes      | NULL      |
| state           | TEXT      | US state code if identified         | Yes      | NULL      |
| status          | TEXT      | Detection status                    | No       | 'active'  |
| vehicle_type    | TEXT      | Type of vehicle                     | Yes      | NULL      |
| direction       | TEXT      | Direction of travel                 | Yes      | NULL      |
| location        | TEXT      | Detection location                  | Yes      | NULL      |
| image_path      | TEXT      | Path to stored image                | Yes      | NULL      |
| video_path      | TEXT      | Path to video recording             | Yes      | NULL      |
| video_start_time| DATETIME  | When recording started              | Yes      | NULL      |
| video_end_time  | DATETIME  | When recording ended                | Yes      | NULL      |

**Indexes**:
- `idx_detections_timestamp`: On `timestamp` (DESC)
- `idx_detections_plate_text`: On `plate_text`

#### Enhanced Results Table

Stores post-processed detection results:

| Column             | Type      | Description                       | Nullable | Default   |
|--------------------|-----------|-----------------------------------|----------|-----------|
| id                 | TEXT      | Primary key (UUID)                | No       | uuid4()   |
| original_detection_id | TEXT   | Foreign key to detections         | No       | -         |
| plate_text         | TEXT      | Enhanced license plate text       | No       | -         |
| confidence         | REAL      | Enhanced confidence score (0-1)   | No       | -         |
| timestamp          | DATETIME  | When enhancement occurred         | No       | utcnow()  |
| match_type         | TEXT      | How enhancement was determined    | Yes      | NULL      |
| confidence_category| TEXT      | Text category (LOW, MEDIUM, HIGH) | Yes      | NULL      |
| enhanced_image_path| TEXT      | Path to enhanced image            | Yes      | NULL      |

**Indexes**:
- `idx_enhanced_results_original_detection_id`: On `original_detection_id`

#### Video Segments Table

Stores metadata about recorded videos:

| Column          | Type      | Description                       | Nullable | Default   |
|-----------------|-----------|-----------------------------------|----------|-----------|
| id              | TEXT      | Primary key (UUID)                | No       | uuid4()   |
| file_path       | TEXT      | Path to video file                | No       | -         |
| start_time      | DATETIME  | When recording started            | No       | -         |
| end_time        | DATETIME  | When recording ended              | No       | -         |
| duration_seconds| REAL      | Length of recording in seconds    | No       | -         |
| file_size_bytes | INTEGER   | Size of video file in bytes       | No       | -         |
| resolution      | TEXT      | Video resolution (e.g., "1280x720")| No      | -         |
| archived        | BOOLEAN   | Whether video is archived         | No       | FALSE     |
| detection_ids   | TEXT      | Comma-separated list of detection IDs| Yes   | NULL      |

**Indexes**:
- `idx_video_segments_start_time`: On `start_time` (DESC)

#### Known Plates Table

Stores reference plates for comparison:

| Column          | Type      | Description                       | Nullable | Default   |
|-----------------|-----------|-----------------------------------|----------|-----------|
| id              | TEXT      | Primary key (UUID)                | No       | uuid4()   |
| plate_text      | TEXT      | Known license plate text          | No       | -         |
| state           | TEXT      | Associated state code             | Yes      | NULL      |
| added_at        | DATETIME  | When plate was added              | No       | utcnow()  |
| vehicle_type    | TEXT      | Type of vehicle                   | Yes      | NULL      |
| notes           | TEXT      | Additional notes                  | Yes      | NULL      |
| authorized      | BOOLEAN   | Whether vehicle is authorized     | No       | TRUE      |

**Indexes**:
- `idx_known_plates_plate_text`: On `plate_text` (UNIQUE)

## SQLAlchemy Models

### Base Model

```python
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()
```

Detection Model


class Detection(Base):
    """License plate detection records"""
    __tablename__ = "detections"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    plate_text = Column(String, nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, index=True)
    
    # Bounding box
    box_x1 = Column(Integer)
    box_y1 = Column(Integer)
    box_x2 = Column(Integer)
    box_y2 = Column(Integer)
    
    # Additional metadata
    frame_id = Column(Integer)
    raw_text = Column(String)
    state = Column(String)
    status = Column(String, default="active", index=True)
    vehicle_type = Column(String)
    direction = Column(String)
    location = Column(String)
    
    # Image and video references
    image_path = Column(String)
    video_path = Column(String)
    video_start_time = Column(DateTime)
    video_end_time = Column(DateTime)
    
    # Relationships
    enhanced_results = relationship("EnhancedResult", back_populates="detection")
Enhanced Result Model


class EnhancedResult(Base):
    """Enhanced license plate results after processing"""
    __tablename__ = "enhanced_results"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    original_detection_id = Column(String, ForeignKey("detections.id"), index=True)
    plate_text = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    match_type = Column(String)
    confidence_category = Column(String)
    enhanced_image_path = Column(String)
    
    # Relationship
    detection = relationship("Detection", back_populates="enhanced_results")
Video Segment Model


class VideoSegment(Base):
    """Video recording segments"""
    __tablename__ = "video_segments"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    file_path = Column(String, nullable=False, unique=True)
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False)
    duration_seconds = Column(Float, nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    resolution = Column(String, nullable=False)
    archived = Column(Boolean, default=False)
    detection_ids = Column(String)  # Comma-separated list of detection IDs
Repository Implementation
Detection Repository
Python


class SQLiteDetectionRepository(DetectionRepository):
    """SQLite implementation of the detection repository"""
    
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self.initialization_complete = False
        
    async def initialize(self) -> None:
        """Initialize the repository"""
        self.initialization_complete = True
        
    async def add_detections(self, detections: List[Dict[str, Any]]) -> None:
        """Add detections to the repository"""
        async with self.session_factory() as session:
            for detection_data in detections:
                # Convert data to model and save
                detection = Detection(...)
                session.add(detection)
            await session.commit()
    
    async def get_detections(self) -> List[Dict[str, Any]]:
        """Get all detections"""
        async with self.session_factory() as session:
            result = await session.execute(
                select(Detection).order_by(Detection.timestamp.desc())
            )
            detections = result.scalars().all()
            return [self._detection_to_dict(detection) for detection in detections]
Database Connection

# Database connection setup
DATABASE_URL = "sqlite+aiosqlite:///data/license_plates.db"

engine = create_async_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite
    echo=False,  # Set to True for debug SQL output
)

# Session factory
async_session = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def init_db():
    """Initialize the database tables"""
    from app.models import Base
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

Database Maintenance
Optimization
Periodic database optimization:

async def run_sqlite_vacuum():
    """Run VACUUM command to optimize SQLite database"""
    import sqlite3
    conn = sqlite3.connect("data/license_plates.db")
    conn.execute("VACUUM")
    conn.close()
Data Retention

async def cleanup_old_data(days: int = 30):
    """Archives data older than specified days"""
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
    
    async with session_factory() as session:
        # Archive old detections
        await session.execute(
            update(Detection)
            .where(Detection.timestamp < cutoff_date)
            .values(status="archived")
        )
        await session.commit()
