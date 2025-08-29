#!/usr/bin/env python3
"""
Database Migration: Add Universal Detection Schema
Adds support for detecting any object type, not just vehicles/license plates
"""

import asyncio
import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text
from database.service import DatabaseService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SQL statements for creating new tables
CREATE_OBJECT_TYPES_TABLE = """
CREATE TABLE IF NOT EXISTS object_types (
    id VARCHAR(36) PRIMARY KEY,
    type_code VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    icon VARCHAR(50),
    color VARCHAR(7),
    priority INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT TRUE,
    metadata_schema JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_UNIVERSAL_DETECTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS universal_detections (
    id VARCHAR(36) PRIMARY KEY,
    camera_id VARCHAR(50) NOT NULL,
    object_type VARCHAR(50) NOT NULL,
    confidence REAL NOT NULL,
    detected_at TIMESTAMP NOT NULL,
    bbox JSON NOT NULL,
    frame_path VARCHAR(500),
    object_image_path VARCHAR(500),
    video_clip_id VARCHAR(36),
    video_thumbnail_path VARCHAR(500),
    metadata JSON DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'unverified',
    reviewed_by VARCHAR(100),
    reviewed_at TIMESTAMP,
    tags JSON DEFAULT '[]',
    flagged BOOLEAN DEFAULT FALSE,
    processing_time_ms INTEGER,
    model_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (object_type) REFERENCES object_types(type_code)
);
"""

# Create indexes for performance
CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_universal_detections_object_type ON universal_detections(object_type);",
    "CREATE INDEX IF NOT EXISTS idx_universal_detections_detected_at ON universal_detections(detected_at DESC);",
    "CREATE INDEX IF NOT EXISTS idx_universal_detections_camera_id ON universal_detections(camera_id);",
    "CREATE INDEX IF NOT EXISTS idx_universal_detections_confidence ON universal_detections(confidence);",
    "CREATE INDEX IF NOT EXISTS idx_universal_detections_status ON universal_detections(status);",
    "CREATE INDEX IF NOT EXISTS idx_universal_detections_flagged ON universal_detections(flagged);"
]

# Insert default object types
INSERT_OBJECT_TYPES = """
INSERT OR IGNORE INTO object_types (id, type_code, display_name, icon, color, priority, metadata_schema)
VALUES 
    (
        '1', 'vehicle', 'Vehicle', 'fas fa-car', '#4361ee', 1,
        '{"plate_text": {"type": "string", "required": false}, "vehicle_type": {"type": "string", "enum": ["sedan", "suv", "truck", "van", "motorcycle", "bus"]}, "color": {"type": "string"}, "make": {"type": "string"}, "model": {"type": "string"}}'
    ),
    (
        '2', 'person', 'Person', 'fas fa-user', '#00b4d8', 2,
        '{"age_range": {"type": "string", "enum": ["child", "teenager", "adult", "elderly"]}, "gender": {"type": "string", "enum": ["male", "female", "unknown"]}, "clothing": {"type": "string"}, "action": {"type": "string"}}'
    ),
    (
        '3', 'package', 'Package', 'fas fa-box', '#f77f00', 3,
        '{"size": {"type": "string", "enum": ["small", "medium", "large"]}, "carrier": {"type": "string"}, "label_visible": {"type": "boolean"}, "condition": {"type": "string"}}'
    ),
    (
        '4', 'animal', 'Animal', 'fas fa-paw', '#06ffa5', 4,
        '{"species": {"type": "string"}, "size": {"type": "string"}, "behavior": {"type": "string"}, "collar_visible": {"type": "boolean"}}'
    ),
    (
        '5', 'bicycle', 'Bicycle', 'fas fa-bicycle', '#9b59b6', 5,
        '{"type": {"type": "string", "enum": ["road", "mountain", "electric"]}, "rider_present": {"type": "boolean"}}'
    );
"""

