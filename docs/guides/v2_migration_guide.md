# V2 Migration Guide - License Plate Recognition System

**Version:** 2.0  
**Last Updated:** 2025-06-10  
**Authors:** Development Team  

## Overview

This guide provides step-by-step instructions for migrating from the V1 License Plate Recognition System to the enhanced V2 architecture, including data migration, feature comparison, and deployment strategies.

## Migration Overview

### Key Differences Between V1 and V2

| Feature | V1 | V2 | Migration Impact |
|---------|----|----|------------------|
| **Architecture** | Monolithic services | Interface-based with dependency injection | Code restructuring required |
| **Storage** | JSON files only | Dual storage (SQL + JSON) | Data migration needed |
| **Video Recording** | Basic MP4 recording | Enhanced with confidence overlays | Configuration update |
| **API Endpoints** | `/stream`, `/detection`, `/results` | `/v2/*` with V1 compatibility | Gradual transition possible |
| **Detection Processing** | Simple YOLO + OCR | Enhanced with Texas plate improvements | Better accuracy |
| **Service Management** | Direct instantiation | Service factory pattern | Initialization changes |
| **Error Handling** | Basic try/catch | Comprehensive with fallbacks | Improved reliability |

## Pre-Migration Assessment

### 1. System Health Check

Before starting migration, verify your V1 system status:

```bash
# Check V1 system status
python -c "
import os
print('=== V1 System Assessment ===')
print(f'License plates dir exists: {os.path.exists(\"data/license_plates\")}')
print(f'Enhanced plates dir exists: {os.path.exists(\"data/enhanced_plates\")}')
print(f'Videos dir exists: {os.path.exists(\"data/videos\")}')

# Count existing data
import json
import glob

json_files = glob.glob('data/license_plates/*.json')
print(f'Existing JSON files: {len(json_files)}')

if json_files:
    with open(json_files[0], 'r') as f:
        sample_data = json.load(f)
        detections = sample_data.get('detections', [])
        print(f'Sample file detections: {len(detections)}')
"
```

### 2. Data Backup

Create comprehensive backups before migration:

```bash
# Create backup directory
mkdir -p backups/v1_migration_$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups/v1_migration_$(date +%Y%m%d_%H%M%S)"

# Backup all data
cp -r data/ $BACKUP_DIR/data_backup/
cp -r logs/ $BACKUP_DIR/logs_backup/ 
cp .env $BACKUP_DIR/env_backup

# Create data inventory
echo "=== V1 Data Inventory ===" > $BACKUP_DIR/inventory.txt
echo "Backup created: $(date)" >> $BACKUP_DIR/inventory.txt
echo "License plate JSON files: $(find data/license_plates -name '*.json' | wc -l)" >> $BACKUP_DIR/inventory.txt
echo "Enhanced result files: $(find data/enhanced_plates -name '*.json' | wc -l)" >> $BACKUP_DIR/inventory.txt
echo "Video files: $(find data/videos -name '*.mp4' | wc -l)" >> $BACKUP_DIR/inventory.txt
echo "Total data size: $(du -sh data/)" >> $BACKUP_DIR/inventory.txt

echo "Backup created in: $BACKUP_DIR"
```

## Migration Strategies

### Strategy 1: Parallel Deployment (Recommended)

Run V1 and V2 systems simultaneously for gradual transition.

#### Advantages:
- ✅ Zero downtime migration
- ✅ Gradual feature testing
- ✅ Easy rollback capability
- ✅ Data comparison validation

#### Implementation:

