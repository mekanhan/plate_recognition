# Test Structure Migration Guide

## Summary

The test suite has been reorganized from scattered test files to a proper, maintainable structure under the `tests/` directory.

## What Changed

### ✅ Completed Migration

**Old Structure (Scattered):**
```
/
├── test_camera_api.py
├── test_detection_monitor.py  
├── test_detection_manual.py
├── test_image_saving.py
├── test_smart_storage.py
├── test_dedup_fix.py
├── test_monitoring.py
├── test_analytics.py
└── test/
    └── unit/
        ├── test_api.py
        ├── test_camera.py
        └── ...
```

**New Structure (Organized):**
```
tests/
├── __init__.py           # Test suite documentation
├── conftest.py          # Shared fixtures and configuration
├── README.md            # Comprehensive test guide
├── unit/                # Unit tests for components
├── integration/         # Integration tests
├── functional/          # End-to-end tests
├── performance/         # Performance tests
├── fixtures/            # Test data
└── html/               # HTML test files
```

## New Features Added

### 1. **Test Runner Script**
```bash
# Easy test execution
python run_tests.py unit          # Run unit tests
python run_tests.py integration   # Run integration tests
python run_tests.py fast          # Run fast tests only
python run_tests.py coverage      # Generate coverage report
```

### 2. **Pytest Configuration**
- `pytest.ini` - Comprehensive pytest settings
- `.coveragerc` - Coverage configuration
- Test markers for selective execution
- Parallel test execution support

### 3. **Shared Fixtures** (`tests/conftest.py`)
- `test_db` - In-memory test database
- `api_client` - FastAPI test client
- `auth_headers` - Authentication headers
- `mock_camera_stream` - Mock camera for testing
- `benchmark_timer` - Performance timing
- Auto-cleanup of test files

### 4. **Test Dependencies** (`requirements-test.txt`)
```bash
pip install -r requirements-test.txt
```

## Migration Steps Performed

1. ✅ Created organized test directory structure
2. ✅ Moved scattered test files to appropriate directories:
   - Unit tests → `tests/unit/`
   - Integration tests → `tests/integration/`
   - Functional tests → `tests/functional/`
3. ✅ Created comprehensive test configuration files
4. ✅ Added shared fixtures and utilities
5. ✅ Created test runner for convenience
6. ✅ Added test documentation

## File Locations After Migration

| Old Location | New Location | Type |
|-------------|--------------|------|
| `/test_monitoring.py` | `/tests/unit/test_monitoring.py` | Unit |
| `/test_analytics.py` | `/tests/unit/test_analytics.py` | Unit |
| `/test_dedup_fix.py` | `/tests/unit/test_dedup_fix.py` | Unit |
| `/test_smart_storage.py` | `/tests/unit/test_smart_storage.py` | Unit |
| `/test_camera_api.py` | `/tests/integration/test_camera_api.py` | Integration |
| `/test_detection_monitor.py` | `/tests/functional/test_detection_monitor.py` | Functional |
| `/test_detection_manual.py` | `/tests/functional/test_detection_manual.py` | Functional |
| `/test_image_saving.py` | `/tests/functional/test_image_saving.py` | Functional |
| `/test/unit/*` | `/tests/unit/*` | Unit |

## Benefits of New Structure

1. **Better Organization** - Tests grouped by type and purpose
2. **Easier Discovery** - Pytest automatically finds all tests
3. **Selective Execution** - Run only the tests you need
4. **Shared Resources** - Common fixtures reduce duplication
5. **CI/CD Ready** - Proper structure for automation
6. **Coverage Reports** - Built-in coverage analysis
7. **Performance Testing** - Dedicated performance test support
8. **Documentation** - Clear guidelines for writing tests

## How to Use

### Running Tests

```bash
# Run all tests
pytest

# Run specific category
pytest tests/unit/
pytest tests/integration/

# Run with markers
pytest -m "unit and not slow"
pytest -m "database"

# Run with coverage
pytest --cov --cov-report=html

# Use the test runner
python run_tests.py unit
python run_tests.py coverage
```

### Writing New Tests

1. Place test in appropriate directory
2. Use appropriate markers (`@pytest.mark.unit`, etc.)
3. Follow naming convention: `test_<feature>.py`
4. Use shared fixtures from `conftest.py`
5. Add docstrings to explain test purpose

### Example Test

```python
import pytest

class TestNewFeature:
    """Test suite for new feature"""
    
    @pytest.mark.unit
    def test_feature_behavior(self):
        """Test that feature behaves correctly"""
        # Arrange
        input_data = "test"
        
        # Act
        result = process_feature(input_data)
        
        # Assert
        assert result == expected_value
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_feature_with_database(self, test_db):
        """Test feature with database interaction"""
        result = await test_db.query_something()
        assert result is not None
```

## Cleanup Required

The old `test/` directory can be removed after verifying all tests work:

```bash
# After verification, remove old test directory
rm -rf test/

# Remove scattered test files (already moved)
rm test_*.py  # (in root directory)
```

## Next Steps

1. ✅ Test structure migrated
2. ⏳ Update CI/CD pipelines to use new structure
3. ⏳ Add more comprehensive test coverage
4. ⏳ Set up automated test runs on commits

This migration improves code quality and development workflow significantly!