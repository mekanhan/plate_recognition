#!/usr/bin/env python3
"""
Quick script to test system changes
Wrapper for the main test runner that was moved to scripts/development/
"""
import subprocess
import sys
from pathlib import Path

def main():
    """Run the main test runner from its new location"""
    script_path = Path("scripts/development/run_tests.py")
    
    if not script_path.exists():
        print("❌ Test runner not found at scripts/development/run_tests.py")
        return False
    
    # Pass all arguments to the main test runner
    cmd = [sys.executable, str(script_path)] + sys.argv[1:]
    result = subprocess.run(cmd)
    return result.returncode == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)