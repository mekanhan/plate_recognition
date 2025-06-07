"""
Tests for the storage service to ensure detections are properly saved.
"""
import pytest
import asyncio
import json
import os
import time
from unittest.mock import patch, mock_open
from app.services.storage_service import StorageService

@pytest.mark.asyncio
async def test_initialize():
    """Test storage service initialization"""
    # Mock directories to avoid file system operations
    with patch('os.makedirs') as mock_makedirs:
        storage_service = StorageService()
        await storage_service.initialize()
        
        # Check if directories were created
        assert mock_makedirs.call_count == 2
        
        # Verify initialization fields
        assert storage_service.license_plates_dir == "data/license_plates"
        assert storage_service.enhanced_plates_dir == "data/enhanced_plates"
        assert storage_service.session_timestamp is not None
        assert storage_service.session_file is not None
        assert storage_service.task is not None

@pytest.mark.asyncio
async def test_add_detections():
    """Test adding detections to storage"""
    storage_service = StorageService()
    
    # Initialize without file system operations
    with patch('os.makedirs'):
        with patch('asyncio.create_task'):
            await storage_service.initialize()
    
    # Mock the save operation
    with patch.object(storage_service, '_save_data') as mock_save:
        test_detections = [
            {
                "detection_id": "test1",
                "plate_text": "ABC123",
                "confidence": 0.9,
                "timestamp": time.time()
            },
            {
                "detection_id": "test2",
                "plate_text": "XYZ789",
                "confidence": 0.85,
                "timestamp": time.time()
            }
        ]
        
        # Add detections
        await storage_service.add_detections(test_detections)
        
        # Verify detections were added
        assert len(storage_service.plate_database["detections"]) == 2
        assert storage_service.plate_database["detections"][0]["detection_id"] == "test1"
        assert storage_service.plate_database["detections"][1]["detection_id"] == "test2"
        
        # Verify save was called
        assert mock_save.called

@pytest.mark.asyncio
async def test_save_data():
    """Test saving data to files"""
    storage_service = StorageService()
    
    # Initialize without file system operations
    with patch('os.makedirs'):
        with patch('asyncio.create_task'):
            await storage_service.initialize()
    
    # Add some test detections
    storage_service.plate_database["detections"] = [
        {
            "detection_id": "test1",
            "plate_text": "ABC123",
            "confidence": 0.9,
            "timestamp": time.time()
        }
    ]
    
    # Mock file operations
    m = mock_open()
    with patch('builtins.open', m):
        await storage_service._save_data()
        
        # Verify files were opened for writing
        m.assert_called()

@pytest.mark.asyncio
async def test_empty_detections_not_saved():
    """Test that empty detections are not saved to file"""
    storage_service = StorageService()
    
    # Initialize without file system operations
    with patch('os.makedirs'):
        with patch('asyncio.create_task'):
            await storage_service.initialize()
    
    # Ensure plate_database has empty detections
    storage_service.plate_database["detections"] = []
    
    # Mock file operations
    m = mock_open()
    with patch('builtins.open', m):
        await storage_service._save_data()
        
        # Verify file was not opened (since detections are empty)
        assert not m.called

@pytest.mark.asyncio
async def test_periodic_save():
    """Test the periodic save functionality"""
    storage_service = StorageService()
    
    # Set a shorter save interval for testing
    storage_service.save_interval = 0.1
    
    # Initialize without file system operations
    with patch('os.makedirs'):
        await storage_service.initialize()
    
    # Mock the save operation
    with patch.object(storage_service, '_save_data') as mock_save:
        # Add a detection to ensure there's data to save
        storage_service.plate_database["detections"] = [{"detection_id": "test"}]
        
        # Let the periodic save run for a short time
        await asyncio.sleep(0.2)
        
        # Cancel the task to clean up
        storage_service.task.cancel()
        try:
            await storage_service.task
        except asyncio.CancelledError:
            pass
        
        # Verify save was called at least once
        assert mock_save.called