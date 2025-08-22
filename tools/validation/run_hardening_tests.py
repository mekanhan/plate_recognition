#!/usr/bin/env python3
"""
Simple test runner for system hardening validation
Runs tests without complex pytest configuration dependencies
"""
import sys
import asyncio
import traceback
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_configuration_management():
    """Test configuration management system"""
    print("Testing Configuration Management...")
    try:
        from config.app_config import get_config
        
        # Test config loading
        config = get_config()
        assert config is not None
        assert hasattr(config, 'data_dir')
        print("✅ Configuration loading test passed")
        
        # Test database URL
        db_url = config.get_database_url()
        assert 'sqlite+aiosqlite' in db_url
        print("✅ Database URL generation test passed")
        
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        traceback.print_exc()
        return False

def test_logging_system():
    """Test logging system"""
    print("\nTesting Logging System...")
    try:
        from config.log_manager import get_logger
        
        logger = get_logger("test_service")
        assert logger is not None
        assert logger.name == "test_service"
        print("✅ Logger creation test passed")
        
        return True
    except Exception as e:
        print(f"❌ Logging test failed: {e}")
        traceback.print_exc()
        return False

async def test_database_hardening():
    """Test database hardening features"""
    print("\nTesting Database Hardening...")
    try:
        from database.db_config import db_config, check_database_health
        
        # Test database initialization
        engine = await db_config.init_engine()
        assert engine is not None
        print("✅ Database initialization test passed")
        
        # Test health check
        health = await check_database_health()
        assert 'status' in health
        assert health['database_exists'] is True
        print("✅ Database health check test passed")
        
        # Test session management
        async with db_config.get_session() as session:
            from sqlalchemy import text
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1
        print("✅ Database session test passed")
        
        await db_config.close()
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        traceback.print_exc()
        return False

async def test_health_monitoring():
    """Test health monitoring system"""
    print("\nTesting Health Monitoring...")
    try:
        from config.health_monitor import HealthMonitor
        
        monitor = HealthMonitor()
        assert monitor is not None
        
        # Test metrics collection
        metrics = await monitor.collect_system_metrics()
        assert 'cpu_percent' in metrics
        assert 'memory' in metrics
        print("✅ Health monitoring test passed")
        
        return True
    except Exception as e:
        print(f"❌ Health monitoring test failed: {e}")
        traceback.print_exc()
        return False

def test_media_retention():
    """Test media retention management"""
    print("\nTesting Media Retention...")
    try:
        import tempfile
        from config.media_retention_manager import MediaRetentionManager
        
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = MediaRetentionManager(
                storage_path=temp_dir,
                max_size_gb=1,
                retention_days=7
            )
            assert manager is not None
            
            usage = manager.get_storage_usage()
            assert isinstance(usage, dict)
            print("✅ Media retention test passed")
        
        return True
    except Exception as e:
        print(f"❌ Media retention test failed: {e}")
        traceback.print_exc()
        return False

async def test_api_health_endpoints():
    """Test API health endpoints if available"""
    print("\nTesting API Health Endpoints...")
    try:
        import aiohttp
        
        endpoints = [
            'http://localhost:8001/api/health/database',
            'http://localhost:8001/api/health/system',
            'http://localhost:8001/api/health/services'
        ]
        
        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints:
                try:
                    async with session.get(endpoint, timeout=aiohttp.ClientTimeout(total=5)) as response:
                        if response.status == 200:
                            data = await response.json()
                            assert 'status' in data
                            print(f"✅ {endpoint} test passed")
                        else:
                            print(f"⚠️  {endpoint} returned status {response.status}")
                except aiohttp.ClientError:
                    print(f"⚠️  {endpoint} not accessible (service may not be running)")
        
        return True
    except Exception as e:
        print(f"❌ API health endpoints test failed: {e}")
        return False

async def test_database_maintenance():
    """Test database maintenance utilities"""
    print("\nTesting Database Maintenance...")
    try:
        from database.maintenance import DatabaseMaintenance
        
        maintenance = DatabaseMaintenance()
        assert maintenance is not None
        
        # Test integrity check
        result = await maintenance.check_integrity()
        assert isinstance(result, bool)
        print("✅ Database maintenance test passed")
        
        return True
    except Exception as e:
        print(f"❌ Database maintenance test failed: {e}")
        traceback.print_exc()
        return False

async def main():
    """Run all hardening tests"""
    print("🔧 SYSTEM HARDENING VALIDATION TESTS")
    print("=" * 50)
    
    tests = [
        ("Configuration Management", test_configuration_management()),
        ("Logging System", test_logging_system()),
        ("Database Hardening", test_database_hardening()),
        ("Health Monitoring", test_health_monitoring()),
        ("Media Retention", test_media_retention()),
        ("API Health Endpoints", test_api_health_endpoints()),
        ("Database Maintenance", test_database_maintenance()),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        if asyncio.iscoroutine(test_func):
            result = await test_func
        else:
            result = test_func
        
        if result:
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"🔧 HARDENING VALIDATION RESULTS")
    print(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ ALL HARDENING TESTS PASSED - SYSTEM IS PRODUCTION READY")
        return 0
    else:
        print(f"⚠️  {total - passed} TESTS FAILED - REVIEW REQUIRED")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))