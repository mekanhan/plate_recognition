#!/usr/bin/env python3
"""
Quick database schema update for missing filename column
"""
import asyncio
from database.service import DatabaseService
from sqlalchemy import text

async def update_schema():
    db = DatabaseService()
    await db.init_db()
    
    print("Checking video_recordings table schema...")
    
    async with db.async_session() as session:
        # Check if filename column exists
        result = await session.execute(text("PRAGMA table_info(video_recordings)"))
        columns = result.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"Current columns: {column_names}")
        
        # Check and add missing columns
        required_columns = {
            'filename': 'TEXT',
            'file_size_bytes': 'INTEGER',
            'video_codec': 'VARCHAR(20)',
            'video_width': 'INTEGER', 
            'video_height': 'INTEGER',
            'video_fps': 'INTEGER',
            'is_compressed': 'BOOLEAN',
            'compression_ratio': 'FLOAT',
            'has_audio': 'BOOLEAN'
        }
        
        for col_name, col_type in required_columns.items():
            if col_name not in column_names:
                print(f"Adding {col_name} column...")
                await session.execute(text(f"ALTER TABLE video_recordings ADD COLUMN {col_name} {col_type}"))
                await session.commit()
                print(f"✅ Added {col_name} column")
            else:
                print(f"✅ {col_name} column already exists")
    
    await db.close()
    print("Database schema update complete")

if __name__ == "__main__":
    asyncio.run(update_schema())