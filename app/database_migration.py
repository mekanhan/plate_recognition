# app/database_migration.py
import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import text
from app.database import DATABASE_URL, Base
from app.models import Camera, CameraSession, Detection

logger = logging.getLogger(__name__)

async def migrate_database():
    """Migrate database to add camera support"""
    try:
        # Create engine
        engine = create_async_engine(DATABASE_URL, echo=True)
        
        async with engine.begin() as conn:
            # Create all tables (this will only create new ones)
            await conn.run_sync(Base.metadata.create_all)
            
            # Check if camera_id column exists in detections table
            result = await conn.execute(text("""
                PRAGMA table_info(detections)
            """))
            
            columns = [row[1] for row in result.fetchall()]
            
            if 'camera_id' not in columns:
                logger.info("Adding camera_id column to detections table")
                await conn.execute(text("""
                    ALTER TABLE detections ADD COLUMN camera_id TEXT
                """))
                
                await conn.execute(text("""
                    CREATE INDEX ix_detections_camera_id ON detections(camera_id)
                """))
            
            if 'camera_name' not in columns:
                logger.info("Adding camera_name column to detections table")
                await conn.execute(text("""
                    ALTER TABLE detections ADD COLUMN camera_name TEXT
                """))
            
            # Create a default camera for existing detections
            default_camera_result = await conn.execute(text("""
                SELECT id FROM cameras WHERE name = 'Default Camera' LIMIT 1
            """))
            
            default_camera = default_camera_result.fetchone()
            
            if not default_camera:
                logger.info("Creating default camera for existing detections")
                import uuid
                default_camera_id = str(uuid.uuid4())
                
                await conn.execute(text("""
                    INSERT INTO cameras (
                        id, name, type, status, location, source_config, 
                        auto_discovered, created_at
                    ) VALUES (
                        :id, 'Default Camera', 'usb', 'offline', 'Primary Location',
                        '{"device_id": 0, "resolution": "1280x720", "fps": 30}',
                        false, datetime('now')
                    )
                """), {"id": default_camera_id})
                
                # Update existing detections to reference the default camera
                await conn.execute(text("""
                    UPDATE detections 
                    SET camera_id = :camera_id, camera_name = 'Default Camera'
                    WHERE camera_id IS NULL
                """), {"camera_id": default_camera_id})
                
                logger.info(f"Created default camera with ID: {default_camera_id}")
            
            logger.info("Database migration completed successfully")
            
        await engine.dispose()
        
    except Exception as e:
        logger.error(f"Database migration failed: {str(e)}")
        raise

async def verify_migration():
    """Verify that the migration was successful"""
    try:
        engine = create_async_engine(DATABASE_URL, echo=False)
        
        async with engine.begin() as conn:
            # Check cameras table
            result = await conn.execute(text("SELECT COUNT(*) FROM cameras"))
            camera_count = result.scalar()
            logger.info(f"Cameras table has {camera_count} records")
            
            # Check camera_sessions table
            result = await conn.execute(text("SELECT COUNT(*) FROM camera_sessions"))
            session_count = result.scalar()
            logger.info(f"Camera sessions table has {session_count} records")
            
            # Check detections table for camera_id column
            result = await conn.execute(text("""
                SELECT COUNT(*) FROM detections WHERE camera_id IS NOT NULL
            """))
            detections_with_camera = result.scalar()
            logger.info(f"Detections with camera_id: {detections_with_camera}")
            
        await engine.dispose()
        logger.info("Migration verification completed")
        
    except Exception as e:
        logger.error(f"Migration verification failed: {str(e)}")
        raise

if __name__ == "__main__":
    import sys
    import asyncio
    
    async def main():
        if len(sys.argv) > 1 and sys.argv[1] == "verify":
            await verify_migration()
        else:
            await migrate_database()
            await verify_migration()
    
    asyncio.run(main())