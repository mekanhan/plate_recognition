#!/usr/bin/env python3
"""
Update Database Schema
Migrate existing database to match current models
"""
import asyncio
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from database.service import DatabaseService
from database.models import Base

async def main():
    """Update database schema"""
    print("Updating database schema...")
    
    db_service = DatabaseService()
    
    # This will create any missing tables and columns
    await db_service.init_db()
    
    print("Database schema updated successfully!")

if __name__ == "__main__":
    asyncio.run(main())