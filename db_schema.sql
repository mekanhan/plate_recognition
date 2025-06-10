-- Detection table for license plate records
CREATE TABLE detections (
    id TEXT PRIMARY KEY,
    plate_text TEXT NOT NULL,
    confidence REAL NOT NULL,
    timestamp DATETIME NOT NULL,
    box_x1 INTEGER,
    box_y1 INTEGER,
    box_x2 INTEGER,
    box_y2 INTEGER,
    frame_id INTEGER,
    raw_text TEXT,
    state TEXT,
    status TEXT DEFAULT 'active',
    vehicle_type TEXT,
    direction TEXT,
    location TEXT,
    image_path TEXT,
    video_path TEXT,
    video_start_time DATETIME,
    video_end_time DATETIME
);

-- Enhanced results from post-processing
CREATE TABLE enhanced_results (
    id TEXT PRIMARY KEY,
    original_detection_id TEXT REFERENCES detections(id),
    plate_text TEXT NOT NULL,
    confidence REAL NOT NULL,
    timestamp DATETIME NOT NULL,
    match_type TEXT,
    confidence_category TEXT,
    enhanced_image_path TEXT
);

-- Known plates for reference/matching
CREATE TABLE known_plates (
    id TEXT PRIMARY KEY,
    plate_text TEXT NOT NULL UNIQUE,
    state TEXT,
    added_at DATETIME NOT NULL,
    vehicle_type TEXT,
    notes TEXT,
    authorized BOOLEAN DEFAULT TRUE
);

-- System events for monitoring
CREATE TABLE system_events (
    id TEXT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    event_type TEXT NOT NULL,
    details TEXT, -- JSON formatted
    level TEXT NOT NULL
);

-- Indexes for common queries
CREATE INDEX idx_detections_timestamp ON detections(timestamp);
CREATE INDEX idx_detections_plate_text ON detections(plate_text);
CREATE INDEX idx_known_plates_plate_text ON known_plates(plate_text);

-- New table for managing video storage
CREATE TABLE video_segments (
    id TEXT PRIMARY KEY,
    file_path TEXT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    duration_seconds REAL NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    resolution TEXT NOT NULL,
    archived BOOLEAN DEFAULT FALSE,
    detection_ids TEXT -- Comma-separated list of detection IDs in this segment
);
