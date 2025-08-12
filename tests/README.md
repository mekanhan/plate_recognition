# LPR System Test Suite

## Overview

This directory contains the complete test suite for the License Plate Recognition (LPR) system. The tests are organized by type and scope to ensure comprehensive coverage and maintainability.

**Note**: This is the consolidated test directory. All test files from the legacy `/test/` directory have been migrated here for better organization.

## Directory Structure

```
tests/
├── unit/           # Unit tests for individual components
├── integration/    # Integration tests for service interactions
├── functional/     # End-to-end functional tests
├── performance/    # Performance and load tests
├── fixtures/       # Test data and fixtures
├── html/          # HTML test files for UI testing
└── conftest.py    # Shared pytest fixtures and configuration
```

## Running Tests

### Quick Start

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
pytest

# Run with coverage
pytest --cov

# Run specific test suite
python run_tests.py unit
python run_tests.py integration
python run_tests.py functional
```

### Using the Test Runner

The `run_tests.py` script provides convenient commands:

```bash
# Run all tests
python run_tests.py all

# Run unit tests only
python run_tests.py unit

# Run fast tests (no slow/gpu/camera tests)
python run_tests.py fast

# Run with coverage report
python run_tests.py coverage

# Run tests matching a keyword
python run_tests.py all -k "camera"

# Run tests with specific marker
python run_tests.py all -m "database"

# Run tests in parallel
python run_tests.py all --parallel

# Stop on first failure
python run_tests.py all --failfast
```

### Direct pytest Commands

```bash
# Run all tests with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_analytics.py

# Run tests matching pattern
pytest -k "test_detection"

# Run tests with specific marker
pytest -m "unit and not slow"

# Run with coverage and generate HTML report
pytest --cov --cov-report=html

# Run tests in parallel (requires pytest-xdist)
pytest -n auto
```

### Individual Test Execution (Legacy Method)

```bash
# Run from project root directory
cd /path/to/plate_recognition

# Test imports and dependencies
python3 tests/unit/test_imports.py

# Test database operations
python3 tests/unit/test_database.py

# Test API endpoints
python3 tests/unit/test_api.py

# Test AI pipeline
python3 tests/unit/test_ai.py

# Test camera connections
python3 tests/unit/test_camera.py

# Run camera diagnostics
python3 tests/unit/diagnose_camera.py 192.168.1.100 -u admin -P password
```

## Test Markers

Tests are marked with categories for selective execution:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.functional` - Functional tests
- `@pytest.mark.performance` - Performance tests
- `@pytest.mark.slow` - Slow running tests
- `@pytest.mark.gpu` - Tests requiring GPU
- `@pytest.mark.camera` - Tests requiring camera hardware
- `@pytest.mark.database` - Database interaction tests
- `@pytest.mark.api` - API endpoint tests
- `@pytest.mark.auth` - Authentication tests
- `@pytest.mark.monitoring` - Monitoring system tests
- `@pytest.mark.analytics` - Analytics system tests

## HTML Test Files (`tests/html/`)

The HTML test files provide browser-based testing and validation:

- `test_video.html` - Video playback testing with various formats
- `test_video_playback.html` - Advanced video playback controls testing
- `test_recording_playback.html` - Recording system playback testing
- `test_today_recording.html` - Today's recordings viewer and navigation

**Usage**: Open HTML files in browser by navigating to `http://localhost:8080/tests/html/[filename].html` when the frontend server is running.

## Test Categories

### Unit Tests (`tests/unit/`)
- Individual component testing
- Mocked dependencies
- Fast execution
- No external dependencies

#### Core Tests
- `test_imports.py` - Verify all dependencies are properly installed
- `test_database.py` - Database operations and CRUD functionality  
- `test_api.py` - API endpoint testing
- `test_ai.py` - AI detection pipeline testing
- `test_camera.py` - Camera connection and snapshot testing
- `test_analytics.py` - Analytics engine and visualization testing
- `test_monitoring.py` - Monitoring system and metrics testing
- `test_dedup_fix.py` - Deduplication system testing
- `test_smart_storage.py` - Storage management testing

#### Camera Tests
- `test_camera_fixed.py` - Test camera with working configuration
- `test_camera_recording.py` - FFmpeg recording from real camera
- `test_hikvision_streams.py` - Hikvision-specific stream testing

