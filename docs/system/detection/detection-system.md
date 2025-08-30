# License Plate Detection System Documentation

**Status**: ✅ WORKING (Fixed 2025-08-29)  
**Last Updated**: 2025-08-29  

## Overview

The license plate detection system processes camera streams in real-time, identifies license plates using AI models, and stores detection data in the database with deduplication filtering.

## Architecture

```
Camera Stream → AI Pipeline → FilteredDetectionProcessor → Database + Images
                     ↓              ↓                           ↓
                YOLO + OCR    Deduplication Filter      detections table
```

### Components

1. **AI Pipeline** (`ai_pipeline/`)
   - YOLO vehicle detection
   - License plate segmentation  
   - EasyOCR text recognition

2. **FilteredDetectionProcessor** (`ai_pipeline/detection_processor.py`)
   - Applies deduplication filtering
   - Saves valid detections to database
   - Manages detection metadata

3. **Detection Filter** (`ai_pipeline/detection_filter.py`)  
   - Prevents duplicate detections
   - Time-based and spatial filtering
   - Configurable thresholds

4. **Database Storage** (`database/service.py`)
   - `detections` table for license plate data
   - Stores metadata, confidence scores, image paths
   - Supports search and filtering

## Data Flow

### 1. Detection Processing
```python
# Camera frame → AI Pipeline
detection = ai_pipeline.process_frame(frame)

# Filter duplicates
should_store, reason = filter.should_store(detection, camera_id)

# Save to database if valid
if should_store:
    detection_id = await db_service.save_detection(detection_data)
```

### 2. Database Schema
```sql
-- detections table
CREATE TABLE detections (
    id VARCHAR(36) PRIMARY KEY,
    camera_id VARCHAR(50) NOT NULL,
    plate_text VARCHAR(20) NOT NULL,
    confidence FLOAT NOT NULL,
    vehicle_type VARCHAR(50),
    detected_at DATETIME NOT NULL,
    vehicle_bbox JSON,
    plate_bbox JSON,
    frame_path VARCHAR(500),
    plate_image_path VARCHAR(500),
    meta_data JSON
);
```

### 3. File Storage
```
detections/
├── plates/     # Cropped license plate images
│   └── {uuid}_plate.jpg
└── frames/     # Full camera frames
    └── {uuid}_frame.jpg
```

## API Endpoints

### Recent Detections
```bash
GET /api/detections/recent?limit=10&camera_id=camera_123
```

### Search Detections  
```bash
GET /api/detections/search?plate_text=ABC123&limit=50&offset=0
```

### Detection Statistics
```bash
GET /api/detections/stats
```

## Configuration

### Feature Flags (`config/features.json`)
```json
{
  "detection_features": {
    "license_plate_detection": true,
    "universal_detection": false
  }
}
```

### Filter Settings
- **Time threshold**: 30 seconds between same plate detections
- **Spatial threshold**: Minimum distance for duplicate detection
- **Confidence threshold**: Minimum OCR confidence score

## Troubleshooting

### Common Issues

#### 1. No Detections in Database
- **Symptoms**: Images saved but API returns empty results
- **Check**: Detection processor database method
- **Fix**: Ensure using `save_detection()` not `create_universal_detection()`

#### 2. Too Many Duplicate Detections
- **Symptoms**: Same plate detected multiple times rapidly
- **Check**: Filter configuration and thresholds
- **Fix**: Adjust time/spatial thresholds in detection filter

#### 3. Low Detection Rate
- **Symptoms**: Few detections despite traffic
- **Check**: AI model confidence thresholds, camera positioning
- **Fix**: Lower confidence thresholds or improve camera angle

### Debugging Commands

```bash
# Check detection count
curl -s "http://localhost:8001/api/detections/recent?limit=1" | jq 'length'

# View recent detection
curl -s "http://localhost:8001/api/detections/recent?limit=1" | jq '.'

# Check filter stats (if available)
# curl -s "http://localhost:8001/api/detection/filter/stats"

# Check detection images
ls -la detections/plates/ | tail -5
ls -la detections/frames/ | tail -5
```

## Historical Issues & Fixes

### 2025-08-29: Detection Database Storage Fix
**Problem**: Detection processor using `create_universal_detection()` method that failed
**Solution**: Changed to use working `save_detection()` method with original detections table
**Lesson**: Use proven working patterns instead of forcing new unfinished features

### Key Debugging Principles Applied
1. **Follow the data flow**: Images saved ✅, database empty ❌ = database insertion problem
2. **Fix first, optimize later**: Get working system before adding features  
3. **Use working patterns**: `save_detection()` method was proven to work
4. **Minimal viable fix**: Changed only the broken save method

## Future Improvements

### Priority 1 - Missing Core Features
- [ ] Fix detection statistics endpoint (returns 0 despite active detections)
- [ ] Add camera names to detection results (currently shows camera_id)
- [ ] Implement detection rate monitoring dashboard

### Priority 2 - Enhanced Features  
- [ ] Detection quality scoring and ranking
- [ ] Export detections to CSV/Excel
- [ ] Detection analytics and reporting
- [ ] Plate history visualization

### Priority 3 - System Cleanup
- [ ] Complete universal detection system or remove it
- [ ] Standardize detection table schema
- [ ] Add comprehensive detection API documentation

## Migration Notes

### Universal Detection System
The codebase contains an incomplete "universal detection" system intended to handle multiple object types (vehicles, people, etc.) in addition to license plates. 

**Current State**: Partially implemented but non-functional
**Recommendation**: Either complete the migration or remove the universal detection code to avoid confusion

**If Completing Migration**:
1. Fix `create_universal_detection()` method
2. Update all detection endpoints to use universal table
3. Migrate existing detection data
4. Update frontend to handle universal detection format

**If Removing Universal Detection**:
1. Remove `universal_detections` table
2. Remove `create_universal_detection()` method  
3. Clean up universal detection references
4. Update feature flags documentation

## Testing Procedures

### Verification Checklist
- [ ] Services running: `python3 bin/check_services.py`
- [ ] Recent detections API: `curl http://localhost:8001/api/detections/recent?limit=5`
- [ ] Search API: `curl http://localhost:8001/api/detections/search?limit=5`  
- [ ] Images being saved: `ls detections/plates/ | tail -5`
- [ ] Database records: Check detection count in API response
- [ ] Frontend display: Verify detections show in web interface

### Performance Testing
- Monitor detection rate over time
- Check database query performance with large datasets
- Verify image storage doesn't exceed disk limits
- Test deduplication filter effectiveness