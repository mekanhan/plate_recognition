#!/usr/bin/env python3
"""
Master Startup Script for License Plate Recognition System
Starts all services with process management, health monitoring, and graceful shutdown
"""
import os
import sys
import time
import signal
import socket
import subprocess
import threading
from pathlib import Path
from datetime import datetime

class ServiceManager:
    def __init__(self):
        self.services = {}
        self.running = True
        
        # Import log manager
        try:
            from utils.log_manager import get_service_logger
            self.logger = get_service_logger('service_manager')
            self.use_log_manager = True
        except ImportError:
            # Fallback to basic logging
            self.log_dir = Path("logs")
            self.log_dir.mkdir(exist_ok=True)
            self.use_log_manager = False
        
        # Use venv Python if available
        venv_python = Path(".venv/bin/python3")
        if venv_python.exists():
            python_exe = str(venv_python.absolute())
        else:
            python_exe = 'python3'
        
        # Service definitions
        self.service_configs = {
            'main_api': {
                'name': 'Main API (Port 8001)',
                'command': [python_exe, '-m', 'api.main'],
                'port': 8001,
                'cwd': '.',
                'health_url': 'http://localhost:8001/health',
                'startup_delay': 3
            },
            'recording_service': {
                'name': '24/7 Recording Service (Port 8002)',
                'command': [python_exe, 'bin/service-management/start_recording_service.py'],
                'port': 8002,
                'cwd': '.',
                'health_url': 'http://localhost:8002/health',
                'startup_delay': 5
            },
            'frontend': {
                'name': 'Frontend Server (Port 8080)',
                'command': [python_exe, '-m', 'http.server', '8080'],
                'port': 8080,
                'cwd': 'frontend',
                'health_url': 'http://localhost:8080/',
                'startup_delay': 2
            },
            'media_retention': {
                'name': 'Media Retention Service',
                'command': [python_exe, 'tools/maintenance/media_retention_service.py'],
                'port': None,  # No port - background service
                'cwd': '.',
                'health_url': None,  # No HTTP health check
                'startup_delay': 3,
                'optional': True  # Optional service - don't fail if it can't start
            }
        }
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, sig, frame):
        """Handle shutdown signals"""
        print(f"\n🛑 Received signal {sig}. Shutting down gracefully...")
        self.running = False
        self.stop_all_services()
        sys.exit(0)

    def check_port_available(self, port):
        """Check if a port is available"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                return result != 0
        except Exception:
            return False

    def create_log_file(self, service_name):
        """Create log file for service using log manager if available"""
        if self.use_log_manager:
            # New log manager handles rotation automatically
            from utils.log_manager import log_manager
            log_file = log_manager.log_dir / f"{service_name}.log"
            return str(log_file)
        else:
            # Fallback to timestamped files
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = self.log_dir / f"{service_name}_{timestamp}.log"
            return str(log_file)

    def start_service(self, service_key, config):
        """Start a single service"""
        try:
            # Check if port is available (skip for services without ports)
            if config['port'] is not None:
                if not self.check_port_available(config['port']):
                    print(f"❌ Port {config['port']} is already in use for {config['name']}")
                    if not config.get('optional', False):
                        return False
                    else:
                        print(f"⚠️  Skipping optional service {config['name']}")
                        return True
            
            # Create log file
            log_file = self.create_log_file(service_key)
            
            # Start process
            with open(log_file, 'w') as log_handle:
                process = subprocess.Popen(
                    config['command'],
                    cwd=config['cwd'],
                    stdout=log_handle,
                    stderr=subprocess.STDOUT,
                    bufsize=1,
                    universal_newlines=True
                )
            
            self.services[service_key] = {
                'process': process,
                'config': config,
                'log_file': log_file,
                'start_time': time.time()
            }
            
            print(f"🚀 Starting {config['name']}...")
            print(f"   Log file: {log_file}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to start {config['name']}: {e}")
            return False

    def check_service_health(self, service_key):
        """Check if service is healthy"""
        service = self.services.get(service_key)
        if not service:
            return False
        
        process = service['process']
        config = service['config']
        
        # Check if process is still running
        if process.poll() is not None:
            return False
        
        # For services with health URLs, check HTTP response
        if config.get('health_url'):
            try:
                import urllib.request
                with urllib.request.urlopen(config['health_url'], timeout=5) as response:
                    return response.status == 200
            except Exception:
                # If health check fails, still consider running if process is alive
                uptime = time.time() - service['start_time']
                return uptime > config.get('startup_delay', 5)
        else:
            # For services without health URLs, just check if process is running and past startup delay
            uptime = time.time() - service['start_time']
            return uptime > config.get('startup_delay', 3)
        
        return True

    def wait_for_service_ready(self, service_key, timeout=30):
        """Wait for service to be ready"""
        service = self.services.get(service_key)
        if not service:
            return False
        
        config = service['config']
        startup_delay = config.get('startup_delay', 3)
        
        print(f"   Waiting {startup_delay}s for {config['name']} to initialize...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.check_service_health(service_key):
                elapsed = time.time() - service['start_time']
                print(f"   ✅ {config['name']} is ready! (took {elapsed:.1f}s)")
                return True
            time.sleep(1)
        
        print(f"   ⚠️  {config['name']} may not be fully ready yet")
        return False

    def start_all_services(self):
        """Start all services in order"""
        print("=" * 70)
        print("🚀 LICENSE PLATE RECOGNITION SYSTEM STARTUP")
        print("=" * 70)
        
        # Check Python environment
        venv_python = Path(".venv/bin/python3")
        if venv_python.exists():
            print(f"🐍 Python: {venv_python.absolute()} (venv)")
        else:
            print(f"🐍 Python: python3 (system)")
        print(f"📁 Working Directory: {os.getcwd()}")
        print()
        
        # Create necessary directories
        os.makedirs("recordings", exist_ok=True)
        os.makedirs("detections", exist_ok=True)
        os.makedirs("detections/frames", exist_ok=True)
        os.makedirs("detections/plates", exist_ok=True)
        os.makedirs("static", exist_ok=True)
        
        success_count = 0
        
        # Start services in order
        for service_key, config in self.service_configs.items():
            if self.start_service(service_key, config):
                if self.wait_for_service_ready(service_key):
                    success_count += 1
                else:
                    print(f"   ⚠️  {config['name']} started but may have issues")
                    success_count += 1
            else:
                print(f"   ❌ Failed to start {config['name']}")
            print()
        
        if success_count == len(self.service_configs):
            self.print_success_message()
            return True
        else:
            print(f"⚠️  Only {success_count}/{len(self.service_configs)} services started successfully")
            return False

    def print_success_message(self):
        """Print success message with URLs"""
        print("=" * 70)
        print("✅ ALL SERVICES STARTED SUCCESSFULLY!")
        print("=" * 70)
        print()
        print("🌐 ACCESS URLS:")
        print("   Frontend:        http://localhost:8080/")
        print("   Main API:        http://localhost:8001/docs")
        print("   Recording API:   http://localhost:8002/docs")
        print()
        print("📊 HEALTH CHECKS:")
        print("   Main API:        http://localhost:8001/health")
        print("   Recording API:   http://localhost:8002/health")
        print()
        print("📝 LOG FILES:")
        for service_key, service in self.services.items():
            print(f"   {service['config']['name']:20} {service['log_file']}")
        print()
        print("🛑 STOP SERVICES:")
        print("   Press Ctrl+C or run: python stop_all_services.py")
        print("=" * 70)

    def monitor_services(self):
        """Monitor services and restart if needed"""
        print("🔍 Monitoring services... (Press Ctrl+C to stop)")
        
        while self.running:
            try:
                for service_key, service in list(self.services.items()):
                    if not self.check_service_health(service_key):
                        config = service['config']
                        print(f"⚠️  {config['name']} appears to be down. Checking...")
                        
                        # Give it a moment and check again
                        time.sleep(2)
                        if not self.check_service_health(service_key):
                            print(f"❌ {config['name']} is not responding")
                            # Could implement restart logic here if needed
                
                time.sleep(10)  # Check every 10 seconds
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Monitor error: {e}")
                time.sleep(5)

    def stop_all_services(self):
        """Stop all services gracefully"""
        print("\n🛑 Stopping all services...")
        
        for service_key, service in self.services.items():
            try:
                process = service['process']
                config = service['config']
                
                print(f"   Stopping {config['name']}...")
                
                # Try graceful shutdown first
                process.terminate()
                
                # Wait up to 10 seconds for graceful shutdown
                try:
                    process.wait(timeout=10)
                    print(f"   ✅ {config['name']} stopped gracefully")
                except subprocess.TimeoutExpired:
                    # Force kill if graceful shutdown fails
                    print(f"   🔨 Force killing {config['name']}...")
                    process.kill()
                    process.wait()
                    print(f"   ✅ {config['name']} force stopped")
                    
            except Exception as e:
                print(f"   ❌ Error stopping {config['name']}: {e}")
        
        print("✅ All services stopped")

    def get_service_status(self):
        """Get status of all services"""
        status = {}
        for service_key, service in self.services.items():
            config = service['config']
            is_healthy = self.check_service_health(service_key)
            uptime = time.time() - service['start_time']
            
            status[service_key] = {
                'name': config['name'],
                'port': config['port'],
                'healthy': is_healthy,
                'uptime': uptime,
                'log_file': service['log_file']
            }
        
        return status

def main():
    """Main entry point"""
    try:
        # Create service manager
        manager = ServiceManager()
        
        # Start all services
        if not manager.start_all_services():
            print("❌ Some services failed to start. Check logs for details.")
            return 1
        
        # Start monitoring in background thread
        monitor_thread = threading.Thread(target=manager.monitor_services, daemon=True)
        monitor_thread.start()
        
        # Keep main thread alive
        try:
            while manager.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        
        return 0
        
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        return 1
    finally:
        # Ensure cleanup
        if 'manager' in locals():
            manager.stop_all_services()

if __name__ == "__main__":
    sys.exit(main())