#### Utility Tests
- `diagnose_camera.py` - Comprehensive camera diagnostics tool
- `find_rtsp_url.py` - RTSP URL discovery utility
- `full_test.py` - Complete system integration test

Example:
```python
@pytest.mark.unit
def test_plate_validation():
    assert validate_plate("ABC1234") == True
```

### Integration Tests (`tests/integration/`)
- Service interaction testing
- API endpoint testing
- Database integration
- Multiple component interaction

Example:
```python
@pytest.mark.integration
async def test_camera_api(api_client):
    response = await api_client.get("/api/cameras")
    assert response.status_code == 200
```

### Functional Tests (`tests/functional/`)
- End-to-end scenarios
- Complete workflows
- User journey testing
- System behavior validation

Example:
```python
@pytest.mark.functional
async def test_detection_workflow():
    # Complete detection workflow test
    pass
```

### Performance Tests (`tests/performance/`)
- Load testing
- Response time measurement
- Resource utilization
- Scalability testing

Example:
```python
@pytest.mark.performance
def test_detection_speed(benchmark_timer):
    benchmark_timer.start()
    # Performance critical operation
    elapsed = benchmark_timer.stop()
    assert elapsed < 0.1  # Must complete in 100ms
```

## Fixtures

Common fixtures are available in `conftest.py`:

### Database Fixtures
- `test_db` - In-memory test database
- `sample_camera_data` - Sample camera configuration
- `sample_detection_data` - Sample detection data

### API Fixtures
- `api_client` - FastAPI test client
- `auth_headers` - Authentication headers

### Mock Fixtures
- `mock_camera_stream` - Mock camera without hardware
- `mock_yolo_model` - Mock YOLO model

### Utility Fixtures
- `temp_dir` - Temporary directory for test files
- `test_image_path` - Test image file
- `benchmark_timer` - Performance timing

## Coverage Reports

Coverage reports are generated in multiple formats:

```bash
# Terminal report with missing lines
pytest --cov --cov-report=term-missing

# HTML report (opens in browser)
pytest --cov --cov-report=html
open htmlcov/index.html

# XML report (for CI/CD)
pytest --cov --cov-report=xml
```

## Writing Tests

### Test File Naming
- Unit tests: `test_<component>.py`
- Integration tests: `test_<feature>_integration.py`
- Functional tests: `test_<scenario>_functional.py`

### Test Class Structure
```python
class TestComponentName:
    """Test suite for ComponentName"""
    
    def setup_method(self):
        """Setup before each test"""
        pass
    
    def teardown_method(self):
        """Cleanup after each test"""
        pass
    
    @pytest.mark.unit
    def test_specific_behavior(self):
        """Test specific behavior description"""
        # Arrange
        # Act
        # Assert
```

### Async Tests
```python
@pytest.mark.asyncio
async def test_async_operation():
    result = await async_function()
    assert result is not None
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt -r requirements-test.txt
      - run: pytest --cov --cov-report=xml
      - uses: codecov/codecov-action@v2
```

## Best Practices

1. **Keep tests independent** - Each test should be able to run in isolation
2. **Use fixtures** - Don't repeat setup code, use fixtures
3. **Test one thing** - Each test should verify one specific behavior
4. **Use descriptive names** - Test names should describe what they test
5. **Mock external dependencies** - Unit tests shouldn't depend on external services
6. **Clean up resources** - Always clean up test files and resources
7. **Use markers** - Mark tests appropriately for selective execution
8. **Document complex tests** - Add docstrings explaining complex test logic

## Troubleshooting

### Common Issues

**Import errors:**
```bash
# Ensure project is in Python path
export PYTHONPATH=$PYTHONPATH:.
```

**Database tests failing:**
```bash
# Use in-memory database for tests
# Check conftest.py for test_db fixture
```

**GPU tests on CPU-only machines:**
```bash
# Skip GPU tests
pytest -m "not gpu"
```

**Camera tests without hardware:**
```bash
# Skip camera tests
pytest -m "not camera"
```

## Contributing

When adding new tests:
1. Place in appropriate directory (unit/integration/functional)
2. Use appropriate markers
3. Follow naming conventions
4. Add docstrings
5. Update this README if adding new patterns

## Contact

For questions about testing, create an issue in the repository.