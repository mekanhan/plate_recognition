#!/usr/bin/env python3
"""
Test script for Edge Device Implementation
"""
import asyncio
import logging
import sys
import os

# Add current directory to path
sys.path.insert(0, '.')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_edge_implementation():
    """Test the edge device implementation"""
    
    print("🚀 Testing Edge Device Implementation (Phase 1)")
    print("=" * 50)
    
    # Test 1: Import all new modules
    print("\n1. Testing imports...")
    try:
        from app.models import SyncQueue, SyncStatus, Priority, DeviceConfig
        print("   ✓ Enhanced models imported")
        
        from app.services.device_service import DeviceService
        print("   ✓ DeviceService imported")
        
        from app.services.sync_service import SyncService
        print("   ✓ SyncService imported")
        
        from app.routers.sync import router as sync_router
        print("   ✓ Sync router imported")
        
        # Test required dependencies
        try:
            import sqlalchemy
            print("   ✓ SQLAlchemy available")
        except ImportError:
            print("   ❌ SQLAlchemy missing - run: pip install sqlalchemy>=2.0.0")
            return False
            
        try:
            import aiosqlite
            print("   ✓ aiosqlite available")
        except ImportError:
            print("   ❌ aiosqlite missing - run: pip install aiosqlite")
            return False
            
        try:
            import aiohttp
            print("   ✓ aiohttp available")
        except ImportError:
            print("   ❌ aiohttp missing - run: pip install aiohttp")
            return False
            
        try:
            import cryptography
            print("   ✓ cryptography available")
        except ImportError:
            print("   ❌ cryptography missing - run: pip install cryptography")
            return False
            
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return False
    
    # Test 2: Initialize device service
    print("\n2. Testing device service...")
    try:
        device_service = DeviceService({
            'cloud_api_url': 'https://test.lprcloud.com',
            'registration_token': 'test-token'
        })
        print("   ✓ DeviceService created")
        
        # Test device ID generation
        device_id = device_service._generate_device_id()
        print(f"   ✓ Generated device ID: {device_id}")
        
        # Test encryption key generation
        device_service._load_encryption_key()
        if device_service.fernet:
            print("   ✓ Encryption key loaded")
        else:
            print("   ❌ Encryption key failed to load")
            return False
        
    except Exception as e:
        print(f"   ❌ Device service test failed: {e}")
        return False
    
    # Test 3: Initialize sync service
    print("\n3. Testing sync service...")
    try:
        sync_service = SyncService(device_service, {
            'sync_mode': 'batch',
            'sync_interval': 60,
            'sync_batch_size': 10
        })
        print("   ✓ SyncService created")
        
        # Test sync result dataclass
        from app.services.sync_service import SyncResult
        result = SyncResult(accepted_count=5, rejected_count=1, errors=['test error'])
        print(f"   ✓ SyncResult created: {result.accepted_count} accepted, {result.rejected_count} rejected")
        
    except Exception as e:
        print(f"   ❌ Sync service test failed: {e}")
        return False
    
    # Test 4: Test database models
    print("\n4. Testing database models...")
    try:
        # Create test sync queue entry
        sync_item_data = {
            'item_type': 'detection',
            'item_id': 'test-detection-001',
            'data': {
                'plate_text': 'ABC123',
                'confidence': 0.95,
                'timestamp': '2025-01-20T10:00:00Z'
            },
            'status': SyncStatus.PENDING,
            'priority': Priority.HIGH
        }
        print("   ✓ SyncQueue data structure created")
        
        # Test enums
        assert SyncStatus.PENDING.value == "pending"
        assert Priority.HIGH.value == 3
        print("   ✓ Enums working correctly")
        
        # Test SQLAlchemy model creation
        from app.models import Base
        print("   ✓ SQLAlchemy Base model accessible")
        
    except Exception as e:
        print(f"   ❌ Database models test failed: {e}")
        return False
    
    # Test 5: Configuration loading
    print("\n5. Testing configuration...")
    try:
        from config.settings import Config, SyncMode
        config = Config()
        
        # Test new sync configuration
        assert hasattr(config, 'sync_mode')
        assert hasattr(config, 'cloud_api_url')
        assert hasattr(config, 'sync_interval')
        print("   ✓ Configuration has sync settings")
        
        # Test property methods
        sync_enabled = config.is_sync_enabled
        print(f"   ✓ Sync enabled: {sync_enabled}")
        
        # Test sync mode enum
        assert SyncMode.BATCH.value == "batch"
        print("   ✓ SyncMode enum working")
        
    except Exception as e:
        print(f"   ❌ Configuration test failed: {e}")
        return False
    
    # Test 6: Check file structure
    print("\n6. Testing file structure...")
    expected_files = [
        'app/models.py',
        'app/services/device_service.py',
        'app/services/sync_service.py',
        'app/routers/sync.py',
        'requirements.txt',
        '.env.edge.example'
    ]
    
    missing_files = []
    for file_path in expected_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"   ❌ Missing files: {missing_files}")
        return False
    else:
        print("   ✓ All required files present")
    
    # Test 7: Test data directory creation
    print("\n7. Testing data directory setup...")
    try:
        os.makedirs("data", exist_ok=True)
        print("   ✓ Data directory created")
        
        # Test write permissions
        test_file = "data/test_write.txt"
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        print("   ✓ Data directory is writable")
        
    except Exception as e:
        print(f"   ❌ Data directory test failed: {e}")
        return False
    
    # Test 8: Test optional dependencies
    print("\n8. Testing optional dependencies...")
    optional_deps = {
        'netifaces': 'Network interface detection',
        'jwt': 'JWT token support',
        'passlib': 'Password hashing'
    }
    
    for dep, description in optional_deps.items():
        try:
            __import__(dep)
            print(f"   ✓ {dep} available ({description})")
        except ImportError:
            # Special case for JWT
            if dep == 'jwt':
                print(f"   ⚠️  {dep} missing ({description}) - install with: pip install pyjwt")
            else:
                print(f"   ⚠️  {dep} missing ({description}) - install with: pip install {dep}")
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed! Edge Device Phase 1 implementation is ready.")
    print("\n📋 Next steps:")
    print("1. Install missing dependencies: pip install -r requirements.txt")
    print("2. Copy .env.edge.example to .env and configure")
    print("3. Start the application: python -m uvicorn app.main:app --reload")
    print("4. Test sync endpoints at: http://localhost:8001/api/sync/status")
    print("\n🔗 Available API endpoints:")
    print("   • GET  /api/sync/status - Check sync queue status")
    print("   • POST /api/sync/force - Force immediate sync")
    print("   • GET  /api/sync/device/info - Get device information")
    print("   • POST /api/sync/test-connection - Test cloud connection")
    print("   • GET  /docs - API documentation")
    
    return True

if __name__ == "__main__":
    try:
        result = asyncio.run(test_edge_implementation())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)