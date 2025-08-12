#!/usr/bin/env python3
"""
Enhanced Camera Connection Diagnostics Tool
Provides comprehensive testing and troubleshooting for IP camera connections
"""
import asyncio
import socket
import subprocess
import cv2
import os
import sys
import time
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import urllib.parse
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CameraDiagnostics:
    """Comprehensive camera connection diagnostics"""
    
    # Common RTSP paths by manufacturer
    RTSP_PATHS = {
        'reolink': [
            '/h264Preview_01_main',
            '/Preview_01_main', 
            '/h264Preview_01_sub',
            '/Preview_01_sub',
            '/live/main',
            '/live/sub'
        ],
        'hikvision': [
            '/Streaming/Channels/101',
            '/Streaming/Channels/1',
            '/h264/ch1/main/av_stream',
            '/h264/ch1/sub/av_stream',
            '/ISAPI/Streaming/channels/101'
        ],
        'dahua': [
            '/cam/realmonitor?channel=1&subtype=0',
            '/cam/realmonitor?channel=1&subtype=1',
            '/live',
            '/video1',
            '/video2'
        ],
        'generic': [
            '/stream',
            '/live',
            '/video',
            '/rtsp',
            '/cam1',
            '/channel1',
            '/1',
            '/'
        ]
    }
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'recommendations': []
        }
    
    def run_diagnostic(self, ip: str, port: int = 554, username: str = None, 
                      password: str = None, brand: str = 'generic',
                      connection_type: str = 'rtsp') -> Dict:
        """Run complete diagnostic suite"""
        print(f"\n{'='*60}")
        print(f"Camera Connection Diagnostics")
        print(f"{'='*60}")
        print(f"Target: {ip}:{port}")
        print(f"Brand: {brand}")
        print(f"Type: {connection_type.upper()}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        # 1. Network connectivity test
        self._test_network_connectivity(ip, port)
        
        # 2. Port scan for common camera ports
        self._scan_common_ports(ip)
        
        # 3. RTSP path discovery
        if connection_type.lower() == 'rtsp':
            working_paths = self._test_rtsp_paths(ip, port, username, password, brand)
        
        # 4. Network quality test
        self._test_network_quality(ip)
        
        # 5. Generate recommendations
        self._generate_recommendations()
        
        return self.results
    
    def _test_network_connectivity(self, ip: str, port: int) -> bool:
        """Test basic network connectivity"""
        print("1. Testing Network Connectivity...")
        print("-" * 40)
        
        # Ping test
        ping_result = self._ping_test(ip)
        
        # Socket connection test
        socket_result = self._socket_test(ip, port)
        
        self.results['tests']['network'] = {
            'ping': ping_result,
            'socket': socket_result
        }
        
        return ping_result['success'] and socket_result['success']
    
    def _ping_test(self, ip: str) -> Dict:
        """Test ICMP ping connectivity"""
        try:
            # Platform-specific ping command
            param = '-n' if sys.platform.lower() == 'win32' else '-c'
            command = ['ping', param, '4', ip]
            
            result = subprocess.run(command, capture_output=True, text=True, timeout=10)
            success = result.returncode == 0
            
            if success:
                # Parse ping statistics
                output = result.stdout
                if 'min/avg/max' in output:  # Linux/Mac
                    latency_line = [l for l in output.split('\n') if 'min/avg/max' in l][0]
                    avg_latency = float(latency_line.split('=')[1].split('/')[1])
                else:  # Windows
                    avg_latency = 0
                    for line in output.split('\n'):
                        if 'Average' in line:
                            avg_latency = float(line.split('=')[-1].replace('ms', '').strip())
                
                print(f"✅ Ping successful (avg: {avg_latency:.1f}ms)")
                return {
                    'success': True,
                    'latency_ms': avg_latency,
                    'message': f"Host is reachable with {avg_latency:.1f}ms latency"
                }
            else:
                print(f"❌ Ping failed - host may be blocking ICMP")
                return {
                    'success': False,
                    'message': "Ping failed - host unreachable or blocking ICMP"
                }
                
        except subprocess.TimeoutExpired:
            print(f"❌ Ping timeout")
            return {
                'success': False,
                'message': "Ping timeout - host not responding"
            }
        except Exception as e:
            print(f"❌ Ping error: {e}")
            return {
                'success': False,
                'message': f"Ping error: {str(e)}"
            }
    
    def _socket_test(self, ip: str, port: int) -> Dict:
        """Test TCP socket connectivity"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            
            start_time = time.time()
            result = sock.connect_ex((ip, port))
            connect_time = (time.time() - start_time) * 1000  # ms
            
            sock.close()
            
            if result == 0:
                print(f"✅ Port {port} is open (connected in {connect_time:.1f}ms)")
                return {
                    'success': True,
                    'port': port,
                    'connect_time_ms': connect_time,
                    'message': f"Port {port} is open and accepting connections"
                }
            else:
                print(f"❌ Port {port} is closed or filtered")
                return {
                    'success': False,
                    'port': port,
                    'message': f"Port {port} is closed or filtered"
                }
                
        except socket.timeout:
            print(f"❌ Socket timeout on port {port}")
            return {
                'success': False,
                'port': port,
                'message': "Connection timeout - port may be filtered by firewall"
            }
        except Exception as e:
            print(f"❌ Socket error: {e}")
            return {
                'success': False,
                'port': port,
                'message': f"Socket error: {str(e)}"
            }
    
    def _scan_common_ports(self, ip: str) -> Dict:
        """Scan common camera ports"""
        print("\n2. Scanning Common Camera Ports...")
        print("-" * 40)
        
        common_ports = {
            80: "HTTP",
            443: "HTTPS", 
            554: "RTSP",
            8080: "HTTP-Alt",
            8554: "RTSP-Alt",
            10554: "RTSP-Alt2",
            88: "Kerberos",
            8000: "HTTP-Alt2",
            9000: "HTTP-Alt3"
        }
        
        open_ports = {}
        for port, service in common_ports.items():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((ip, port))
            sock.close()
            
            if result == 0:
                print(f"✅ Port {port:5} ({service:10}) - OPEN")
                open_ports[port] = service
            else:
                print(f"   Port {port:5} ({service:10}) - closed")
        
        self.results['tests']['port_scan'] = {
            'open_ports': open_ports,
            'scanned_ports': list(common_ports.keys())
        }
        
        return open_ports
    
    def _test_rtsp_paths(self, ip: str, port: int, username: str, 
                        password: str, brand: str) -> List[Dict]:
        """Test various RTSP paths"""
        print("\n3. Testing RTSP Stream Paths...")
        print("-" * 40)
        
        # Get paths to test
        paths = self.RTSP_PATHS.get(brand.lower(), [])
        if brand.lower() != 'generic':
            paths.extend(self.RTSP_PATHS['generic'])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_paths = []
        for path in paths:
            if path not in seen:
                seen.add(path)
                unique_paths.append(path)
        
        working_paths = []
        failed_paths = []
        
        for path in unique_paths:
            print(f"\nTesting path: {path}")
            result = self._test_single_rtsp_path(ip, port, username, password, path)
            
            if result['success']:
                working_paths.append(result)
                print(f"✅ SUCCESS - {result['resolution']} @ {result['fps']:.1f} fps")
                # Don't break - test all paths to find alternatives
            else:
                failed_paths.append(result)
                print(f"❌ FAILED - {result['error']}")
        
        self.results['tests']['rtsp_paths'] = {
            'working_paths': working_paths,
            'failed_paths': failed_paths,
            'total_tested': len(unique_paths)
        }
        
        if working_paths:
            print(f"\n✅ Found {len(working_paths)} working RTSP path(s)")
        else:
            print("\n❌ No working RTSP paths found")
        
        return working_paths
    
    def _test_single_rtsp_path(self, ip: str, port: int, username: str, 
                               password: str, path: str) -> Dict:
        """Test a single RTSP path"""
        # Build URL
        if username and password:
            auth = f"{username}:{password}@"
        else:
            auth = ""
        
        url = f"rtsp://{auth}{ip}:{port}{path}"
        
        # Mask password in logs
        display_url = url.replace(password, "****") if password else url
        
        try:
            # Set OpenCV options for testing
            os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;tcp|timeout;5000000'
            
            cap = cv2.VideoCapture(url)
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
            cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)
            
            if not cap.isOpened():
                return {
                    'success': False,
                    'path': path,
                    'url': display_url,
                    'error': 'Failed to open stream'
                }
            
            # Try to read a frame
            ret, frame = cap.read()
            if not ret or frame is None:
                cap.release()
                return {
                    'success': False,
                    'path': path,
                    'url': display_url,
                    'error': 'Failed to read frame'
                }
            
            # Get stream properties
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            cap.release()
            
            return {
                'success': True,
                'path': path,
                'url': display_url,
                'resolution': f"{width}x{height}",
                'fps': fps if fps > 0 else 25.0,
                'frame_size': frame.shape
            }
            
        except Exception as e:
            return {
                'success': False,
                'path': path,
                'url': display_url,
                'error': str(e)
            }
        finally:
            if 'OPENCV_FFMPEG_CAPTURE_OPTIONS' in os.environ:
                del os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS']
    
    def _test_network_quality(self, ip: str) -> Dict:
        """Test network quality metrics"""
        print("\n4. Testing Network Quality...")
        print("-" * 40)
        
        try:
            # Extended ping test for packet loss
            param = '-n' if sys.platform.lower() == 'win32' else '-c'
            command = ['ping', param, '20', ip]
            
            result = subprocess.run(command, capture_output=True, text=True, timeout=25)
            output = result.stdout
            
            # Parse packet loss
            packet_loss = 0
            if '% loss' in output:
                for line in output.split('\n'):
                    if '% loss' in line or '% packet loss' in line:
                        packet_loss = float(line.split('%')[0].split()[-1])
            
            # Parse jitter (variation in latency)
            latencies = []
            for line in output.split('\n'):
                if 'time=' in line:
                    try:
                        time_str = line.split('time=')[1].split()[0]
                        latency = float(time_str.replace('ms', ''))
                        latencies.append(latency)
                    except:
                        pass
            
            if latencies:
                avg_latency = sum(latencies) / len(latencies)
                max_latency = max(latencies)
                min_latency = min(latencies)
                jitter = max_latency - min_latency
                
                print(f"✅ Packet Loss: {packet_loss}%")
                print(f"✅ Latency: min={min_latency:.1f}ms, avg={avg_latency:.1f}ms, max={max_latency:.1f}ms")
                print(f"✅ Jitter: {jitter:.1f}ms")
                
                quality_score = 100 - packet_loss - (jitter / 10)
                quality_rating = "Excellent" if quality_score > 90 else "Good" if quality_score > 70 else "Fair" if quality_score > 50 else "Poor"
                
                print(f"✅ Network Quality: {quality_rating} (score: {quality_score:.1f})")
                
                self.results['tests']['network_quality'] = {
                    'packet_loss_percent': packet_loss,
                    'latency_ms': {
                        'min': min_latency,
                        'avg': avg_latency,
                        'max': max_latency
                    },
                    'jitter_ms': jitter,
                    'quality_score': quality_score,
                    'quality_rating': quality_rating
                }
            else:
                print("❌ Could not measure network quality")
                self.results['tests']['network_quality'] = {
                    'error': 'Could not measure network quality'
                }
                
        except Exception as e:
            print(f"❌ Network quality test error: {e}")
            self.results['tests']['network_quality'] = {
                'error': str(e)
            }
    
    def _generate_recommendations(self):
        """Generate specific recommendations based on test results"""
        print("\n5. Generating Recommendations...")
        print("-" * 40)
        
        recommendations = []
        
        # Check network connectivity
        if 'network' in self.results['tests']:
            net_test = self.results['tests']['network']
            if not net_test['ping']['success']:
                recommendations.append({
                    'priority': 'HIGH',
                    'issue': 'Camera not responding to ping',
                    'fix': 'Check if camera is powered on and connected to network. Some cameras disable ICMP - this may be normal.'
                })
            
            if not net_test['socket']['success']:
                recommendations.append({
                    'priority': 'CRITICAL',
                    'issue': f"Cannot connect to RTSP port",
                    'fix': 'Verify camera IP address, check firewall rules, ensure RTSP is enabled on camera'
                })
        
        # Check open ports
        if 'port_scan' in self.results['tests']:
            open_ports = self.results['tests']['port_scan']['open_ports']
            if 554 not in open_ports and 'rtsp' in str(self.results).lower():
                if open_ports:
                    recommendations.append({
                        'priority': 'HIGH',
                        'issue': 'Standard RTSP port 554 is closed',
                        'fix': f"Try using alternative ports: {', '.join(map(str, open_ports.keys()))}"
                    })
                else:
                    recommendations.append({
                        'priority': 'CRITICAL',
                        'issue': 'No common camera ports are open',
                        'fix': 'Camera may be offline or behind a firewall. Check physical connection and network settings.'
                    })
        
        # Check RTSP paths
        if 'rtsp_paths' in self.results['tests']:
            rtsp_test = self.results['tests']['rtsp_paths']
            if not rtsp_test['working_paths']:
                recommendations.append({
                    'priority': 'HIGH',
                    'issue': 'No working RTSP paths found',
                    'fix': 'Check camera documentation for correct RTSP path, verify credentials, ensure RTSP is enabled in camera settings'
                })
            elif len(rtsp_test['working_paths']) > 1:
                best_path = rtsp_test['working_paths'][0]
                recommendations.append({
                    'priority': 'INFO',
                    'issue': 'Multiple RTSP paths available',
                    'fix': f"Recommended path: {best_path['path']} ({best_path['resolution']})"
                })
        
        # Check network quality
        if 'network_quality' in self.results['tests']:
            quality = self.results['tests']['network_quality']
            if 'packet_loss_percent' in quality:
                if quality['packet_loss_percent'] > 5:
                    recommendations.append({
                        'priority': 'HIGH',
                        'issue': f"High packet loss: {quality['packet_loss_percent']}%",
                        'fix': 'Check network cables, switch/router health, WiFi signal strength'
                    })
                
                if quality.get('jitter_ms', 0) > 50:
                    recommendations.append({
                        'priority': 'MEDIUM',
                        'issue': f"High network jitter: {quality['jitter_ms']:.1f}ms",
                        'fix': 'Network congestion detected. Consider QoS settings or dedicated VLAN for cameras'
                    })
        
        self.results['recommendations'] = recommendations
        
        # Print recommendations
        if recommendations:
            for rec in sorted(recommendations, key=lambda x: ['INFO', 'MEDIUM', 'HIGH', 'CRITICAL'].index(x['priority'])):
                icon = "🔴" if rec['priority'] == 'CRITICAL' else "🟡" if rec['priority'] == 'HIGH' else "🟢"
                print(f"\n{icon} {rec['priority']}: {rec['issue']}")
                print(f"   Fix: {rec['fix']}")
        else:
            print("\n✅ No issues found - camera connection appears healthy")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Camera Connection Diagnostics')
    parser.add_argument('ip', help='Camera IP address')
    parser.add_argument('-p', '--port', type=int, default=554, help='RTSP port (default: 554)')
    parser.add_argument('-u', '--username', help='Camera username')
    parser.add_argument('-P', '--password', help='Camera password')
    parser.add_argument('-b', '--brand', default='generic', 
                      choices=['reolink', 'hikvision', 'dahua', 'generic'],
                      help='Camera brand for optimized testing')
    parser.add_argument('-t', '--type', default='rtsp',
                      choices=['rtsp', 'http', 'https'],
                      help='Connection type (default: rtsp)')
    parser.add_argument('-o', '--output', help='Save results to JSON file')
    
    args = parser.parse_args()
    
    # Run diagnostics
    diag = CameraDiagnostics()
    results = diag.run_diagnostic(
        ip=args.ip,
        port=args.port,
        username=args.username,
        password=args.password,
        brand=args.brand,
        connection_type=args.type
    )
    
    # Save results if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results saved to: {args.output}")
    
    # Summary
    print(f"\n{'='*60}")
    print("Diagnostic Summary")
    print(f"{'='*60}")
    
    # Count successes and failures
    successes = 0
    failures = 0
    
    for test_name, test_result in results['tests'].items():
        if isinstance(test_result, dict):
            if test_result.get('success'):
                successes += 1
            elif 'error' in test_result or test_result.get('success') == False:
                failures += 1
    
    print(f"✅ Successful tests: {successes}")
    print(f"❌ Failed tests: {failures}")
    print(f"📋 Recommendations: {len(results['recommendations'])}")
    
    if 'rtsp_paths' in results['tests']:
        working = len(results['tests']['rtsp_paths']['working_paths'])
        if working > 0:
            print(f"\n✅ Found {working} working RTSP path(s)")
            for path in results['tests']['rtsp_paths']['working_paths']:
                print(f"   - {path['path']} ({path['resolution']})")

if __name__ == "__main__":
    main()