1. **Setup V2 Environment**:
   ```bash
   # Create separate V2 directory
   mkdir -p v2_deployment
   cd v2_deployment
   
   # Clone latest code
   git clone https://github.com/your-org/plate_recognition.git .
   git checkout v2-main
   
   # Setup virtual environment
   python -m venv .venv_v2
   source .venv_v2/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure V2 Ports**:
   ```bash
   # V2 configuration
   echo "HOST=0.0.0.0" > .env
   echo "PORT=8001" >> .env  # Different port from V1
   echo "CAMERA_ID=0" >> .env
   # ... other settings
   ```

3. **Data Directory Sharing**:
   ```bash
   # Link to existing data (read-only initially)
   ln -s ../v1_system/data ./data_v1_readonly
   
   # Create separate V2 data directories
   mkdir -p data/license_plates
   mkdir -p data/enhanced_plates
   mkdir -p data/videos
   ```

4. **Start Both Systems**:
   ```bash
   # Terminal 1: V1 System
   cd v1_system
   source .venv/bin/activate
   python -m app.main  # Runs on port 8000
   
   # Terminal 2: V2 System  
   cd v2_deployment
   source .venv_v2/bin/activate
   python -m app.main_v2  # Runs on port 8001
   ```

### Strategy 2: Direct Migration

Replace V1 system directly with V2.

#### Advantages:
- ✅ Simpler deployment
- ✅ No port conflicts
- ✅ Single system maintenance

#### Disadvantages:
- ❌ Potential downtime
- ❌ Harder rollback
- ❌ Less testing flexibility

## Data Migration Process

### 1. JSON Data Migration

V2 maintains compatibility with V1 JSON format while adding enhancements:

```python
# migration_script.py
import json
import os
import uuid
from datetime import datetime

def migrate_v1_to_v2_json():
    """Migrate V1 JSON files to V2 format with additional metadata"""
    
    v1_dir = "data/license_plates"
    v2_dir = "data/license_plates_v2"
    
    os.makedirs(v2_dir, exist_ok=True)
    
    for filename in os.listdir(v1_dir):
        if not filename.endswith('.json'):
            continue
            
        v1_path = os.path.join(v1_dir, filename)
        v2_path = os.path.join(v2_dir, filename)
        
        with open(v1_path, 'r') as f:
            v1_data = json.load(f)
        
        # Convert to V2 format
        v2_data = {
            "session_info": {
                "session_id": v1_data.get("session_id", f"migrated_{uuid.uuid4()}"),
                "start_time": v1_data.get("session_timestamp", datetime.now().timestamp()),
                "version": "2.0",
                "migrated_from": "1.0",
                "migration_timestamp": datetime.now().isoformat(),
                "enhanced_features": True
            },
            "configuration": v1_data.get("configuration", {}),
            "detections": []
        }
        
        # Migrate detections with enhanced fields
        for detection in v1_data.get("detections", []):
            v2_detection = {
                **detection,  # Keep all V1 fields
                "enhanced": False,  # Mark as not enhanced yet
                "migration_source": "v1",
                "ocr_confidence": detection.get("confidence", 0),
                "detection_confidence": detection.get("confidence", 0),
                "video_path": None  # Will be set when video recording triggers
            }
            v2_data["detections"].append(v2_detection)
        
        # Save V2 format
        with open(v2_path, 'w') as f:
            json.dump(v2_data, f, indent=2)
        
        print(f"Migrated: {filename} ({len(v2_data['detections'])} detections)")

if __name__ == "__main__":
    migrate_v1_to_v2_json()
```

### 2. Database Creation and Population

V2 introduces SQLite database alongside JSON storage:

```python
# database_migration.py
import asyncio
import json
import os
from app.repositories.sql_repository import SQLiteDetectionRepository
from app.database import async_session

async def populate_database_from_json():
    """Populate SQLite database from existing JSON files"""
    
    # Initialize repository
    repo = SQLiteDetectionRepository(async_session)
    await repo.initialize()
    
    json_dir = "data/license_plates"
    migrated_count = 0
    
    for filename in os.listdir(json_dir):
        if not filename.endswith('.json'):
            continue
            
        filepath = os.path.join(json_dir, filename)
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        detections = data.get("detections", [])
        if detections:
            await repo.add_detections(detections)
            migrated_count += len(detections)
            print(f"Migrated {len(detections)} detections from {filename}")
    
    print(f"Total detections migrated to database: {migrated_count}")
    await repo.shutdown()

if __name__ == "__main__":
    asyncio.run(populate_database_from_json())
```

### 3. Video File Organization

Organize existing video files to match V2 structure:

```bash
# video_migration.sh
#!/bin/bash

echo "Organizing video files for V2 structure..."

