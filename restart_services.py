#!/usr/bin/env python3
"""
Restart Services Script
Gracefully stops and restarts all LPR system services
"""
import sys
import time
import subprocess
from pathlib import Path

def run_script(script_name, description):
    """Run a script and return success status"""
    try:
        print(f"🔄 {description}...")
        # Use venv Python if available
        venv_python = Path(".venv/bin/python3")
        if venv_python.exists():
            python_exe = str(venv_python.absolute())
        else:
            python_exe = 'python3'
        
        result = subprocess.run([python_exe, script_name], 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print(f"   ✅ {description} completed successfully")
            if result.stdout.strip():
                # Show last few lines of output
                lines = result.stdout.strip().split('\n')
                for line in lines[-3:]:
                    if line.strip():
                        print(f"   {line}")
            return True
        else:
            print(f"   ❌ {description} failed (exit code: {result.returncode})")
            if result.stderr.strip():
                print(f"   Error: {result.stderr.strip()}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"   ⏰ {description} timed out")
        return False
    except Exception as e:
        print(f"   ❌ {description} failed: {e}")
        return False

def check_script_exists(script_name):
    """Check if a script file exists"""
    script_path = Path(script_name)
    if not script_path.exists():
        print(f"❌ Script not found: {script_name}")
        return False
    return True

def main():
    """Main restart function"""
    print("=" * 70)
    print("🔄 RESTARTING LPR SYSTEM SERVICES")
    print("=" * 70)
    
    # Check if required scripts exist
    required_scripts = ['stop_all_services.py', 'start_all_services.py']
    for script in required_scripts:
        if not check_script_exists(script):
            print(f"❌ Cannot proceed without {script}")
            return 1
    
    print("📋 Restart sequence:")
    print("   1. Stop all running services")
    print("   2. Wait for cleanup")
    print("   3. Start all services")
    print("   4. Verify startup")
    print()
    
    # Step 1: Stop services
    if not run_script('stop_all_services.py', 'Stopping all services'):
        print("⚠️  Stop operation had issues, but continuing with restart...")
    
    # Step 2: Wait for cleanup
    print("⏰ Waiting 5 seconds for complete cleanup...")
    time.sleep(5)
    
    # Step 3: Start services
    print("\n" + "=" * 50)
    # Use detached start script for restart
    if not run_script('start_services_detached.py', 'Starting all services'):
        print("❌ Failed to start services")
        return 1
    
    # Step 4: Wait and verify
    print("\n⏰ Waiting 10 seconds for services to initialize...")
    time.sleep(10)
    
    # Optional: Check if check_services.py exists and run it
    if check_script_exists('check_services.py'):
        print("\n" + "=" * 50)
        print("🔍 Verifying service health...")
        run_script('check_services.py', 'Health check')
    
    print("\n" + "=" * 70)
    print("✅ RESTART SEQUENCE COMPLETED")
    print("=" * 70)
    print("🌐 Services should be available at:")
    print("   Frontend:        http://localhost:8080/")
    print("   Main API:        http://localhost:8001/docs")
    print("   Recording API:   http://localhost:8002/docs")
    print("=" * 70)
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n🛑 Restart operation cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during restart: {e}")
        sys.exit(1)