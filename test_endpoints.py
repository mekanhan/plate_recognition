#!/usr/bin/env python3
"""
Quick endpoint testing script - runs the comprehensive test suite
"""
import subprocess
import sys
import os

def main():
    """Run endpoint tests"""
    print("🚀 Starting Endpoint Testing Suite...")
    
    # Add current directory to Python path
    current_dir = os.getcwd()
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    try:
        # Run the comprehensive test
        result = subprocess.run([
            sys.executable, 
            "tests/unit/test_all_endpoints.py"
        ], cwd=current_dir, capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
            
        return result.returncode == 0
        
    except FileNotFoundError:
        print("❌ Test script not found. Running basic test instead...")
        
        # Fallback to basic test
        try:
            result = subprocess.run([
                sys.executable,
                "tests/unit/test_api.py"
            ], cwd=current_dir)
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Could not run tests: {e}")
            return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\\n✅ All tests completed!")
    else:
        print("\\n❌ Some tests failed!")
    sys.exit(0 if success else 1)