# Playback Architecture Review & Implementation Plan

## Current State vs Recommended Approach

### 📊 Current Implementation (Camera-First)
The system currently follows a **camera-centric approach**:
```
Cameras (from DB) → Check for Recordings → Display Available
```

**Current Endpoints**:
- `GET /api/v1/recordings/cameras/{camera_id}/calendar` - Requires valid camera_id
- `GET /api/v1/recordings/cameras/{camera_id}/timeline` - Requires valid camera_id
- No endpoint for discovering all recording sources

**Problems with Current Approach**:
1. ❌ Deleted cameras make recordings inaccessible
2. ❌ No visibility into orphaned recordings
3. ❌ Storage management blind spots
4. ❌ Can't access historical footage from removed cameras
5. ❌ Database dependency for accessing physical files

### ✅ Recommended Implementation (Recordings-First)
The document proposes a **recordings-centric approach**:
```
Scan Filesystem → Discover All Recordings → Enrich with Camera Metadata
```

**Key Benefits**:
1. ✅ All recordings always accessible
2. ✅ Complete storage visibility
3. ✅ Historical footage preserved
4. ✅ Database-independent access
5. ✅ Better forensic capabilities

## 🔍 Gap Analysis

### Missing Components

| Component | Current State | Required Implementation | Priority |
|-----------|--------------|------------------------|----------|
| **Recording Discovery Service** | ❌ Not implemented | Scan filesystem for all recordings | HIGH |
| **Sources Endpoint** | ❌ Not implemented | `/api/recordings/sources` | HIGH |
| **Orphaned Recording Support** | ❌ Not supported | Allow playback without camera in DB | HIGH |
| **Storage Management UI** | ⚠️ Partial | Show all recordings including orphaned | MEDIUM |
| **Cleanup Policies** | ⚠️ Basic | Advanced retention with orphan handling | MEDIUM |
| **Recording Inventory Cache** | ❌ Not implemented | Performance optimization | LOW |

### Current File Structure
```
recordings/
├── camera_946701d3/
│   └── 2025/01/20/14/
│       ├── recording_20250120_140000.mp4
│       └── recording_20250120_141000.mp4
├── camera_deleted_123/  # Orphaned - camera deleted from DB
│   └── 2025/01/15/10/
│       └── recording_20250115_100000.mp4
```

## 🎯 Implementation Priorities

### Phase 1: Core Recording Discovery (HIGH PRIORITY)
**Goal**: Enable access to all recordings regardless of camera status

#### 1.1 Create Recording Discovery Service
```python
# recording_service/services/recording_discovery_service.py
class RecordingDiscoveryService:
    async def get_all_recording_sources(self):
        """Scan filesystem and return all cameras with recordings"""
        # Scan recordings directory
        # Extract camera IDs
        # Check database status
        # Return comprehensive list
    
    async def get_orphaned_recordings(self):
        """Return recordings from deleted cameras"""
        
    async def calculate_storage_usage(self, camera_id=None):
        """Calculate storage per camera or total"""
```

#### 1.2 Add Sources Endpoint
```python
# recording_service/main.py
@app.get("/api/v1/recordings/sources")
async def get_recording_sources(
    include_deleted: bool = True,
    include_empty: bool = False
):
    """Get all cameras that have recordings"""
    return await discovery_service.get_all_recording_sources()
```

#### 1.3 Modify Existing Endpoints
- Remove database validation for camera_id
- Allow playback from any camera_id with recordings
- Add metadata enrichment for active cameras

### Phase 2: UI Integration (HIGH PRIORITY)
**Goal**: Update frontend to use recordings-first approach

#### 2.1 Update Playback Page
```javascript
// frontend/src/pages/RecordingsPage.js
async loadRecordingSources() {
    // Call new /api/recordings/sources endpoint
    // Display all sources including deleted
    // Mark deleted cameras visually
}
```

#### 2.2 Add Filters
- "Active Cameras Only"
- "Deleted Cameras Only"
- "All Sources"
- "Has Recent Recordings"

#### 2.3 Storage Indicators
- Show storage usage per camera
- Highlight orphaned recordings
- Display total system usage

### Phase 3: Storage Management (MEDIUM PRIORITY)
**Goal**: Provide tools for managing orphaned recordings

#### 3.1 Management Endpoints
```python
@app.delete("/api/v1/recordings/orphaned")
async def cleanup_orphaned_recordings(
    older_than_days: int = 30,
    dry_run: bool = True
)

@app.get("/api/v1/recordings/storage/report")
async def get_storage_report()
```

#### 3.2 Cleanup Policies
- Configurable retention for orphaned recordings
- Different policies for active vs deleted cameras
- Storage quota enforcement

### Phase 4: Performance Optimization (LOW PRIORITY)
**Goal**: Optimize for large-scale deployments

#### 4.1 Caching Layer
- Cache recording inventory (5-minute TTL)
- Background refresh process
- Invalidation on new recordings

#### 4.2 Database Optimization
- Index recording metadata
- Optimize filesystem queries
- Implement pagination

## 📝 Implementation Checklist

### Immediate Actions (This Week)
- [ ] Create `RecordingDiscoveryService` class
- [ ] Implement `/api/recordings/sources` endpoint
- [ ] Modify calendar/timeline endpoints to work without DB validation
- [ ] Update frontend to load recording sources
- [ ] Add visual indicators for deleted cameras

### Short-term (Next 2 Weeks)
- [ ] Add storage usage calculations
- [ ] Implement orphaned recording filters
- [ ] Create storage management UI
- [ ] Add cleanup confirmation dialogs
- [ ] Test with simulated deleted cameras

### Long-term (Month)
- [ ] Implement caching layer
- [ ] Add advanced cleanup policies
- [ ] Create storage reports/analytics
- [ ] Add audit logging for deletions
- [ ] Performance testing with large datasets

## 🚨 Critical Considerations

### Data Safety
- **NEVER** auto-delete recordings when camera is deleted
- Always require explicit confirmation for bulk deletions
- Implement soft-delete with recovery period
- Log all deletion operations

### User Experience
- Clearly differentiate active vs deleted cameras
- Show last known camera name for deleted sources
- Provide helpful tooltips explaining orphaned recordings
- Default to showing all sources (transparency)

### Migration Strategy
1. Deploy new discovery service alongside existing
2. Add new endpoints without breaking old ones
3. Gradually migrate UI to use new endpoints
4. Deprecate old endpoints after full migration
5. Maintain backwards compatibility for 1 version

## 💡 Benefits Realization

### For Users
- Never lose access to important footage
- Complete visibility into all recordings
- Better forensic investigation capabilities
- Simplified storage management

### For Administrators
- Identify and clean up orphaned data
- Better storage capacity planning
- Audit trail for all recordings
- Reduced support tickets about "missing" footage

### For System
- More resilient architecture
- Database-independent core functionality
- Better disaster recovery
- Scalable design

## 🎉 Expected Outcomes

After implementing the recordings-first approach:

1. **100% Recording Accessibility** - All recordings viewable regardless of camera status
2. **Storage Transparency** - Complete visibility into storage usage
3. **Improved Reliability** - System works even with database issues
4. **Better User Trust** - Users confident their recordings are safe
5. **Simplified Maintenance** - Easier to manage and debug

## Next Steps

1. Review this analysis with team
2. Prioritize Phase 1 implementation
3. Create detailed tickets for each component
4. Begin with `RecordingDiscoveryService`
5. Test thoroughly with edge cases

The recordings-first approach is the right architectural decision for a security-focused system where data preservation is paramount.