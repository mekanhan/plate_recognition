# app/database.py
import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Set up logging
logger = logging.getLogger(__name__)
# Ensure data directory exists
os.makedirs("data", exist_ok=True)

# Create async engine for SQLite
DATABASE_URL = "sqlite+aiosqlite:///data/license_plates.db"

engine = create_async_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite
    echo=False,  # Set to True for debug SQL output
)

# Create sessionmaker
async_session = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def get_db_session():
    """Get a database session"""
    async with async_session() as session:
        yield session

async def init_db():
    """Initialize the database tables"""
    from app.models import Base
    
    logger.info("Initializing database tables")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized")

async def run_sqlite_vacuum():
    """Run VACUUM command to optimize SQLite database"""
    import sqlite3
    try:
        logger.info("Running SQLite VACUUM command")
        conn = sqlite3.connect("data/license_plates.db")
        conn.execute("VACUUM")
        conn.close()
        logger.info("SQLite VACUUM completed")
    except Exception as e:
        logger.error(f"Error running VACUUM: {e}")
