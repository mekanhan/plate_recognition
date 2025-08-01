#!/usr/bin/env python3
"""
Simple script to start the LPR system
"""
import subprocess
import time
import os
import sys

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    print("="*70)
    print("   LICENSE PLATE RECOGNITION SYSTEM")
    print("   Clean Architecture Implementation")
    print("="*70)
    print()

def check_dependencies():
    print("Checking dependencies...")
    result = subprocess.run([sys.executable, "test_imports.py"], capture_output=True)
    if result.returncode == 0:
        print("✅ All dependencies are installed")
        return True
    else:
        print("❌ Some dependencies are missing")
        print("Run: pip install -r requirements.txt")
        return False

def main():
    clear_screen()
    print_banner()
    
    if not check_dependencies():
        sys.exit(1)
    
    print("\n" + "="*70)
    print("STARTING LPR SYSTEM")
    print("="*70)
    
    print("\n📋 Instructions:\n")
    
    print("1. Start the API server (in a new terminal):")
    print("   cd", os.getcwd())
    print("   python -m api.main")
    print()
    
    print("2. Start the frontend server (in another terminal):")
    print("   cd frontend")
    print("   python3 -m http.server 8080")
    print()
    
    print("3. Open your browser to:")
    print("   http://localhost:8080")
    print()
    
    print("4. API documentation available at:")
    print("   http://localhost:8000/docs")
    print()
    
    print("="*70)
    print("QUICK TESTS:")
    print("="*70)
    
    print("\n1. Test imports:        python test_imports.py")
    print("2. Test camera:         python test_camera.py")
    print("3. Test AI:            python test_ai.py")
    print("4. Test database:      python test_database.py")
    print("5. Test API:           python test_api.py")
    print("6. Full system test:   python full_test.py")
    
    print("\n="*70)
    print("IMPORTANT REMINDERS:")
    print("="*70)
    print("✅ This system uses SNAPSHOTS in the browser (not video streaming)")
    print("✅ For live video, use VLC with the RTSP URLs")
    print("✅ Configure your cameras in config/cameras.yaml")
    print("✅ Check logs in the API terminal for detection events")
    
    print("\n" + "="*70)
    
    # Ask if user wants to start API
    response = input("\nWould you like to start the API server now? (y/n): ")
    if response.lower() == 'y':
        print("\nStarting API server...")
        print("Press Ctrl+C to stop\n")
        subprocess.run([sys.executable, "-m", "api.main"])

if __name__ == "__main__":
    main()