async def migrate_existing_detections(db: DatabaseService):
    """Migrate existing license plate detections to universal format"""
    try:
        # Check if there are existing detections to migrate
        engine = await db.get_engine()
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT COUNT(*) as count FROM detections"))
            row = result.fetchone()
            count = row[0] if row else 0
        
        if count == 0:
            logger.info("No existing detections to migrate")
            return
        
        logger.info(f"Migrating {count} existing detections to universal format...")
        
        # Migrate detections in batches
        batch_size = 1000  # Increase batch size for faster processing
        offset = 0
        
        while offset < count:
            # Get batch of old detections
            query = f"""
                SELECT * FROM detections 
                ORDER BY created_at 
                LIMIT {batch_size} OFFSET {offset}
            """
            async with engine.begin() as conn:
                result = await conn.execute(text(query))
                detections = [row._asdict() for row in result.fetchall()]
            
            # Prepare batch data for bulk insert
            batch_data = []
            for detection in detections:
                # Prepare bbox from vehicle_bbox or plate_bbox
                bbox = detection.get('vehicle_bbox', detection.get('plate_bbox', '[]'))
                if isinstance(bbox, str):
                    try:
                        bbox_list = json.loads(bbox)
                        if len(bbox_list) >= 4:
                            bbox = json.dumps({
                                "x": bbox_list[0],
                                "y": bbox_list[1],
                                "width": bbox_list[2] - bbox_list[0],
                                "height": bbox_list[3] - bbox_list[1]
                            })
                        else:
                            bbox = '{"x": 0, "y": 0, "width": 100, "height": 100}'
                    except:
                        bbox = '{"x": 0, "y": 0, "width": 100, "height": 100}'
                
                # Prepare metadata
                metadata = {
                    "plate_text": detection.get('plate_text', ''),
                    "vehicle_type": detection.get('vehicle_type', ''),
                    "ocr_confidence": detection.get('ocr_confidence', 0),
                    "group_id": detection.get('group_id', ''),
                    "is_best_shot": detection.get('is_best_shot', False)
                }
                
                # Determine status based on confidence
                status = 'verified' if detection.get('confidence', 0) > 0.8 else 'unverified'
                
                batch_data.append({
                    'id': detection['id'],
                    'camera_id': detection['camera_id'],
                    'object_type': 'vehicle',  # All existing detections are vehicles
                    'confidence': detection.get('confidence', 0),
                    'detected_at': detection.get('detected_at', datetime.now().isoformat()),
                    'bbox': bbox,
                    'frame_path': detection.get('frame_path', ''),
                    'object_image_path': detection.get('plate_image_path', ''),
                    'video_clip_id': detection.get('video_clip_id', ''),
                    'metadata': json.dumps(metadata),
                    'status': status,
                    'created_at': detection.get('created_at', datetime.now().isoformat())
                })
            
            # Bulk insert the batch
            if batch_data:
                insert_query = """
                    INSERT OR IGNORE INTO universal_detections (
                        id, camera_id, object_type, confidence, detected_at,
                        bbox, frame_path, object_image_path, video_clip_id,
                        metadata, status, created_at
                    ) VALUES (:id, :camera_id, :object_type, :confidence, :detected_at,
                             :bbox, :frame_path, :object_image_path, :video_clip_id,
                             :metadata, :status, :created_at)
                """
                async with engine.begin() as conn:
                    await conn.execute(text(insert_query), batch_data)
            
            offset += batch_size
            logger.info(f"Migrated {min(offset, count)}/{count} detections...")
        
        logger.info("✅ Migration completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Error during migration: {e}")
        raise

async def run_migration():
    """Run the database migration"""
    db = DatabaseService()
    
    try:
        logger.info("🚀 Starting Universal Detection Schema Migration...")
        
        # Get engine once
        engine = await db.get_engine()
        
        # Create object_types table
        logger.info("Creating object_types table...")
        async with engine.begin() as conn:
            await conn.execute(text(CREATE_OBJECT_TYPES_TABLE))
        
        # Create universal_detections table
        logger.info("Creating universal_detections table...")
        async with engine.begin() as conn:
            await conn.execute(text(CREATE_UNIVERSAL_DETECTIONS_TABLE))
        
        # Create indexes
        logger.info("Creating indexes for performance...")
        async with engine.begin() as conn:
            for index_query in CREATE_INDEXES:
                await conn.execute(text(index_query))
        
        # Insert default object types
        logger.info("Inserting default object types...")
        async with engine.begin() as conn:
            await conn.execute(text(INSERT_OBJECT_TYPES))
        
        # Migrate existing detections
        await migrate_existing_detections(db)
        
        # Verify migration
        logger.info("Verifying migration...")
        
        # Check object types
        async with engine.begin() as conn:
            types_result = await conn.execute(text("SELECT COUNT(*) as count FROM object_types"))
            types_count = types_result.fetchone()[0]
            logger.info(f"✅ Object types created: {types_count}")
        
        # Check universal detections
        async with engine.begin() as conn:
            detections_result = await conn.execute(text("SELECT COUNT(*) as count FROM universal_detections"))
            detections_count = detections_result.fetchone()[0]
            logger.info(f"✅ Universal detections: {detections_count}")
        
        logger.info("✅ Migration completed successfully!")
        
        # Display object types
        logger.info("\n📋 Available Object Types:")
        async with engine.begin() as conn:
            types_result = await conn.execute(text("SELECT type_code, display_name, icon, color FROM object_types ORDER BY priority"))
            types = [row._asdict() for row in types_result.fetchall()]
            for obj_type in types:
                logger.info(f"  - {obj_type['display_name']} ({obj_type['type_code']}): {obj_type['icon']} {obj_type['color']}")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(run_migration())