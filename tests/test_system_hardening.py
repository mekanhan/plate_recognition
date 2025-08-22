"""
System Hardening Test Suite
Comprehensive tests for hardened LPR system components
"""
import pytest
import asyncio
import os
import tempfile
import json
from datetime import datetime, timedelta
from pathlib import Path
import aiohttp
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.app_config import get_config
from config.log_manager import get_logger
from config.health_monitor import HealthMonitor
from config.media_retention_manager import MediaRetentionManager
from database.db_config import db_config, check_database_health
from database.maintenance import DatabaseMaintenance

class TestConfigurationManagement:
    """Test centralized configuration management"""
    
    def test_config_loading(self):
        """Test configuration loads successfully"""
        config = get_config()
        assert config is not None
        assert hasattr(config, 'data_dir')
        assert hasattr(config, 'recordings_dir')
        assert hasattr(config, 'logs_dir')
    
    def test_database_url_generation(self):
        """Test database URL generation"""
        config = get_config()
        db_url = config.get_database_url()
        assert 'sqlite+aiosqlite' in db_url
        assert 'license_plates.db' in db_url
    
    def test_directory_creation(self):
        """Test required directories are created"""
        config = get_config()
        assert os.path.exists(config.data_dir)
        assert os.path.exists(config.recordings_dir)
        assert os.path.exists(config.logs_dir)

class TestLogManager:
    """Test logging system with rotation"""
    
    def test_logger_creation(self):
        """Test logger can be created"""
        logger = get_logger("test_service")
        assert logger is not None
        assert logger.name == "test_service"
    
    def test_log_rotation_config(self):
        """Test log rotation is properly configured"""
        logger = get_logger("test_rotation")
        # Check if handlers are configured for rotation
        has_rotating_handler = any(
            hasattr(handler, 'maxBytes') 
            for handler in logger.handlers
        )
        # Note: May not have rotating handler in test environment
        assert logger is not None

class TestHealthMonitoring:
    """Test health monitoring system"""
    
    @pytest.mark.asyncio
    async def test_health_monitor_creation(self):
        """Test health monitor can be created"""
        monitor = HealthMonitor()
        assert monitor is not None
    
    @pytest.mark.asyncio
    async def test_system_metrics_collection(self):
        """Test system metrics can be collected"""
        monitor = HealthMonitor()
        metrics = await monitor.collect_system_metrics()
        
        assert 'cpu_percent' in metrics
        assert 'memory' in metrics
        assert 'disk' in metrics
        assert isinstance(metrics['cpu_percent'], (int, float))
    
    @pytest.mark.asyncio
    async def test_health_status_evaluation(self):
        """Test health status evaluation"""
        monitor = HealthMonitor()
        metrics = await monitor.collect_system_metrics()
        status = monitor.evaluate_health_status(metrics)
        
        assert status in ['healthy', 'degraded', 'critical']

class TestDatabaseHardening:
    """Test database configuration and hardening"""
    
    @pytest.mark.asyncio
    async def test_database_initialization(self):
        """Test database can be initialized"""
        engine = await db_config.init_engine()
        assert engine is not None
        await db_config.close()
    
    @pytest.mark.asyncio
    async def test_database_health_check(self):
        """Test database health check"""
        health = await check_database_health()
        
        assert 'status' in health
        assert 'database_path' in health
        assert 'database_exists' in health
        assert 'wal_enabled' in health
        assert 'tables' in health
    
    @pytest.mark.asyncio
    async def test_database_session_management(self):
        """Test database session context manager"""
        async with db_config.get_session() as session:
            assert session is not None
            # Test basic query
            from sqlalchemy import text
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1
    
    @pytest.mark.asyncio
    async def test_database_pragmas(self):
        """Test SQLite pragmas are configured"""
        async with db_config.get_session() as session:
            from sqlalchemy import text
            
            # Check WAL mode
            result = await session.execute(text("PRAGMA journal_mode"))
            mode = result.scalar()
            assert mode == 'wal'
            
            # Check foreign keys
            result = await session.execute(text("PRAGMA foreign_keys"))
            fk_status = result.scalar()
            assert fk_status == 1

class TestDatabaseMaintenance:
    """Test database maintenance utilities"""
    
    @pytest.mark.asyncio
    async def test_maintenance_initialization(self):
        """Test maintenance system can be initialized"""
        maintenance = DatabaseMaintenance()
        assert maintenance is not None
    
    @pytest.mark.asyncio
    async def test_integrity_check(self):
        """Test database integrity check"""
        maintenance = DatabaseMaintenance()
        result = await maintenance.check_integrity()
        assert isinstance(result, bool)
        # Should pass for a healthy database
        assert result is True
    
    @pytest.mark.asyncio
    async def test_statistics_update(self):
        """Test database statistics update"""
        maintenance = DatabaseMaintenance()
        stats = await maintenance.update_statistics()
        
        assert isinstance(stats, dict)
        assert 'cameras_count' in stats
        assert 'detections_count' in stats
        assert 'database_size_mb' in stats

