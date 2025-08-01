#!/usr/bin/env python3
"""
Stop All Services Script
Gracefully stops all LPR system services
"""
import os
import sys
import signal
import subprocess
import time

def find_processes_on_ports(ports):
    """Find processes listening on specific ports using lsof"""
    processes = []
    
    for port in ports:
        try:
            # Use lsof to find processes on the port
            result = subprocess.run(
                ['lsof', '-i', f':{port}', '-t'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        # Get process info
                        try:
                            cmd_result = subprocess.run(
                                ['ps', '-p', pid, '-o', 'pid,comm,args', '--no-headers'],
                                capture_output=True,
                                text=True
                            )
                            if cmd_result.returncode == 0:
                                process_info = cmd_result.stdout.strip()
                                processes.append({
                                    'pid': int(pid),
                                    'port': port,
                                    'info': process_info
                                })
                        except Exception:
                            pass
        except Exception as e:
            print(f"Warning: Could not check port {port}: {e}")
    
    return processes

def get_service_name(port):
    """Get service name based on port"""
    service_map = {
        8001: 'Main API',
        8002: '24/7 Recording Service',
        8080: 'Frontend Server'
    }
    return service_map.get(port, f'Service on port {port}')

def stop_process_by_pid(pid, service_name):
    """Stop a process by PID"""
    try:
        print(f"🛑 Stopping {service_name} (PID: {pid})...")
        
        # Try graceful shutdown with SIGTERM
        try:
            os.kill(pid, signal.SIGTERM)
            
            # Wait up to 10 seconds for graceful shutdown
            for i in range(10):
                try:
                    # Check if process still exists
                    os.kill(pid, 0)
                    time.sleep(1)
                except ProcessLookupError:
                    print(f"   ✅ {service_name} stopped gracefully")
                    return True
            
            # If still running, force kill
            print(f"   🔨 Force killing {service_name}...")
            os.kill(pid, signal.SIGKILL)
            time.sleep(1)
            print(f"   ✅ {service_name} force stopped")
            return True
            
        except ProcessLookupError:
            print(f"   ✅ {service_name} already stopped")
            return True
            
    except Exception as e:
        print(f"   ❌ Error stopping {service_name}: {e}")
        return False

def main():
    """Main stop function"""
    print("=" * 50)
    print("🛑 STOPPING LPR SYSTEM SERVICES")
    print("=" * 50)
    
    # Find processes on our service ports
    service_ports = [8001, 8002, 8080]
    processes = find_processes_on_ports(service_ports)
    
    if not processes:
        print("✅ No LPR services found running")
        return 0
    
    print(f"Found {len(processes)} running services:")
    for proc in processes:
        service_name = get_service_name(proc['port'])
        print(f"   - {service_name} (PID: {proc['pid']}, Port: {proc['port']})")
    print()
    
    # Stop all processes
    stopped_count = 0
    for proc in processes:
        service_name = get_service_name(proc['port'])
        if stop_process_by_pid(proc['pid'], service_name):
            stopped_count += 1
    
    # Give processes time to clean up
    time.sleep(2)
    
    # Double-check ports are free
    print("\n🔍 Verifying ports are free...")
    remaining = find_processes_on_ports(service_ports)
    
    if remaining:
        print(f"⚠️  {len(remaining)} processes still running, attempting force kill...")
        for proc in remaining:
            try:
                os.kill(proc['pid'], signal.SIGKILL)
                print(f"   🔨 Force killed PID {proc['pid']}")
            except Exception:
                pass
    
    print("\n" + "=" * 50)
    if stopped_count == len(processes):
        print("✅ ALL SERVICES STOPPED SUCCESSFULLY")
    else:
        print(f"⚠️  {stopped_count}/{len(processes)} services stopped")
    print("=" * 50)
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n🛑 Stop operation cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during stop operation: {e}")
        sys.exit(1)