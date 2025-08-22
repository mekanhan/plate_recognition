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

### Future Phases
- Phase 3: Security hardening (auth, encryption, HTTPS)
- Phase 4: Deployment hardening (containers, monitoring)