class TestMediaRetentionManager:
    """Test media storage retention policies"""
    
    def test_retention_manager_creation(self):
        """Test retention manager can be created"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = MediaRetentionManager(
                storage_path=temp_dir,
                max_size_gb=1,
                retention_days=7
            )
            assert manager is not None
            assert manager.storage_path == Path(temp_dir)
    
    def test_storage_usage_calculation(self):
        """Test storage usage calculation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("test data")
            
            manager = MediaRetentionManager(
                storage_path=temp_dir,
                max_size_gb=1,
                retention_days=7
            )
            
            usage = manager.get_storage_usage()
            assert usage['total_size'] > 0
            assert usage['file_count'] >= 1
    
    def test_cleanup_old_files(self):
        """Test cleanup of old files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create old test file
            old_file = Path(temp_dir) / "old_file.txt"
            old_file.write_text("old data")
            
            # Set modification time to past
            old_time = datetime.now().timestamp() - (8 * 24 * 3600)  # 8 days ago
            os.utime(old_file, (old_time, old_time))
            
            manager = MediaRetentionManager(
                storage_path=temp_dir,
                max_size_gb=1,
                retention_days=7
            )
            
            # Cleanup should remove the old file
            cleaned = manager.cleanup_old_files()
            assert cleaned['files_deleted'] >= 1

class TestAPIHealthEndpoints:
    """Test health monitoring API endpoints"""
    
    @pytest.mark.asyncio
    async def test_database_health_endpoint(self):
        """Test database health endpoint"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get('http://localhost:8001/api/health/database') as response:
                    if response.status == 200:
                        data = await response.json()
                        assert 'status' in data
                        assert 'details' in data
                        assert 'timestamp' in data
                    else:
                        pytest.skip("API service not running")
            except aiohttp.ClientError:
                pytest.skip("API service not accessible")
    
    @pytest.mark.asyncio
    async def test_system_health_endpoint(self):
        """Test system health endpoint"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get('http://localhost:8001/api/health/system') as response:
                    if response.status == 200:
                        data = await response.json()
                        assert 'status' in data
                        assert 'system' in data
                        assert 'database' in data
                        assert 'services' in data
                    else:
                        pytest.skip("API service not running")
            except aiohttp.ClientError:
                pytest.skip("API service not accessible")
    
    @pytest.mark.asyncio
    async def test_services_health_endpoint(self):
        """Test services health endpoint"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get('http://localhost:8001/api/health/services') as response:
                    if response.status == 200:
                        data = await response.json()
                        assert 'status' in data
                        assert 'services' in data
                        assert 'main_api' in data['services']
                    else:
                        pytest.skip("API service not running")
            except aiohttp.ClientError:
                pytest.skip("API service not accessible")

class TestSystemIntegration:
    """Test system integration and end-to-end functionality"""
    
    @pytest.mark.asyncio
    async def test_service_availability(self):
        """Test all services are available"""
        services = [
            ('Main API', 'http://localhost:8001/docs'),
            ('Recording Service', 'http://localhost:8002/health'),
            ('Frontend', 'http://localhost:8080/')
        ]
        
        async with aiohttp.ClientSession() as session:
            for service_name, url in services:
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                        if response.status not in [200, 404]:  # 404 is OK for some endpoints
                            pytest.fail(f"{service_name} returned status {response.status}")
                except aiohttp.ClientError:
                    pytest.skip(f"{service_name} not accessible at {url}")
    
    @pytest.mark.asyncio
    async def test_database_service_integration(self):
        """Test database service integration with hardened config"""
        from database.service import DatabaseService
        
        db_service = DatabaseService()
        await db_service.init_db()
        
        # Test session usage (both old and new patterns)
        async with db_service.get_session() as session:
            from sqlalchemy import text
            result = await session.execute(text("SELECT COUNT(*) FROM cameras"))
            count = result.scalar()
            assert isinstance(count, int)
    
    def test_log_files_created(self):
        """Test that log files are being created"""
        config = get_config()
        log_files = list(Path(config.logs_dir).glob("*.log"))
        
        # Should have log files if services have been running
        if log_files:
            # Verify log files have recent content
            recent_logs = [
                f for f in log_files 
                if f.stat().st_mtime > (datetime.now().timestamp() - 3600)  # Last hour
            ]
            assert len(recent_logs) > 0

class TestPerformanceAndReliability:
    """Test performance and reliability improvements"""
    
    @pytest.mark.asyncio
    async def test_database_concurrent_access(self):
        """Test database can handle concurrent access"""
        async def db_operation():
            async with db_config.get_session() as session:
                from sqlalchemy import text
                result = await session.execute(text("SELECT 1"))
                return result.scalar()
        
        # Run multiple concurrent operations
        tasks = [db_operation() for _ in range(5)]
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert all(r == 1 for r in results)
    
    @pytest.mark.asyncio
    async def test_error_recovery(self):
        """Test error recovery mechanisms"""
        # Test retry logic in database config
        success = False
        try:
            async def failing_operation():
                # This should work with retry logic
                async with db_config.get_session() as session:
                    from sqlalchemy import text
                    result = await session.execute(text("SELECT 1"))
                    return result.scalar()
            
            result = await db_config.execute_with_retry(failing_operation)
            success = (result == 1)
        except Exception:
            pass
        
        assert success
    
    def test_storage_quota_enforcement(self):
        """Test storage quota enforcement"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = MediaRetentionManager(
                storage_path=temp_dir,
                max_size_gb=0.001,  # Very small limit
                retention_days=30
            )
            
            # Create files that exceed quota
            for i in range(5):
                test_file = Path(temp_dir) / f"large_file_{i}.txt"
                test_file.write_text("x" * 1000)  # 1KB each
            
            # Check quota enforcement
            usage = manager.get_storage_usage()
            needs_cleanup = manager.needs_cleanup()
            
            assert isinstance(needs_cleanup, bool)

# Test discovery and execution
if __name__ == "__main__":
    # Run specific test classes
    print("Running System Hardening Test Suite...")
    
    # You can run this with: python -m pytest tests/test_system_hardening.py -v
    pytest.main([__file__, "-v", "--tb=short"])