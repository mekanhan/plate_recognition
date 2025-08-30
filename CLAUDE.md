# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Core Principles
- **Simplicity first**: Simple, direct solutions over complex ones
- **Remove barriers**: Focus on core functionality, avoid adding complexity
- **24/7 streaming**: Auto-connect cameras, real-time status display
- **Test thoroughly**: Verify all changes work before claiming success

## Testing Requirements

**MANDATORY**: After ANY code changes, verify fixes work completely.

### Testing Checklist
- ✅ Fix syntax errors and imports
- ✅ Restart affected services
- ✅ Test endpoints with curl
- ✅ Run `python3 bin/check_services.py`
- ✅ Check logs for 5+ minutes stability
- ✅ Verify actual functionality works

**Never claim success until ALL tests pass.**

## Test Workflow
1. Write code
2. Define test cases (minimum 3)
3. Execute tests with verification
4. Document results with evidence
5. Only then confirm completion

### UI Testing
- Start services and verify accessibility
- Test functionality where possible
- Request user verification for browser UI
- Never claim UI fixes work without confirmation

### API Testing
- Test endpoints with curl
- Verify JSON responses
- Check error handling
- Monitor database operations
- Review service logs

### Prohibited Without Testing
Never say "fixed" or "complete" without proof. Always say "testing confirms..." or "please verify..."

## Documentation First
- Check `/docs/` for existing patterns and fixes
- Follow established conventions
- Update docs after implementation
- Ask user if no relevant docs exist

## Breaking Changes Prevention
- Check imports, APIs, tests before changing
- Maintain existing interfaces - use facade pattern if refactoring
- Add new DB columns with defaults, never alter existing
- Ask user about compatibility approach when uncertain
- Keep original files as wrappers when restructuring

## UI Development

### Event Handling
- Use `e.target.closest()` for reliable button clicks
- Clean up before reattaching listeners
- Reset modal state completely when opening

### Component Structure
- Header: User functions, system status
- Sidebar: Navigation, system info
- Content: Section functionality, modals

### Debugging UI Issues
- Add console logging for event flow
- Copy working patterns from similar features
- Test child element clicks
- Verify CSS application

### Anti-Patterns to Avoid
- Functions in templates
- Incomplete state resets
- Assuming CSS works

### Incremental Development
- Commit working baseline before enhancements
- Add one feature at a time
- Test immediately after each change
- Get user approval before next feature

## Commands

### Service Control
```bash
python3 bin/start_lpr.py          # Start all services
python3 bin/stop_all_services.py  # Stop all
python3 bin/check_services.py     # Health check
```

### URLs
- Frontend: http://localhost:8080/
- Main API: http://localhost:8001/ (docs at /docs)
- Recording API: http://localhost:8002/ (docs at /docs)

### Health Checks
```bash
curl http://localhost:8001/api/system/health
curl http://localhost:8002/health
```

## Architecture

### Services
- **Main API (8001)**: Camera management, detection, snapshots
- **Recording Service (8002)**: 24/7 recording, playback
- **Frontend (8080)**: Web interface

### Stack
- FastAPI + SQLite + YOLO + EasyOCR + OpenCV
- Dynamic camera management from database
- 10-minute recording segments
- Automated storage cleanup

## Key Features ✅ Working
- 24/7 recording with 10-minute segments
- Dynamic camera management from database
- Real-time health monitoring
- Automated storage cleanup (10GB default)
- Complete playback API with timeline
- **License plate detection with database storage** (Fixed 2025-08-29)
- **Stable camera ID system** (Implemented 2025-08-30)

## System Status ✅ All Healthy
- Main API: Camera management, snapshots, detection
- Recording Service: Active recording (140+ segments)
- Database: WAL mode, 64MB cache, optimized

## Quick Reference

### Dependencies
- FastAPI, SQLite, YOLO, EasyOCR, OpenCV
- Python 3.8+, pytest for testing

### File Storage
- Recordings: `recordings/camera_id/YYYY/MM/DD/HH/`
- Database: `data/license_plates.db`
- Logs: `logs/` with rotation

### Database Guidelines
- Use `database/db_config.py` for connections
- Run integrity checks after schema changes
- Test both session patterns for compatibility