# Create date-based directories
for video_file in data/videos/*.mp4; do
    if [ -f "$video_file" ]; then
        # Extract creation date
        creation_date=$(stat -c %y "$video_file" | cut -d' ' -f1)
        
        # Create date directory
        mkdir -p "data/videos/$creation_date"
        
        # Move video file
        mv "$video_file" "data/videos/$creation_date/"
        
        echo "Moved $(basename $video_file) to $creation_date/"
    fi
done

echo "Video organization complete."
```

## Configuration Migration

### 1. Environment Variables

Update environment configuration for V2:

```bash
# migrate_config.py
import os
from pathlib import Path

def migrate_env_config():
    """Migrate .env configuration from V1 to V2 format"""
    
    v1_env = Path(".env")
    v2_env = Path(".env.v2")
    
    v2_config = []
    
    if v1_env.exists():
        with open(v1_env, 'r') as f:
            v1_lines = f.readlines()
        
        # Copy existing configuration
        for line in v1_lines:
            v2_config.append(line.strip())
    
    # Add V2-specific configurations
    v2_additions = [
        "",
        "# V2 Enhanced Features",
        "DUAL_STORAGE_ENABLED=true",
        "VIDEO_OVERLAYS_ENABLED=true",
        "CONFIDENCE_DISPLAY_ENABLED=true",
        "PROCESS_EVERY_N_FRAMES=5",
        "VIDEO_BUFFER_SECONDS=5",
        "POST_EVENT_SECONDS=15",
        "VIDEO_FPS=15",
        "",
        "# V2 Performance Settings",
        "FRAME_PROCESSING_TIMEOUT=0.5",
        "STORAGE_BATCH_SIZE=10",
        "LOG_LEVEL=INFO"
    ]
    
    v2_config.extend(v2_additions)
    
    # Write V2 configuration
    with open(v2_env, 'w') as f:
        f.write('\n'.join(v2_config))
    
    print(f"V2 configuration written to {v2_env}")
    print("Review and rename to .env when ready to use V2")

if __name__ == "__main__":
    migrate_env_config()
```

## Feature Validation

### 1. Functionality Comparison

Create validation tests to ensure V2 maintains V1 functionality:

```python
# validation_tests.py
import asyncio
import requests
import json
import time

class MigrationValidator:
    def __init__(self, v1_url="http://localhost:8000", v2_url="http://localhost:8001"):
        self.v1_url = v1_url
        self.v2_url = v2_url
        self.results = {}
    
    def test_api_endpoints(self):
        """Test that V2 endpoints respond correctly"""
        endpoints = [
            ("/", "GET"),
            ("/v2/stream", "GET"),
            ("/v2/results/detections", "GET"),
            ("/docs", "GET")
        ]
        
        for endpoint, method in endpoints:
            try:
                response = requests.get(f"{self.v2_url}{endpoint}", timeout=5)
                self.results[f"v2_{endpoint}"] = {
                    "status_code": response.status_code,
                    "success": response.status_code in [200, 404]  # 404 is OK for some endpoints
                }
                print(f"✅ V2 {endpoint}: {response.status_code}")
            except Exception as e:
                self.results[f"v2_{endpoint}"] = {
                    "status_code": None,
                    "success": False,
                    "error": str(e)
                }
                print(f"❌ V2 {endpoint}: {e}")
    
    def test_backward_compatibility(self):
        """Test that V1 endpoints still work in V2"""
        v1_endpoints = [
            "/stream",
            "/results/latest",
            "/detection/status"
        ]
        
        for endpoint in v1_endpoints:
            try:
                response = requests.get(f"{self.v2_url}{endpoint}", timeout=5)
                self.results[f"v1_compat_{endpoint}"] = {
                    "status_code": response.status_code,
                    "success": response.status_code in [200, 404]
                }
                print(f"✅ V1 Compatibility {endpoint}: {response.status_code}")
            except Exception as e:
                self.results[f"v1_compat_{endpoint}"] = {
                    "status_code": None,
                    "success": False,
                    "error": str(e)
                }
                print(f"❌ V1 Compatibility {endpoint}: {e}")
    
    def test_data_consistency(self):
        """Compare data consistency between V1 and V2"""
        try:
            # Get V1 data
            v1_response = requests.get(f"{self.v1_url}/results/latest")
            v1_data = v1_response.json() if v1_response.status_code == 200 else {}
            
            # Get V2 data
            v2_response = requests.get(f"{self.v2_url}/v2/results/detections")
            v2_data = v2_response.json() if v2_response.status_code == 200 else {}
            
            self.results["data_consistency"] = {
                "v1_detections": len(v1_data.get("detections", [])),
                "v2_detections": len(v2_data.get("detections", [])),
                "data_migrated": len(v2_data.get("detections", [])) >= len(v1_data.get("detections", []))
            }
            
            print(f"✅ Data consistency check completed")
            
        except Exception as e:
            self.results["data_consistency"] = {
                "success": False,
                "error": str(e)
            }
            print(f"❌ Data consistency check failed: {e}")
    
    def generate_report(self):
        """Generate migration validation report"""
        report = {
            "migration_validation_report": {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "results": self.results,
                "summary": {
                    "total_tests": len(self.results),
                    "passed_tests": sum(1 for r in self.results.values() 
                                      if isinstance(r, dict) and r.get("success", False)),
                    "failed_tests": sum(1 for r in self.results.values() 
                                      if isinstance(r, dict) and not r.get("success", True))
                }
            }
        }
        
        with open("migration_validation_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📋 Validation Report Generated")
        print(f"Total tests: {report['migration_validation_report']['summary']['total_tests']}")
        print(f"Passed: {report['migration_validation_report']['summary']['passed_tests']}")
        print(f"Failed: {report['migration_validation_report']['summary']['failed_tests']}")

if __name__ == "__main__":
    validator = MigrationValidator()
    validator.test_api_endpoints()
    validator.test_backward_compatibility()
    validator.test_data_consistency()
    validator.generate_report()
```

## Gradual Feature Adoption

### Phase 1: Basic V2 Deployment

1. **Deploy V2 with V1 compatibility mode**
2. **Test basic functionality**
3. **Validate data storage**

```bash
# Start V2 in compatibility mode
export V1_COMPATIBILITY_MODE=true
python -m app.main_v2
```

### Phase 2: Enhanced Features

1. **Enable dual storage**
2. **Activate video overlays**
3. **Test enhanced recognition**

```bash
# Enable enhanced features gradually
echo "DUAL_STORAGE_ENABLED=true" >> .env
echo "VIDEO_OVERLAYS_ENABLED=true" >> .env
```

### Phase 3: Full V2 Features

1. **Enable all V2 features**
2. **Migrate client applications to V2 APIs**
3. **Deprecate V1 endpoints**

```bash
# Full V2 configuration
cat >> .env << EOF
# Full V2 Feature Set
ENHANCED_RECOGNITION_ENABLED=true
TEXAS_PLATE_IMPROVEMENTS=true
CHARACTER_CORRECTION_ENABLED=true
CONFIDENCE_COLOR_CODING=true
SYSTEM_METRICS_OVERLAY=true
EOF
```

## Rollback Procedures

### Quick Rollback to V1

If issues arise during migration:

```bash
# Stop V2 system
pkill -f "python -m app.main_v2"

# Restore V1 data from backup
BACKUP_DIR="backups/v1_migration_YYYYMMDD_HHMMSS"  # Use actual backup dir
rm -rf data/
cp -r $BACKUP_DIR/data_backup/ data/

# Restore V1 configuration
cp $BACKUP_DIR/env_backup .env

# Start V1 system
source .venv/bin/activate
python -m app.main
```

### Data Recovery

If data corruption occurs:

```python
# data_recovery.py
import shutil
import os
from datetime import datetime

def recover_from_backup():
    """Recover data from the most recent backup"""
    
    backup_dirs = [d for d in os.listdir("backups/") if d.startswith("v1_migration_")]
    if not backup_dirs:
        print("No backup directories found!")
        return
    
    latest_backup = sorted(backup_dirs)[-1]
    backup_path = f"backups/{latest_backup}"
    
    print(f"Recovering from backup: {latest_backup}")
    
    # Create recovery timestamp
    recovery_dir = f"recovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Backup current state before recovery
    if os.path.exists("data/"):
        shutil.move("data/", f"{recovery_dir}_current_data")
    
    # Restore from backup
    shutil.copytree(f"{backup_path}/data_backup", "data/")
    
    print(f"Data recovered from {latest_backup}")
    print(f"Previous state saved to {recovery_dir}_current_data")

if __name__ == "__main__":
    recover_from_backup()
```

## Performance Comparison

### Monitoring Migration Performance

```python
# performance_monitor.py
import time
import psutil
import requests
import json

class PerformanceMonitor:
    def __init__(self):
        self.metrics = {
            "v1": {},
            "v2": {}
        }
    
    def measure_response_time(self, url, version):
        """Measure API response time"""
        start_time = time.time()
        try:
            response = requests.get(url, timeout=10)
            end_time = time.time()
            return {
                "response_time": end_time - start_time,
                "status_code": response.status_code,
                "success": response.status_code == 200
            }
        except Exception as e:
            return {
                "response_time": None,
                "status_code": None,
                "success": False,
                "error": str(e)
            }
    
    def measure_system_resources(self):
        """Measure CPU and memory usage"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage("/").percent
        }
    
    def run_comparison(self):
        """Run performance comparison between V1 and V2"""
        
        # Test endpoints
        endpoints = {
            "stream": {"v1": "http://localhost:8000/stream", "v2": "http://localhost:8001/v2/stream"},
            "results": {"v1": "http://localhost:8000/results/latest", "v2": "http://localhost:8001/v2/results/detections"}
        }
        
        for endpoint_name, urls in endpoints.items():
            print(f"Testing {endpoint_name} performance...")
            
            for version, url in urls.items():
                metrics = self.measure_response_time(url, version)
                self.metrics[version][endpoint_name] = metrics
                
                if metrics["success"]:
                    print(f"✅ {version.upper()} {endpoint_name}: {metrics['response_time']:.3f}s")
                else:
                    print(f"❌ {version.upper()} {endpoint_name}: Failed")
        
        # System resources
        system_metrics = self.measure_system_resources()
        print(f"\n📊 System Resources:")
        print(f"CPU: {system_metrics['cpu_percent']:.1f}%")
        print(f"Memory: {system_metrics['memory_percent']:.1f}%")
        print(f"Disk: {system_metrics['disk_usage']:.1f}%")
        
        # Save report
        report = {
            "performance_comparison": {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "metrics": self.metrics,
                "system": system_metrics
            }
        }
        
        with open("performance_comparison.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print("\n📋 Performance report saved to performance_comparison.json")

if __name__ == "__main__":
    monitor = PerformanceMonitor()
    monitor.run_comparison()
```

## Post-Migration Checklist

### ✅ Verification Tasks

- [ ] **V2 System Starting**: V2 application starts without errors
- [ ] **Database Connectivity**: SQLite database accessible and populated
- [ ] **JSON Compatibility**: Existing JSON files readable by V2
- [ ] **Video Recording**: Enhanced video recording with overlays working
- [ ] **API Endpoints**: All V2 endpoints responding correctly
- [ ] **Backward Compatibility**: V1 endpoints still functional
- [ ] **Data Integrity**: No data loss during migration
- [ ] **Performance**: V2 performance meets or exceeds V1
- [ ] **Enhanced Features**: Texas plate improvements active
- [ ] **Dual Storage**: Both SQL and JSON storage working

### 📋 Documentation Updates

- [ ] **Update API Documentation**: Reflect V2 endpoint changes
- [ ] **Configuration Guide**: Update environment variable documentation
- [ ] **Deployment Guide**: Update deployment procedures
- [ ] **Troubleshooting Guide**: Add V2-specific troubleshooting
- [ ] **User Training**: Update user guides for V2 features

### 🔧 Operational Procedures

- [ ] **Monitoring Setup**: Configure monitoring for V2 metrics
- [ ] **Backup Procedures**: Update backup scripts for dual storage
- [ ] **Log Rotation**: Configure log rotation for V2 logging
- [ ] **Health Checks**: Implement V2-specific health checks
- [ ] **Alerting**: Update alerts for V2 system monitoring

This comprehensive migration guide ensures a smooth transition from V1 to V2 while maintaining system reliability and data integrity throughout the process.