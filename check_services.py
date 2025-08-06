#!/usr/bin/env python3
"""
Service Status Checker
Check the health and status of all LPR system services
"""
import sys
import time
import urllib.request
import urllib.error
import json
from datetime import datetime

class ServiceChecker:
    def __init__(self):
        self.services = {
            'main_api': {
                'name': 'Main API',
                'url': 'http://localhost:8001/health',
                'port': 8001,
                'expected_keys': ['status', 'timestamp', 'cameras']
            },
            'recording_service': {
                'name': '24/7 Recording Service',
                'url': 'http://localhost:8002/health',
                'port': 8002,
                'expected_keys': ['status', 'active_cameras']
            },
            'frontend': {
                'name': 'Frontend Server',
                'url': 'http://localhost:8080/',
                'port': 8080,
                'expected_keys': None  # HTML response
            }
        }

    def check_service(self, service_key, service_config):
        """Check individual service health"""
        try:
            req = urllib.request.Request(service_config['url'])
            req.add_header('User-Agent', 'LPR-HealthCheck/1.0')
            
            start_time = time.time()
            with urllib.request.urlopen(req, timeout=10) as response:
                response_time = (time.time() - start_time) * 1000
                
                if service_key == 'frontend':
                    # For frontend, just check if we get HTML
                    content = response.read().decode('utf-8')
                    is_html = '<html' in content.lower() or '<!doctype' in content.lower()
                    
                    return {
                        'status': 'healthy' if is_html else 'unhealthy',
                        'response_time': response_time,
                        'http_status': response.status,
                        'content_type': response.headers.get('Content-Type', 'unknown'),
                        'details': 'Serving HTML content' if is_html else 'Not serving HTML'
                    }
                else:
                    # For APIs, parse JSON response
                    content = response.read().decode('utf-8')
                    data = json.loads(content)
                    
                    # Check if expected keys are present
                    missing_keys = []
                    if service_config['expected_keys']:
                        for key in service_config['expected_keys']:
                            if key not in data:
                                missing_keys.append(key)
                    
                    status = 'healthy'
                    if response.status != 200:
                        status = 'unhealthy'
                    elif missing_keys:
                        status = 'partial'
                    elif data.get('status') != 'healthy':
                        status = 'unhealthy'
                    
                    return {
                        'status': status,
                        'response_time': response_time,
                        'http_status': response.status,
                        'data': data,
                        'missing_keys': missing_keys
                    }
                    
        except urllib.error.HTTPError as e:
            return {
                'status': 'error',
                'error': f'HTTP {e.code}: {e.reason}',
                'response_time': None
            }
        except urllib.error.URLError as e:
            return {
                'status': 'offline',
                'error': f'Connection failed: {e.reason}',
                'response_time': None
            }
        except json.JSONDecodeError as e:
            return {
                'status': 'error',
                'error': f'Invalid JSON response: {e}',
                'response_time': None
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Unexpected error: {e}',
                'response_time': None
            }

    def format_status(self, status):
        """Format status with emoji"""
        status_map = {
            'healthy': '✅ HEALTHY',
            'partial': '⚠️  PARTIAL',
            'unhealthy': '❌ UNHEALTHY',
            'offline': '🔴 OFFLINE',
            'error': '❌ ERROR'
        }
        return status_map.get(status, f'❓ {status.upper()}')

    def format_response_time(self, response_time):
        """Format response time"""
        if response_time is None:
            return 'N/A'
        elif response_time < 100:
            return f'{response_time:.0f}ms ✅'
        elif response_time < 500:
            return f'{response_time:.0f}ms ⚠️'
        else:
            return f'{response_time:.0f}ms ❌'
    
    def check_recording_details(self):
        """Check detailed recording service status"""
        try:
            req = urllib.request.Request('http://localhost:8002/health/detailed')
            req.add_header('User-Agent', 'LPR-HealthCheck/1.0')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                print("\n📹 RECORDING SERVICE DETAILED STATUS")
                print("   " + "-" * 50)
                
                # Overall status
                status = data.get('status', 'unknown')
                print(f"   Service Status: {self.format_status('healthy' if status == 'healthy' else 'unhealthy')}")
                
                # Recording status
                rec_status = data.get('recording_status', {})
                active = rec_status.get('active_recordings', 0)
                total = rec_status.get('total_cameras', 0)
                print(f"   Active Recordings: {active}/{total} cameras")
                
                # Shutdown status
                shutdown = data.get('shutdown_status', {})
                if shutdown.get('is_shutting_down'):
                    print(f"   ⚠️  SHUTDOWN IN PROGRESS")
                    print(f"       Requested at: {shutdown.get('shutdown_requested_at')}")
                    print(f"       Cameras stopped: {shutdown.get('cameras_stopped', 0)}/{total}")
                
                # System stats
                stats = data.get('system_stats', {})
                uptime = stats.get('uptime_seconds', 0)
                uptime_str = f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m {int(uptime % 60)}s"
                print(f"   Uptime: {uptime_str}")
                print(f"   Total Segments: {stats.get('total_segments', 0)}")
                print(f"   Total Size: {stats.get('total_size_mb', 0):.1f} MB")
                print(f"   Total Errors: {stats.get('total_errors', 0)}")
                
                # Camera details
                cameras = rec_status.get('cameras', {})
                if cameras:
                    print("\n   📷 CAMERA RECORDING STATUS:")
                    for cam_id, cam_status in cameras.items():
                        rec_icon = "🔴" if cam_status.get('is_recording') else "⚫"
                        conn_status = cam_status.get('connection_status', 'unknown')
                        error_count = cam_status.get('error_count', 0)
                        error_str = f" (⚠️  {error_count} errors)" if error_count > 0 else ""
                        
                        print(f"       {rec_icon} {cam_status.get('name', cam_id)}: {conn_status}{error_str}")
                        if cam_status.get('ffmpeg_pid'):
                            print(f"          FFmpeg PID: {cam_status.get('ffmpeg_pid')}")
                        if cam_status.get('last_segment_time'):
                            print(f"          Last segment: {cam_status.get('last_segment_time')}")
                
                return True
                
        except urllib.error.URLError as e:
            print("\n📹 RECORDING SERVICE DETAILED STATUS")
            print("   ❌ Could not connect to recording service for detailed status")
            return False
        except Exception as e:
            print(f"\n   ❌ Error checking recording details: {e}")
            return False

    def check_all_services(self):
        """Check all services and return results"""
        print("=" * 70)
        print(f"🔍 LPR SYSTEM HEALTH CHECK - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        results = {}
        all_healthy = True
        
        for service_key, service_config in self.services.items():
            print(f"\n🔍 Checking {service_config['name']} (Port {service_config['port']})...")
            result = self.check_service(service_key, service_config)
            results[service_key] = result
            
            # Print status
            print(f"   Status: {self.format_status(result['status'])}")
            print(f"   Response Time: {self.format_response_time(result.get('response_time'))}")
            
            if result['status'] in ['offline', 'error']:
                all_healthy = False
                print(f"   Error: {result.get('error', 'Unknown error')}")
            elif result['status'] == 'unhealthy':
                all_healthy = False
                if 'data' in result:
                    print(f"   Details: {result['data']}")
            elif result['status'] == 'partial':
                print(f"   Missing Keys: {', '.join(result.get('missing_keys', []))}")
            
            # Show additional details for healthy services
            if result['status'] == 'healthy' and 'data' in result:
                data = result['data']
                if service_key == 'main_api':
                    cameras = data.get('cameras', 0)
                    database = data.get('database', 'unknown')
                    print(f"   Cameras: {cameras}")
                    print(f"   Database: {database}")
                elif service_key == 'recording_service':
                    active_cameras = data.get('active_cameras', 0)
                    print(f"   Active Cameras: {active_cameras}")
                    # Show detailed recording status if available
                    self.check_recording_details()
        
        # Overall status
        print("\n" + "=" * 70)
        if all_healthy:
            print("✅ ALL SERVICES ARE HEALTHY")
        else:
            print("❌ SOME SERVICES HAVE ISSUES")
        print("=" * 70)
        
        return results, all_healthy

    def continuous_monitoring(self, interval=30):
        """Continuously monitor services"""
        print(f"🔄 Starting continuous monitoring (checking every {interval} seconds)")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                results, all_healthy = self.check_all_services()
                
                if not all_healthy:
                    print(f"\n⚠️  Issues detected at {datetime.now().strftime('%H:%M:%S')}")
                
                print(f"\n⏰ Next check in {interval} seconds...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped")

def main():
    """Main function"""
    checker = ServiceChecker()
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--monitor' or sys.argv[1] == '-m':
            interval = 30
            if len(sys.argv) > 2:
                try:
                    interval = int(sys.argv[2])
                except ValueError:
                    print("Invalid interval. Using default 30 seconds.")
            checker.continuous_monitoring(interval)
        elif sys.argv[1] == '--help' or sys.argv[1] == '-h':
            print("Usage:")
            print("  python check_services.py           # Single health check")
            print("  python check_services.py -m [SEC]  # Continuous monitoring")
            print("  python check_services.py --help    # Show this help")
            return 0
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            return 1
    else:
        # Single check
        results, all_healthy = checker.check_all_services()
        return 0 if all_healthy else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n🛑 Operation cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)