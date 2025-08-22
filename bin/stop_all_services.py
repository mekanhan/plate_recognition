#!/usr/bin/env python3
"""
Stop All Services Script
Gracefully stops all LPR system services with validation
"""
import os
import sys
import signal
import subprocess
import time
import json
import urllib.request
import urllib.error

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

def try_graceful_recording_shutdown():
    """Try to gracefully shutdown recording service via API"""
    try:
        # First check if recording service is running
        req = urllib.request.Request('http://localhost:8002/health/detailed')
        req.add_header('User-Agent', 'LPR-Stop/1.0')
        
        with urllib.request.urlopen(req, timeout=5) as response:
            health_data = json.loads(response.read().decode('utf-8'))
            
            print("📹 Recording Service Status:")
            rec_status = health_data.get('recording_status', {})
            active = rec_status.get('active_recordings', 0)
            total = rec_status.get('total_cameras', 0)
            
            if active > 0:
                print(f"   Active recordings: {active}/{total} cameras")
                print("   Initiating graceful shutdown...")
                
                # Request graceful shutdown
                shutdown_req = urllib.request.Request(
                    'http://localhost:8002/shutdown',
                    method='POST'
                )
                shutdown_req.add_header('User-Agent', 'LPR-Stop/1.0')
                
                with urllib.request.urlopen(shutdown_req, timeout=5) as shutdown_response:
                    shutdown_data = json.loads(shutdown_response.read().decode('utf-8'))
                    print(f"   ✅ Shutdown initiated: {shutdown_data.get('message')}")
                    
                    # Monitor shutdown progress
                    max_wait = shutdown_data.get('max_wait_seconds', 30)
                    start_time = time.time()
                    
                    while time.time() - start_time < max_wait:
                        try:
                            # Check shutdown progress
                            req = urllib.request.Request('http://localhost:8002/health/detailed')
                            req.add_header('User-Agent', 'LPR-Stop/1.0')
                            
                            with urllib.request.urlopen(req, timeout=2) as check_response:
                                check_data = json.loads(check_response.read().decode('utf-8'))
                                shutdown_status = check_data.get('shutdown_status', {})
                                
                                if shutdown_status.get('is_shutting_down'):
                                    stopped = shutdown_status.get('cameras_stopped', 0)
                                    print(f"   ⏳ Stopping cameras: {stopped}/{total}")
                                    time.sleep(2)
                                else:
                                    print("   ✅ Recording service shutdown complete")
                                    return True
                                    
                        except urllib.error.URLError:
                            # Service no longer responding, likely shut down
                            print("   ✅ Recording service stopped")
                            return True
                    
                    print("   ⚠️  Graceful shutdown timeout, will force stop")
                    return False
            else:
                print("   No active recordings")
                return True
                
    except urllib.error.URLError:
        print("📹 Recording Service: Not responding (may already be stopped)")
        return True
    except Exception as e:
        print(f"📹 Recording Service: Error during graceful shutdown: {e}")
        return False

def validate_service_stopped(port, service_name, max_wait=10):
    """Validate that a service has actually stopped"""
    print(f"\n🔍 Validating {service_name} shutdown...")
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        processes = find_processes_on_ports([port])
        if not processes:
            print(f"   ✅ {service_name} fully stopped (port {port} released)")
            return True
        
        print(f"   ⏳ Waiting for {service_name} to release port {port}...")
        time.sleep(1)
    
    print(f"   ❌ {service_name} still holding port {port}")
    return False

def main():
    """Main stop function"""
    print("=" * 50)
    print("🛑 STOPPING LPR SYSTEM SERVICES WITH VALIDATION")
    print("=" * 50)
    
    # First, try graceful shutdown for recording service
    recording_shutdown_success = try_graceful_recording_shutdown()
    
    # Find processes on our service ports
    service_ports = [8001, 8002, 8080]
    processes = find_processes_on_ports(service_ports)
    
    if not processes:
        print("\n✅ No LPR services found running")
        return 0
    
    print(f"\nFound {len(processes)} running services:")
    for proc in processes:
        service_name = get_service_name(proc['port'])
        print(f"   - {service_name} (PID: {proc['pid']}, Port: {proc['port']})")
    print()
    
    # Stop all processes
    stopped_count = 0
    validation_results = {}
    
    for proc in processes:
        service_name = get_service_name(proc['port'])
        port = proc['port']
        
        # Special handling for recording service if graceful shutdown succeeded
        if port == 8002 and recording_shutdown_success:
            print(f"🛑 {service_name} already shutting down gracefully...")
            # Wait a bit longer for graceful shutdown
            time.sleep(3)
            # Verify it's actually stopped
            if not find_processes_on_ports([8002]):
                stopped_count += 1
                validation_results[port] = True
                continue
        
        # Normal stop process
        if stop_process_by_pid(proc['pid'], service_name):
            stopped_count += 1
    
    # Give processes time to clean up
    time.sleep(2)
    
    # Validate each service is actually stopped
    print("\n🔍 Validating service shutdown...")
    all_validated = True
    
    for port in service_ports:
        service_name = get_service_name(port)
        if port not in validation_results:
            validation_results[port] = validate_service_stopped(port, service_name)
        
        if not validation_results[port]:
            all_validated = False
    
    # Final check - force kill any remaining processes
    if not all_validated:
        print("\n⚠️  Some services didn't stop cleanly, attempting force cleanup...")
        remaining = find_processes_on_ports(service_ports)
        
        for proc in remaining:
            try:
                os.kill(proc['pid'], signal.SIGKILL)
                print(f"   🔨 Force killed PID {proc['pid']} on port {proc['port']}")
            except Exception:
                pass
        
        # Final validation
        time.sleep(1)
        for port in service_ports:
            if not validation_results[port]:
                service_name = get_service_name(port)
                if not find_processes_on_ports([port]):
                    print(f"   ✅ {service_name} finally stopped (port {port} released)")
                    validation_results[port] = True
                else:
                    print(f"   ❌ {service_name} still running on port {port}")
    
    # Summary
    print("\n" + "=" * 50)
    print("SHUTDOWN SUMMARY:")
    print("-" * 50)
    
    for port in service_ports:
        service_name = get_service_name(port)
        status = "✅ Stopped" if validation_results.get(port, False) else "❌ Failed"
        print(f"{service_name}: {status}")
    
    print("-" * 50)
    
    if all(validation_results.get(port, False) for port in service_ports):
        print("✅ ALL SERVICES STOPPED AND VALIDATED SUCCESSFULLY")
        result = 0
    else:
        failed_count = sum(1 for port in service_ports if not validation_results.get(port, False))
        print(f"⚠️  {failed_count} services failed to stop properly")
        result = 1
    
    print("=" * 50)
    
    return result

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n🛑 Stop operation cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during stop operation: {e}")
        sys.exit(1)