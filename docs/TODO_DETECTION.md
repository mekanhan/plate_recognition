# Detection System TODO List

**Created**: 2025-08-29  
**Priority**: Based on user impact and system stability

## 🔴 High Priority - Fix Broken Features

### 1. Detection Statistics Endpoint Issue
**Problem**: `/api/detections/stats` returns all zeros despite active detections
**Impact**: Users can't see detection counts/metrics  
**Investigation needed**: 
- Check if stats method queries correct table
- Verify date/time filtering logic
- Compare with working recent detections endpoint

### 2. Camera Names in Detection Results
**Problem**: Detection API returns `camera_id` instead of readable camera names
**Impact**: Poor user experience, harder to identify camera locations
**Fix needed**:
- Update detection endpoints to join with cameras table
- Add camera name to detection result format
- Test with multiple cameras

## 🟡 Medium Priority - Missing Features

### 3. Frontend Detection Display
**Problem**: Unknown if frontend properly displays detection data
**Impact**: Users may not see detections in web interface
**Tasks**:
- Test detection page in frontend 
- Verify detection list loads data from API
- Check detection image display functionality

### 4. Universal Detection System Cleanup
**Problem**: Incomplete universal detection system causing confusion
**Impact**: Code complexity, potential future bugs
**Decision needed**: Complete it or remove it entirely
**If removing**:
- Remove `universal_detections` table
- Remove `create_universal_detection()` method
- Clean up feature flags
- Update documentation

## 🟢 Low Priority - Enhancements

### 5. Detection Analytics Dashboard
**Features to add**:
- Detection rate over time graphs
- Top detected plates
- Camera performance comparison
- Peak traffic hours analysis

### 6. Detection Export Functionality
**Features to add**:
- Export to CSV/Excel
- Date range filtering
- Camera filtering
- Include/exclude images option

### 7. Enhanced Search & Filtering
**Features to add**:
- Fuzzy plate text matching
- Date/time range filtering
- Confidence score filtering
- Vehicle type filtering

## 📋 Quick Wins (< 2 hours each)

### A. Add Detection Count to System Health
- Modify `bin/check_services.py` to show detection count
- Add to system health API endpoint

### B. Improve Detection Logging
- Add more detailed logging to detection processor
- Log filter statistics periodically
- Add detection rate logging

### C. API Documentation
- Add detection endpoints to API docs
- Include example responses
- Document query parameters

## 🔍 Investigation Items

### Database Performance
- Test detection queries with large datasets
- Check if indexes needed on detection table
- Monitor database file size growth

### Filter Effectiveness  
- Analyze duplicate detection rates
- Review filter statistics if available
- Optimize filter parameters if needed

### Image Storage Management
- Check if old detection images are cleaned up
- Verify storage limits are respected
- Consider image compression options

## 📝 Documentation Tasks

### API Documentation
- Document all detection endpoints
- Add example requests/responses  
- Include error handling guide

### User Guide
- How to view detections in frontend
- How to search and filter detections
- How to export detection data

### System Administration
- How to monitor detection performance
- How to troubleshoot detection issues
- How to adjust detection parameters

## 🧪 Testing Improvements

### Automated Testing
- Unit tests for detection processor
- Integration tests for detection API
- Performance tests for detection queries

### Manual Testing Procedures
- Detection rate monitoring
- Multi-camera testing
- Frontend functionality verification

---

## Decision Points Needed

1. **Universal Detection System**: Complete or remove?
2. **Detection Statistics**: Fix existing or rewrite?
3. **Image Storage**: Keep all images or implement cleanup?
4. **Frontend Integration**: Priority level for detection display?

## Next Steps Recommendation

1. Fix detection statistics endpoint (impacts user experience)
2. Add camera names to detection results (easy win)
3. Test frontend detection display
4. Decide on universal detection system fate
5. Add detection count to health checks (visibility)