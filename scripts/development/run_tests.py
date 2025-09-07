#!/usr/bin/env python3
"""
LPR System Test Runner
Convenient script to run various test suites
"""
import sys
import subprocess
import os
from pathlib import Path

def run_command(cmd, description=""):
    """Run a command and return success status"""
    print(f"🚀 {description}")
    print(f"   Command: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=Path.cwd())
    success = result.returncode == 0
    print(f"   Result: {'✅ PASSED' if success else '❌ FAILED'}\n")
    return success

def main():
    """Main test runner"""
    if len(sys.argv) < 2:
        print("""
🧪 LPR System Test Runner

Usage: python3 run_tests.py <test_type> [options]

Test Types:
  all           - Run all tests (comprehensive + v3)
  v3            - Test API v3 endpoints only
  endpoints     - Test all API endpoints (comprehensive)
  unit          - Run pytest unit tests
  integration   - Run pytest integration tests
  fast          - Run fast tests only (no slow/gpu/camera)
  coverage      - Run tests with coverage report

Examples:
  python3 run_tests.py v3
  python3 run_tests.py all
  python3 run_tests.py unit
  python3 run_tests.py coverage
        """)
        return False
    
    test_type = sys.argv[1].lower()
    
    # Ensure we're in the project root (go up two levels from scripts/development/)
    project_root = Path(__file__).parent.parent.parent
    os.chdir(project_root)
    
    success = True
    
    if test_type == "v3":
        success &= run_command([
            "python3", "tests/unit/test_api_v3.py"
        ], "Running API v3 Tests")
        
    elif test_type == "endpoints":
        success &= run_command([
            "python3", "tests/unit/test_all_endpoints.py"
        ], "Running Comprehensive Endpoint Tests")
        
    elif test_type == "all":
        success &= run_command([
            "python3", "tests/unit/test_api_v3.py"
        ], "Running API v3 Tests")
        
        success &= run_command([
            "python3", "tests/unit/test_all_endpoints.py"
        ], "Running Comprehensive Endpoint Tests")
        
    elif test_type == "unit":
        success &= run_command([
            "python3", "-m", "pytest", "tests/unit/", "-v", "-m", "unit"
        ], "Running Unit Tests")
        
    elif test_type == "integration":
        success &= run_command([
            "python3", "-m", "pytest", "tests/integration/", "-v", "-m", "integration"
        ], "Running Integration Tests")
        
    elif test_type == "fast":
        success &= run_command([
            "python3", "-m", "pytest", "-v", "-m", "not slow and not gpu and not camera"
        ], "Running Fast Tests")
        
    elif test_type == "coverage":
        success &= run_command([
            "python3", "-m", "pytest", "--cov", "--cov-report=term-missing", "--cov-report=html"
        ], "Running Tests with Coverage")
        
    else:
        print(f"❌ Unknown test type: {test_type}")
        return False
    
    print("=" * 60)
    if success:
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 60)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)