## Detection System Architecture ✅ Fixed

### Current State (2025-08-29)
- **Detection Processing**: Uses `FilteredDetectionProcessor` with deduplication
- **Database Storage**: Saves to original `detections` table (NOT universal_detections)
- **API Endpoints**: `/api/detections/recent`, `/api/detections/search` fully functional
- **Real-time Processing**: Active detection every few seconds with database storage

### Detection Data Flow
1. Camera streams processed by AI pipeline
2. `FilteredDetectionProcessor` applies deduplication filtering
3. Valid detections saved using `db_service.save_detection()`
4. Images stored in `detections/plates/` and `detections/frames/`
5. Database records accessible via API endpoints

### Critical Lessons Learned (2025-08-29)

#### **Root Cause of Detection Failure**
- System had TWO detection tables: `detections` (working) and `universal_detections` (broken)
- Detection processor was using broken `create_universal_detection()` method
- Fix: Use proven `save_detection()` method with original table

#### **Why Systems Break During "Improvements"**
1. **Incomplete Migration**: Someone started universal detection system but never finished
2. **Feature Flag Confusion**: Multiple detection approaches active simultaneously  
3. **Over-Engineering**: Trying to force new architecture instead of fixing existing
4. **Missing Documentation**: No clear migration plan or rollback strategy

#### **Debugging Best Practices Applied**
1. **Follow the Data**: 3000+ images saved but 0 database records = database insertion problem
2. **Fix First, Improve Later**: Get working system before adding features
3. **Use Working Patterns**: `save_detection()` worked, so use it
4. **Minimal Viable Fix**: Change only the broken component

#### **Key Debugging Rules**
- When debugging, check what WAS working recently
- Look for incomplete feature rollouts  
- Test simplest fix first
- Don't rebuild working components
- **Fix first, optimize later**

### What's Still Missing & Next Steps

#### **Detection System Gaps**
- [ ] Detection statistics endpoint returns 0 (needs investigation)
- [ ] Camera names not showing in detection results (shows camera_id)
- [ ] No detection history visualization in frontend
- [ ] Universal detection system incomplete (should complete or remove)

#### **Documentation Needed**
- [ ] Detection API endpoint documentation
- [ ] Filter configuration guide
- [ ] Detection troubleshooting guide
- [ ] Migration strategy documentation

#### **System Improvements**
- [ ] Add detection rate monitoring
- [ ] Implement detection quality scoring
- [ ] Add detection export functionality
- [ ] Create detection analytics dashboard

### Phantom Camera Prevention ✅ Implemented (2025-08-30)

#### **Problem Solved**
- Orphaned recording folders created phantom camera entries in UI
- When cameras were deleted, their 200GB+ recording folders remained
- UI scanned folders and displayed them as fake camera cards
- Users saw "Entrance Gate" and "Entrance Gate (3)" that weren't real cameras

#### **Solution Implemented**
1. **Stable Camera ID System**: Cameras now use stable IDs like "reolink_camera" instead of dynamic IDs
2. **Recording Migration**: Existing recordings moved from `camera_a171d280fdc7` to `reolink_camera`  
3. **Orphan Cleanup**: Removed 183.6GB of orphaned recordings from deleted cameras
4. **Prevention**: Future cameras will use location-based stable IDs for recording folders

#### **Scripts Available**
- `scripts/cleanup_orphaned_recordings.py` - Remove orphaned recording folders
- `scripts/migrate_to_stable_ids.py` - Migrate existing recordings to stable IDs
- `scripts/debug_cameras.py` - Debug camera vs recording folder mismatches

#### **Benefits**
- **No more phantom cameras**: Recording folders won't create fake camera entries
- **Recording continuity**: Replace camera hardware without losing recording history
- **Clean UI**: Only real, active cameras appear in camera management
- **Future-proof**: Location-based naming (e.g., "front_entrance", "parking_lot_1")

### Future Phases
- Phase 3: Security hardening (auth, encryption, HTTPS)
- Phase 4: Deployment hardening (containers, monitoring)
- **Phase 5**: Complete camera UI integration with stable ID selection