#!/usr/bin/env python3
"""
Start Services in Detached Mode
Starts all services as background processes and exits
"""
import os
import sys
import subprocess
import time
from pathlib import Path

def start_service(name, command, cwd='.'):
    """Start a service in background"""
    try:
        # Use venv Python if available
        venv_python = Path(".venv/bin/python3")
        if venv_python.exists() and command[0] in ['python', 'python3', sys.executable]:
            command[0] = str(venv_python.absolute())
        
        # Create log directory
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Create log file
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"{name}_{timestamp}.log"
        
        # Start process in background
        with open(log_file, 'w') as log:
            process = subprocess.Popen(
                command,
                cwd=cwd,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True  # Detach from parent
            )
        
        print(f"✅ Started {name} (PID: {process.pid}, Log: {log_file})")
        return True
        
    except Exception as e:
        print(f"❌ Failed to start {name}: {e}")
        return False

def main():
    """Start all services"""
    print("=" * 60)
    print("🚀 STARTING LPR SERVICES (DETACHED)")
    print("=" * 60)
    
    # Check if venv exists
    venv_python = Path(".venv/bin/python3")
    if venv_python.exists():
        print(f"🐍 Using venv Python: {venv_python}")
    else:
        print("🐍 Using system Python")
    
    print()
    
    # Create necessary directories
    for dir_name in ["logs", "recordings", "detections", "detections/frames", "detections/plates", "static"]:
        Path(dir_name).mkdir(exist_ok=True)
    
    # Start services
    services = [
        {
            'name': 'main_api',
            'command': ['python3', '-m', 'api.main'],
            'cwd': '.'
        },
        {
            'name': 'recording_service',
            'command': ['python3', 'bin/service-management/start_recording_service.py'],
            'cwd': '.'
        },
        {
            'name': 'frontend',
            'command': ['python3', '-m', 'http.server', '8080', '--bind', '0.0.0.0'],
            'cwd': 'frontend'
        }
    ]
    
    success_count = 0
    for service in services:
        if start_service(service['name'], service['command'], service['cwd']):
            success_count += 1
        time.sleep(2)  # Brief pause between starts
    
    print()
    print("=" * 60)
    
    if success_count == len(services):
        print("✅ ALL SERVICES STARTED SUCCESSFULLY")
        print()
        print("🌐 Service URLs:")
        print("   Frontend:      http://localhost:8080/")
        print("   Main API:      http://localhost:8001/docs")
        print("   Recording API: http://localhost:8002/docs")
        print()
        print("🔍 Check status: python3 bin/check_services.py")
        print("🛑 Stop all:     python3 bin/stop_all_services.py")
    else:
        print(f"⚠️  Only {success_count}/{len(services)} services started")
        print("Check logs/ directory for error details")
    
    print("=" * 60)
    
    return 0 if success_count == len(services) else 1

if __name__ == "__main__":
    sys.exit(main())