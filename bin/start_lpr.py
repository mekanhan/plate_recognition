#!/usr/bin/env python3
"""
Simple LPR System Startup Script
Just run: python3 start_lpr.py
"""
import subprocess
import sys
import time
from pathlib import Path

def main():
    print("🚀 Starting License Plate Recognition System...")
    
    # Check and apply pending database migrations
    print("📊 Checking database migrations...")
    result = subprocess.run([sys.executable, "tools/database/migrate.py", "upgrade"], 
                          capture_output=True, text=True)
    if result.returncode != 0:
        print("❌ Database migration failed. Please check the error.")
        if result.stderr:
            print(f"Error: {result.stderr}")
        return 1
    else:
        print("✅ Database migrations up to date")
    
    # Use the detached start script
    print("🔄 Starting all services...")
    result = subprocess.run([sys.executable, "bin/service-management/start_services_detached.py"])
    
    if result.returncode == 0:
        print("\n✅ System started successfully!")
        print("\n🌐 Access the system at:")
        print("   Frontend:      http://localhost:8080/")
        print("   API Docs:      http://localhost:8001/docs")
        print("   Recording API: http://localhost:8002/docs")
        print("\n🛑 To stop: python3 bin/stop_all_services.py")
        return 0
    else:
        print("\n❌ Failed to start services")
        return 1

if __name__ == "__main__":
    sys.exit(main())