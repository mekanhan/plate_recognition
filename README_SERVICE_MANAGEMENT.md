# Service Management Scripts

This directory contains comprehensive service management scripts for the License Plate Recognition system.

## Quick Start

### Start All Services
```bash
python start_all_services.py
```
This will start:
- Main API on port 8001
- 24/7 Recording Service on port 8002  
- Frontend Server on port 8080

### Stop All Services
```bash
python stop_all_services.py
```

### Check Service Health
```bash
python check_services.py
```

### Restart All Services
```bash
python restart_services.py
```

## Script Details

### start_all_services.py
- **Purpose**: Master startup script with process management
- **Features**:
  - Starts all services in proper order
  - Creates log files for each service
  - Monitors service health during startup
  - Provides graceful shutdown on Ctrl+C
  - Shows service URLs when ready

### stop_all_services.py
- **Purpose**: Gracefully stop all running services
- **Features**:
  - Finds all LPR-related processes
  - Attempts graceful shutdown (SIGTERM)
  - Force kills if needed (SIGKILL)
  - Clears processes on service ports

### check_services.py
- **Purpose**: Health monitoring and status checking
- **Features**:
  - Tests HTTP endpoints for each service
  - Measures response times
  - Validates API responses
  - Supports continuous monitoring
- **Usage**:
  ```bash
  python check_services.py           # Single check
  python check_services.py -m 30     # Monitor every 30 seconds
  ```

### restart_services.py
- **Purpose**: Complete system restart
- **Features**:
  - Stops all services
  - Waits for cleanup
  - Starts all services
  - Verifies successful startup

## Service Configuration

### Port Assignments
- **8001**: Main API (FastAPI backend)
- **8002**: 24/7 Recording Service  
- **8080**: Frontend Server (HTTP server)

### Log Files
All services create timestamped log files in the `logs/` directory:
- `main_api_YYYYMMDD_HHMMSS.log`
- `recording_service_YYYYMMDD_HHMMSS.log`
- `frontend_YYYYMMDD_HHMMSS.log`

### Health Check Endpoints
- Main API: `http://localhost:8001/health`
- Recording Service: `http://localhost:8002/health`
- Frontend: `http://localhost:8080/` (HTML response)

## Process Management Features

### Graceful Shutdown
- Services receive SIGTERM signal first
- 10-second timeout for graceful shutdown
- Force kill (SIGKILL) if needed
- Cleanup of resources and connections

### Service Monitoring
- Real-time health checks during startup
- Background monitoring of service status
- Automatic detection of failed services
- Port availability checking

### Error Handling
- Comprehensive error messages
- Fallback mechanisms
- Service dependency management
- Resource cleanup on failure

## Troubleshooting

### Port Already in Use
If you get "port already in use" errors:
1. Run `python stop_all_services.py`
2. Wait a few seconds
3. Try starting again

### Service Won't Start
1. Check the log files in `logs/` directory
2. Verify Python dependencies are installed
3. Ensure required directories exist
4. Check for permission issues

### Health Check Failures
1. Verify services are actually running
2. Check firewall/network settings
3. Look for errors in service logs
4. Ensure database connectivity

## Advanced Usage

### Background Operation
To run services in the background:
```bash
nohup python start_all_services.py > system.log 2>&1 &
```

### Service-Specific Startup
You can still start individual services:
```bash
python start_recording_service.py  # Recording service only
python -m api.main                 # Main API only
cd frontend && python -m http.server 8080  # Frontend only
```

### Monitoring Integration
The health check script can be integrated with monitoring systems:
```bash
python check_services.py && echo "All healthy" || echo "Issues detected"
```

## Integration with CLAUDE.md

These scripts are designed to work with the commands documented in `CLAUDE.md`:

```bash
# Old way (manual)
cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# New way (automated)
python start_all_services.py
```

The service management scripts provide the same functionality with additional benefits:
- Process management
- Health monitoring  
- Graceful shutdown
- Centralized logging
- Error handling