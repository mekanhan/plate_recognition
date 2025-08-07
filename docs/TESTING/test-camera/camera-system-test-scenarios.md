# Camera System Testing Scenarios & Strategy

## Current System State Analysis

### ✅ What's Been Implemented

1. **Database-Driven Architecture**
   - SQLite database with camera tables
   - Camera service layer with CRUD operations
   - Encryption for credentials (Fernet)
   - 8-field standardized status format

2. **Dual API System**
   - **v1 API** (`/api/cameras`) - Original endpoints (partially functional)
   - **v2 API** (`/v2/api/cameras`) - New database-driven endpoints
   - Test server available on port 8080

3. **Frontend Integration**
   - Camera modal for adding/editing cameras
   - Connection testing functionality
   - Fallback logic (v2 → v1 → recording service)
   - Recording status display with real-time updates

4. **Recording Service**
   - Still uses hardcoded cameras (not yet integrated with database)
   - Runs on port 8002
   - Has health/status endpoints

### ⚠️ Current Issues & Gaps

1. **Integration Disconnect**
   - Recording service doesn't read from database
   - Camera manager in main API still loads hardcoded cameras
   - No automatic recording start for new cameras

2. **Missing Functionality**
   - Edit camera not fully implemented
   - Delete camera needs recording service integration
   - No bulk camera operations yet

3. **Configuration Issues**
   - Some frontend assets missing (logo.png, vision_port_text.png)
   - CORS configuration might need adjustment

## Testing Strategy

### Phase 1: Database & API Foundation Testing

#### Scenario 1.1: Database Operations
**Test**: Verify database CRUD operations work correctly
- Add camera with encrypted credentials
- Retrieve camera with decrypted credentials
- Update camera settings
- Delete camera (soft delete)

**Validation Points**:
- Credentials are encrypted in database
- Camera IDs are unique
- Timestamps update correctly
- Status tracking works

#### Scenario 1.2: v2 API Endpoints
**Test**: Use test server (port 8080) to verify all endpoints
```
GET    /v2/api/cameras/status     - Bulk status (8 fields)
GET    /v2/api/cameras            - List all cameras
POST   /v2/api/cameras            - Create new camera
GET    /v2/api/cameras/{id}       - Get single camera
PUT    /v2/api/cameras/{id}       - Update camera (partial)
DELETE /v2/api/cameras/{id}       - Delete camera
POST   /v2/api/cameras/{id}/start - Start recording
POST   /v2/api/cameras/{id}/stop  - Stop recording
```

**Test Data**:
- Valid camera: IP in network range, correct credentials
- Invalid camera: Wrong IP/credentials
- Edge cases: Special characters in names, max field lengths

### Phase 2: Frontend Integration Testing

#### Scenario 2.1: Add Camera Flow
**Steps**:
1. Open camera modal
2. Fill in camera details
3. Test connection (should validate)
4. Save camera
5. Verify camera appears in list

**Validation**:
- Form validation works
- Connection test provides feedback
- Camera saves to database
- List refreshes automatically

#### Scenario 2.2: Camera Status Display
**Test**: Verify 8-field standard display
- Location (default: "Unknown")
- Connection (format: "RTSP (IP)")
- Recording Status (with icon)
- Connection Status (with color)
- FFmpeg PID
- Segments Created
- Storage Used
- Recording Uptime

**Edge Cases**:
- New camera (all defaults)
- Recording camera (live values)
- Disconnected camera (error states)

### Phase 3: Service Integration Testing

#### Scenario 3.1: Recording Service Integration
**Current State**: Recording service is disconnected from database

