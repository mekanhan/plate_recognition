"""
Migration: Remove universal detection system
Created: 2025-08-30
Purpose: Clean up incomplete universal detection system to avoid confusion
"""

import asyncio
import logging
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import text
from database.db_config import DatabaseConfig

logger = logging.getLogger(__name__)

async def remove_universal_detection_system():
    """Remove universal detection table and related code references"""
    
    db_config = DatabaseConfig()
    
    try:
        async with db_config.get_session() as session:
            # Check if universal_detections table exists
            result = await session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='universal_detections'"))
            table_exists = result.fetchone() is not None
            
            if table_exists:
                logger.info("Dropping universal_detections table...")
                await session.execute(text("DROP TABLE universal_detections"))
                await session.commit()
                logger.info("universal_detections table dropped successfully")
            else:
                logger.info("universal_detections table does not exist, skipping")
            
            # Check for any related indexes
            result = await session.execute(text("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE '%universal_detection%'"))
            indexes = result.fetchall()
            
            for index in indexes:
                index_name = index[0]
                logger.info(f"Dropping index {index_name}...")
                await session.execute(text(f"DROP INDEX {index_name}"))
                await session.commit()
            
            logger.info("Universal detection system cleanup completed successfully")
            return True
            
    except Exception as e:
        logger.error(f"Universal detection cleanup failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(remove_universal_detection_system())
    
    if result:
        print("Universal detection system removed successfully")
        print("\nNext steps:")
        print("1. Remove universal detection methods from database/service.py")
        print("2. Update feature flags in config/features.json") 
        print("3. Remove references from API endpoints")
        sys.exit(0)
    else:
        print("Universal detection cleanup failed")
        sys.exit(1)