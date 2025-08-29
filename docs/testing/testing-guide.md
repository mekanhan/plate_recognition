# API Testing Guide

## Test Scripts Overview

This document describes the testing infrastructure for the License Plate Recognition API system.

## Available Test Scripts

### 1. Comprehensive Endpoint Testing

**File**: `tests/unit/test_all_endpoints.py`
**Purpose**: Tests all 52 API endpoints across all categories
**Usage**: 
```bash
python3 tests/unit/test_all_endpoints.py
# OR
python3 test_endpoints.py  # Convenience wrapper
```

**Coverage**:
- System Health & Status (5 endpoints)
- Camera Management (16 endpoints) 
- ONVIF Discovery (4 endpoints)
- Detection Management (11 endpoints)
- Analytics & Quality (5 endpoints)
- Storage Management (3 endpoints)
- Video Management (1 endpoint)

### 2. Basic API Testing

**File**: `tests/unit/test_api.py`
**Purpose**: Tests core functionality with detailed output
**Usage**:
```bash
python3 tests/unit/test_api.py
```

**Coverage**:
- Health checks
- Camera operations
- Detection queries
- Analytics data
- VLC integration

## Test Categories

### Expected Response Codes

The test suite expects different response codes based on endpoint type:

- **200 OK**: Successfully working endpoints
- **404 Not Found**: Expected for non-existent resources (cameras, detections)
- **422 Unprocessable Entity**: Expected for endpoints requiring request data
- **500 Server Error**: ❌ Indicates database session or server issues

### Database Session Testing

All endpoints have been updated to use FastAPI dependency injection:
```python
db_service: DatabaseService = Depends(get_database_service)
```

This eliminates the "Could not locate a bind configured on mapper" errors that previously caused 500 responses.

## Running Tests

### Prerequisites

1. **Start Services**:
   ```bash
   python3 bin/start_lpr.py
   ```

2. **Verify Services Running**:
   ```bash
   python3 bin/check_services.py
   ```

### Test Execution

#### Comprehensive Test Suite
```bash
# Run full endpoint test suite
python3 test_endpoints.py

# Run comprehensive test directly
python3 tests/unit/test_all_endpoints.py
```

#### Individual Test Scripts
```bash
# Basic API functionality
python3 tests/unit/test_api.py

# Camera-specific testing
python3 tests/unit/test_camera.py

# Database testing
python3 tests/unit/test_database.py
```

### Test Results

Test results are saved to `tests/results/` with timestamps:
- JSON format with detailed endpoint responses
- Pass/fail statistics
- Error details for debugging

## Interpreting Results

### Success Indicators
- ✅ 200 responses for working endpoints
- ✅ 404 responses for non-existent resources
- ✅ JSON responses with expected data structure

### Failure Indicators  
- ❌ 500 Server Error (database session issues)
- ❌ Connection timeouts
- ❌ Unexpected response codes

### Common Issues

#### Database Session Errors
**Symptom**: 500 responses with "Could not locate a bind configured on mapper"
**Solution**: Verify all endpoints use dependency injection pattern

#### Service Not Running
**Symptom**: Connection refused errors
**Solution**: Start services with `python3 bin/start_lpr.py`

#### Port Conflicts
**Symptom**: Tests fail with connection errors
**Solution**: Verify API running on port 8001, update test scripts if needed

## Test Environment

### API Base URL
- **Production/Testing**: `http://localhost:8001`
- **Legacy/Development**: `http://localhost:8000` (outdated)

### Required Services
1. **Main API** (port 8001): Camera management, detection endpoints
2. **Recording Service** (port 8002): 24/7 recording functionality  
3. **Frontend** (port 8080): Web interface (not tested by API scripts)

## Automation

### Continuous Testing
```bash
# Run tests every 5 minutes (example)
while true; do
    python3 test_endpoints.py
    sleep 300
done
```

### Integration with CI/CD
The test scripts return proper exit codes:
- Exit 0: All tests passed
- Exit 1: Some tests failed

## Performance Testing

### Response Time Monitoring
The test suite measures response times and flags slow endpoints:
- ✅ < 100ms: Fast
- ⚠️  100-500ms: Acceptable
- ❌ > 500ms: Slow (investigate)

### Load Testing
For load testing specific endpoints:
```bash
# Example using curl for basic load testing
for i in {1..100}; do
    curl -s http://localhost:8001/api/cameras > /dev/null &
done
wait
```

## Troubleshooting

### Common Test Failures

1. **Detection Endpoints (500 errors)**
   - Check database session configuration
   - Verify DatabaseService dependency injection

2. **Camera Endpoints (404 errors)**
   - Expected behavior for non-existent cameras
   - Add real camera for testing success cases

3. **ONVIF Discovery Timeouts**
   - Network-dependent operations may be slow
   - Consider increasing timeout for network tests

### Debug Mode

Add debug output to test scripts:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

### Planned Test Improvements
1. **Authentication Testing**: When auth is implemented
2. **Load Testing**: Automated performance benchmarks  
3. **Integration Testing**: End-to-end workflow testing
4. **Mock Data**: Consistent test data for reproducible results

### Test Coverage Goals
- 100% endpoint coverage ✅ (52/52 endpoints)
- Error condition testing
- Performance benchmarking
- Security testing (when auth implemented)