**Test Plan**:
1. Add camera via UI
2. Check if recording service sees it (currently won't)
3. Document integration requirements
4. Test manual recording start/stop

#### Scenario 3.2: Status Synchronization
**Test**: Real-time status updates across services
- Start recording → status updates in UI
- Stop recording → status reflects change
- Connection loss → error state displayed
- Service restart → cameras reload

### Phase 4: End-to-End Scenarios

#### Scenario 4.1: Complete Camera Lifecycle
1. **Add Camera**
   - Via UI with connection test
   - Verify in database
   - Check all services aware

2. **Use Camera**
   - Start recording
   - Monitor status
   - View snapshots

3. **Modify Camera**
   - Change settings
   - Update location
   - Test new connection

4. **Remove Camera**
   - Stop recording first
   - Delete from UI
   - Verify cleanup

#### Scenario 4.2: Multi-Camera Operations
**Test**: System behavior with multiple cameras
- Add 5-10 cameras
- Start recording on all
- Monitor performance
- Bulk operations

### Phase 5: Error Handling & Recovery

#### Scenario 5.1: Connection Failures
- Invalid IP address
- Wrong credentials
- Network timeout
- Camera offline

**Expected Behavior**:
- Clear error messages
- Graceful degradation
- Retry mechanisms
- Status indicators

#### Scenario 5.2: Service Failures
- Database unavailable
- Recording service down
- API service restart
- Frontend reload

**Recovery Testing**:
- Services auto-reconnect
- Data persistence
- Status recovery
- No data loss

## Testing Execution Plan

### Week 1: Foundation Testing
- Day 1-2: Database and v2 API testing
- Day 3-4: Frontend integration testing
- Day 5: Documentation of issues found

### Week 2: Integration Testing
- Day 1-2: Recording service integration planning
- Day 3-4: Status synchronization testing
- Day 5: Performance testing with multiple cameras

### Week 3: Production Readiness
- Day 1-2: Error handling scenarios
- Day 3-4: Recovery and resilience testing
- Day 5: Final integration testing

## Test Environment Setup

### Required Components:
1. **Main API** (Port 8001)
   - Full application with all services

2. **Test API** (Port 8080)
   - Lightweight v2 endpoints only
   - Good for isolated testing

3. **Recording Service** (Port 8002)
   - Currently with hardcoded cameras
   - Needs database integration

4. **Frontend** (Port 3000)
   - Full UI with camera management

5. **Database**
   - SQLite at `data/license_plates.db`
   - Migration scripts available

### Test Data Setup:
```bash
# Run migration to set up initial cameras
python migrate_to_new_camera_schema.py

# Use test server for API testing
python test_camera_api.py

# Check database state
sqlite3 data/license_plates.db "SELECT * FROM cameras;"
```

## Success Metrics

### Functional Requirements:
- ✅ All CRUD operations work via API
- ✅ Frontend can manage cameras without code changes
- ✅ Status displays accurately for all 8 fields
- ⏳ Recording service uses database (pending)
- ⏳ Automatic recording start for new cameras (pending)

### Non-Functional Requirements:
- Response time < 1 second for all operations
- Support 10+ cameras without performance issues
- Zero downtime during camera updates
- Encrypted credential storage
- Comprehensive error handling

## Risk Areas & Mitigation

### High Risk:
1. **Recording Service Integration**
   - Current: Hardcoded cameras
   - Impact: New cameras won't record
   - Mitigation: Prioritize integration

2. **Service Synchronization**
   - Current: Services work independently
   - Impact: Status inconsistencies
   - Mitigation: Implement event system

### Medium Risk:
1. **Performance with Multiple Cameras**
   - Current: Not tested at scale
   - Impact: Slow UI/timeouts
   - Mitigation: Load testing, optimization

2. **Error Recovery**
   - Current: Basic error handling
   - Impact: Poor user experience
   - Mitigation: Comprehensive error states

## Recommendations

### Immediate Actions:
1. Complete recording service database integration
2. Fix missing frontend assets
3. Implement camera edit functionality
4. Add comprehensive logging

### Next Phase:
1. Event-driven architecture for status updates
2. Bulk camera import/export
3. Camera templates for quick setup
4. Advanced monitoring dashboard

### Long Term:
1. Microservices architecture
2. Kubernetes deployment
3. Multi-tenant support
4. AI-powered camera optimization