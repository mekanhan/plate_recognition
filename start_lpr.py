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
    
    # Check if database schema needs updating
    db_path = Path("data/license_plates.db")
    if db_path.exists():
        print("📊 Checking database schema...")
        result = subprocess.run([sys.executable, "update_database_schema.py"], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Database update failed. Please check the error.")
            return 1
    
    # Use the detached start script
    print("🔄 Starting all services...")
    result = subprocess.run([sys.executable, "start_services_detached.py"])
    
    if result.returncode == 0:
        print("\n✅ System started successfully!")
        print("\n🌐 Access the system at:")
        print("   Frontend:      http://localhost:8080/")
        print("   API Docs:      http://localhost:8001/docs")
        print("   Recording API: http://localhost:8002/docs")
        print("\n🛑 To stop: python3 stop_all_services.py")
        return 0
    else:
        print("\n❌ Failed to start services")
        return 1

if __name__ == "__main__":
    sys.exit(main())