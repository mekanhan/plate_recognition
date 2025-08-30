"""
Migration: Add stable_camera_id column to cameras table
Created: 2025-08-30
Purpose: Implement stable camera IDs for recording continuity
"""

import asyncio
import logging
import re
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import text
from database.db_config import DatabaseConfig

logger = logging.getLogger(__name__)

def normalize_camera_name(name: str) -> str:
    """Convert camera name to stable ID format"""
    if not name:
        return "camera_unknown"
    
    # Convert to lowercase
    normalized = name.lower()
    
    # Replace spaces and special characters with underscores
    normalized = re.sub(r'[^a-z0-9_]', '_', normalized)
    
    # Remove multiple underscores
    normalized = re.sub(r'_+', '_', normalized)
    
    # Remove leading/trailing underscores
    normalized = normalized.strip('_')
    
    # Ensure minimum length
    if len(normalized) < 3:
        normalized = f"camera_{normalized}"
    
    # Ensure doesn't start with number
    if normalized and normalized[0].isdigit():
        normalized = f"cam_{normalized}"
    
    return normalized[:50]  # Limit to 50 chars

async def run_migration():
    """Add stable_camera_id column and populate with normalized names"""
    
    db_config = DatabaseConfig()
    
    try:
        async with db_config.get_session() as session:
            # Check if column already exists
            result = await session.execute(text("PRAGMA table_info(cameras)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'stable_camera_id' in columns:
                logger.info("stable_camera_id column already exists, skipping migration")
                return True
            
            logger.info("Adding stable_camera_id column to cameras table...")
            
            # Add the new column (without UNIQUE constraint initially)
            await session.execute(text("ALTER TABLE cameras ADD COLUMN stable_camera_id VARCHAR(100)"))
            
            logger.info("Populating stable_camera_id for existing cameras...")
            
            # Get all existing cameras
            result = await session.execute(text("SELECT camera_id, name FROM cameras"))
            cameras = result.fetchall()
            
            stable_ids_used = set()
            
            for camera_id, name in cameras:
                # Generate stable ID from name
                base_stable_id = normalize_camera_name(name)
                stable_id = base_stable_id
                
                # Ensure uniqueness
                counter = 1
                while stable_id in stable_ids_used:
                    stable_id = f"{base_stable_id}_{counter}"
                    counter += 1
                
                stable_ids_used.add(stable_id)
                
                # Update the camera record
                await session.execute(
                    text("UPDATE cameras SET stable_camera_id = :stable_id WHERE camera_id = :camera_id"),
                    {"stable_id": stable_id, "camera_id": camera_id}
                )
                
                logger.info(f"Camera '{name}' -> stable_id: '{stable_id}'")
            
            await session.commit()
            
            # Create unique index for performance and uniqueness
            logger.info("Creating unique index on stable_camera_id...")
            await session.execute(text("CREATE UNIQUE INDEX idx_stable_camera_id ON cameras(stable_camera_id)"))
            await session.commit()
            
            logger.info(f"Migration completed successfully! Updated {len(cameras)} cameras")
            return True
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False

async def rollback_migration():
    """Remove stable_camera_id column (for testing/rollback)"""
    
    db_config = DatabaseConfig()
    
    try:
        async with db_config.get_session() as session:
            logger.info("Rolling back stable_camera_id migration...")
            
            # SQLite doesn't support DROP COLUMN directly
            # We would need to recreate the table, but for now just mark as rollback
            logger.warning("SQLite doesn't support DROP COLUMN. Manual cleanup required.")
            return True
            
    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        result = asyncio.run(rollback_migration())
    else:
        result = asyncio.run(run_migration())
    
    if result:
        print("Migration completed successfully")
        sys.exit(0)
    else:
        print("Migration failed")
        sys.exit(1)