#!/usr/bin/env python3
"""
System Hardening Validation Script
Validates that all hardening improvements are working correctly
"""
import sys
import asyncio
import json
import requests
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_configuration_system():
    """Test configuration management"""
    print("📋 Testing Configuration Management...")
    try:
        from config.app_config import get_config
        
        config = get_config()
        assert config is not None
        
        # Test database URL generation
        db_url = config.get_database_url()
        assert 'sqlite+aiosqlite' in db_url
        assert 'license_plates.db' in db_url
        
        print("   ✅ Configuration loading and database URL generation")
        return True
    except Exception as e:
        print(f"   ❌ Configuration test failed: {e}")
        return False

async def test_database_hardening():
    """Test database hardening features"""
    print("\n💾 Testing Database Hardening...")
    success_count = 0
    
    try:
        from database.db_config import db_config, check_database_health
        
        # Test 1: Database initialization
        engine = await db_config.init_engine()
        assert engine is not None
        print("   ✅ Database engine initialization")
        success_count += 1
        
        # Test 2: Health check
        health = await check_database_health()
        assert health['status'] == 'healthy'
        assert health['database_exists'] is True
        print("   ✅ Database health check")
        success_count += 1
        
        # Test 3: WAL mode verification
        if health.get('wal_enabled'):
            print("   ✅ WAL mode enabled for concurrent access")
            success_count += 1
        else:
            print("   ⚠️  WAL mode not enabled")
        
        # Test 4: Session management
        async with db_config.get_session() as session:
            from sqlalchemy import text
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1
        print("   ✅ Database session management")
        success_count += 1
        
        await db_config.close()
        return success_count >= 3
        
    except Exception as e:
        print(f"   ❌ Database hardening test failed: {e}")
        return False

async def test_database_maintenance():
    """Test database maintenance utilities"""
    print("\n🔧 Testing Database Maintenance...")
    try:
        from database.maintenance import DatabaseMaintenance
        
        maintenance = DatabaseMaintenance()
        
        # Test integrity check
        result = await maintenance.check_integrity()
        assert result is True
        print("   ✅ Database integrity check")
        
        # Test statistics update
        stats = await maintenance.update_statistics()
        assert isinstance(stats, dict)
        print("   ✅ Database statistics update")
        
        return True
    except Exception as e:
        print(f"   ❌ Database maintenance test failed: {e}")
        return False

def test_api_health_endpoints():
    """Test health monitoring API endpoints"""
    print("\n📊 Testing Health Monitoring APIs...")
    success_count = 0
    
    endpoints = [
        ('Database Health', 'http://localhost:8001/api/health/database'),
        ('Services Health', 'http://localhost:8001/api/health/services'),
        ('Storage Health', 'http://localhost:8001/api/health/storage'),
    ]
    
    for name, url in endpoints:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'status' in data:
                    print(f"   ✅ {name} endpoint working")
                    success_count += 1
                else:
                    print(f"   ⚠️  {name} endpoint missing status field")
            else:
                print(f"   ⚠️  {name} endpoint returned {response.status_code}")
        except requests.RequestException:
            print(f"   ⚠️  {name} endpoint not accessible (service may be down)")
    
    return success_count >= 2

def test_service_health():
    """Test overall service health"""
    print("\n🌐 Testing Service Health...")
    success_count = 0
    
    services = [
        ('Main API', 'http://localhost:8001/docs'),
        ('Recording Service', 'http://localhost:8002/health'),
        ('Frontend', 'http://localhost:8080/'),
    ]
    
    for name, url in services:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code in [200, 404]:  # 404 is OK for some endpoints
                print(f"   ✅ {name} service responding")
                success_count += 1
            else:
                print(f"   ⚠️  {name} service returned {response.status_code}")
        except requests.RequestException:
            print(f"   ❌ {name} service not accessible")
    
    return success_count >= 2

def test_recording_functionality():
    """Test recording service functionality"""
    print("\n📹 Testing Recording Functionality...")
    try:
        response = requests.get('http://localhost:8002/recordings/status', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('is_running') and data.get('active_recorders', 0) > 0:
                print("   ✅ Recording service active with cameras")
                return True
            else:
                print("   ⚠️  Recording service running but no active cameras")
                return False
        else:
            print("   ❌ Recording service not responding")
            return False
    except requests.RequestException:
        print("   ❌ Recording service not accessible")
        return False

def test_database_performance():
    """Test database performance optimizations"""
    print("\n⚡ Testing Database Performance...")
    try:
        response = requests.get('http://localhost:8001/api/health/database', timeout=5)
        if response.status_code == 200:
            data = response.json()
            details = data.get('details', {})
            
            success_count = 0
            
            # Check WAL mode
            if details.get('wal_enabled'):
                print("   ✅ WAL mode enabled")
                success_count += 1
            
            # Check database size is reasonable
            db_size = details.get('database_size', 0)
            if db_size > 0:
                print(f"   ✅ Database operational (size: {db_size / 1024 / 1024:.1f}MB)")
                success_count += 1
            
            # Check tables exist
            tables = details.get('tables', [])
            if len(tables) > 0:
                print(f"   ✅ Database tables present ({len(tables)} tables)")
                success_count += 1
            
            return success_count >= 2
        else:
            print("   ❌ Cannot access database health endpoint")
            return False
    except Exception as e:
        print(f"   ❌ Database performance test failed: {e}")
        return False

def create_summary_report(results):
    """Create a summary report of test results"""
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print("\n" + "=" * 60)
    print("🔧 SYSTEM HARDENING VALIDATION SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:<35} {status}")
    
    print("-" * 60)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL HARDENING TESTS PASSED!")
        print("💪 System is production-ready with hardened configuration")
        return 0
    elif passed_tests >= total_tests * 0.8:
        print("\n⚠️  Most tests passed - Minor issues detected")
        print("🔍 Review failed tests before production deployment")
        return 1
    else:
        print("\n❌ SIGNIFICANT ISSUES DETECTED")
        print("🚫 System requires attention before production use")
        return 2

async def main():
    """Run all validation tests"""
    print("🔒 SYSTEM HARDENING VALIDATION")
    print("Validating all hardening improvements are working correctly...\n")
    
    results = {}
    
    # Run all tests
    results["Configuration Management"] = test_configuration_system()
    results["Database Hardening"] = await test_database_hardening()
    results["Database Maintenance"] = await test_database_maintenance()
    results["Health Monitoring APIs"] = test_api_health_endpoints()
    results["Service Health"] = test_service_health()
    results["Recording Functionality"] = test_recording_functionality()
    results["Database Performance"] = test_database_performance()
    
    return create_summary_report(results)

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))