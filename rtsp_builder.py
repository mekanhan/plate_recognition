#!/usr/bin/env python3
"""
RTSP URL Builder and Validator Utility
Interactive tool for building and testing RTSP URLs for IP cameras
"""
import sys
import urllib.parse
from typing import Dict, List, Optional, Tuple
import argparse

class RTSPURLBuilder:
    """Interactive RTSP URL builder with brand-specific templates"""
    
    # Brand-specific URL templates and common configurations
    BRAND_TEMPLATES = {
        'reolink': {
            'default_port': 554,
            'common_paths': [
                '/h264Preview_01_main',  # Main stream
                '/Preview_01_main',      # Alternative main
                '/h264Preview_01_sub',   # Sub stream (lower quality)
                '/Preview_01_sub',       # Alternative sub
                '/live/main',            # Generic live main
                '/live/sub'              # Generic live sub
            ],
            'url_format': 'rtsp://{auth}{ip}:{port}{path}',
            'notes': 'Reolink cameras typically use Preview or h264Preview paths'
        },
        'hikvision': {
            'default_port': 554,
            'common_paths': [
                '/Streaming/Channels/101',        # Channel 1 main stream
                '/Streaming/Channels/1',          # Alternative format
                '/h264/ch1/main/av_stream',       # H.264 main stream
                '/h264/ch1/sub/av_stream',        # H.264 sub stream
                '/ISAPI/Streaming/channels/101',  # ISAPI format
                '/ISAPI/Streaming/channels/102'   # ISAPI sub stream
            ],
            'url_format': 'rtsp://{auth}{ip}:{port}{path}',
            'notes': 'Hikvision uses channel-based paths. 101=main, 102=sub stream'
        },
        'dahua': {
            'default_port': 554,
            'common_paths': [
                '/cam/realmonitor?channel=1&subtype=0',  # Main stream
                '/cam/realmonitor?channel=1&subtype=1',  # Sub stream
                '/live',                                 # Generic live
                '/video1',                               # Video channel 1
                '/video2',                               # Video channel 2
                '/ch1/0',                               # Channel format
                '/ch1/1'                                # Channel sub format
            ],
            'url_format': 'rtsp://{auth}{ip}:{port}{path}',
            'notes': 'Dahua uses realmonitor with channel/subtype parameters'
        },
        'axis': {
            'default_port': 554,
            'common_paths': [
                '/axis-media/media.amp',                    # Main stream
                '/axis-media/media.amp?resolution=1920x1080', # Specific resolution
                '/axis-media/media.amp?videocodec=h264',    # H.264 codec
                '/onvif/media_service/profiles/profile_1_h264', # ONVIF
                '/mjpg/video.mjpg'                         # MJPEG stream
            ],
            'url_format': 'rtsp://{auth}{ip}:{port}{path}',
            'notes': 'Axis cameras support ONVIF and media.amp endpoints'
        },
        'foscam': {
            'default_port': 554,
            'common_paths': [
                '/videoMain',      # Main stream
                '/videoSub',       # Sub stream  
                '/video.pro1',     # Profile 1
                '/video.pro2',     # Profile 2
                '/11'              # Numeric channel
            ],
            'url_format': 'rtsp://{auth}{ip}:{port}{path}',
            'notes': 'Foscam uses videoMain/videoSub or profile-based paths'
        },
        'generic': {
            'default_port': 554,
            'common_paths': [
                '/stream',         # Most common
                '/live',           # Generic live
                '/video',          # Generic video
                '/rtsp',           # Self-describing
                '/cam1',           # Camera 1
                '/channel1',       # Channel 1
                '/1',              # Simple numeric
                '/',               # Root path
                '/stream1',        # Stream 1
                '/main'            # Main stream
            ],
            'url_format': 'rtsp://{auth}{ip}:{port}{path}',
            'notes': 'Common generic paths that work with many camera brands'
        }
    }
    
    def __init__(self):
        self.current_config = {
            'ip': '',
            'port': 554,
            'username': '',
            'password': '',
            'brand': 'generic',
            'path': '/stream'
        }
    
    def interactive_builder(self):
        """Interactive mode for building RTSP URLs"""
        print("🎥 RTSP URL Builder - Interactive Mode")
        print("=" * 50)
        
        # Get camera details
        self.current_config['ip'] = input("Camera IP address: ").strip()
        if not self.current_config['ip']:
            print("❌ IP address is required")
            return None
        
        # Brand selection
        print("\nAvailable camera brands:")
        brands = list(self.BRAND_TEMPLATES.keys())
        for i, brand in enumerate(brands, 1):
            print(f"  {i}. {brand.title()}")
        
        try:
            brand_choice = input(f"\nSelect brand (1-{len(brands)}) or press Enter for generic: ").strip()
            if brand_choice:
                brand_idx = int(brand_choice) - 1
                if 0 <= brand_idx < len(brands):
                    self.current_config['brand'] = brands[brand_idx]
                else:
                    print("Invalid choice, using generic")
            else:
                self.current_config['brand'] = 'generic'
        except ValueError:
            print("Invalid input, using generic")
            self.current_config['brand'] = 'generic'
        
        # Get brand template
        template = self.BRAND_TEMPLATES[self.current_config['brand']]
        
        # Port (with brand default)
        default_port = template['default_port']
        port_input = input(f"Port (default {default_port}): ").strip()
        if port_input:
            try:
                self.current_config['port'] = int(port_input)
            except ValueError:
                print(f"Invalid port, using default {default_port}")
                self.current_config['port'] = default_port
        else:
            self.current_config['port'] = default_port
        
        # Credentials
        self.current_config['username'] = input("Username (optional): ").strip()
        if self.current_config['username']:
            self.current_config['password'] = input("Password (optional): ").strip()
        
        # Show common paths for this brand
        print(f"\nCommon paths for {self.current_config['brand'].title()}:")
        print(f"Note: {template['notes']}")
        
        paths = template['common_paths']
        for i, path in enumerate(paths, 1):
            print(f"  {i}. {path}")
        
        # Path selection
        try:
            path_choice = input(f"\nSelect path (1-{len(paths)}) or enter custom: ").strip()
            if path_choice.isdigit():
                path_idx = int(path_choice) - 1
                if 0 <= path_idx < len(paths):
                    self.current_config['path'] = paths[path_idx]
                else:
                    print("Invalid choice, using first path")
                    self.current_config['path'] = paths[0]
            else:
                # Custom path
                if path_choice:
                    if not path_choice.startswith('/'):
                        path_choice = '/' + path_choice
                    self.current_config['path'] = path_choice
                else:
                    self.current_config['path'] = paths[0]
        except (ValueError, IndexError):
            print("Invalid input, using first path")
            self.current_config['path'] = paths[0]
        
        # Build and display URL
        url = self.build_url(self.current_config)
        display_url = self.build_url(self.current_config, mask_password=True)
        
        print(f"\n✅ Generated RTSP URL:")
        print(f"   {display_url}")
        
        # Test option
        test_choice = input("\nTest this URL? (y/N): ").strip().lower()
        if test_choice == 'y':
            print("\nTesting connection...")
            self.test_url(url)
        
        return url
    
    def build_url(self, config: Dict, mask_password: bool = False) -> str:
        """Build RTSP URL from configuration"""
        # Handle authentication
        auth = ""
        if config.get('username'):
            password = config.get('password', '')
            if mask_password and password:
                password = '****'
            if password:
                auth = f"{config['username']}:{password}@"
            else:
                auth = f"{config['username']}@"
        
        # Build URL
        url = f"rtsp://{auth}{config['ip']}:{config['port']}{config['path']}"
        return url
    
    def test_url(self, url: str) -> bool:
        """Test RTSP URL using OpenCV"""
        try:
            import cv2
            import os
            
            # Set timeout for testing
            os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;tcp|timeout;5000000'
            
            print("Attempting to connect...")
            cap = cv2.VideoCapture(url)
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
            cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)
            
            if not cap.isOpened():
                print("❌ Failed to open stream")
                return False
            
            print("✅ Stream opened successfully")
            
            # Try to read a frame
            ret, frame = cap.read()
            if ret and frame is not None:
                height, width = frame.shape[:2]
                print(f"✅ Frame received: {width}x{height}")
                
                # Try to get FPS
                fps = cap.get(cv2.CAP_PROP_FPS)
                if fps > 0:
                    print(f"✅ FPS: {fps}")
                
                cap.release()
                return True
            else:
                print("❌ Failed to read frame")
                cap.release()
                return False
                
        except ImportError:
            print("❌ OpenCV not available for testing")
            return False
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False
        finally:
            if 'OPENCV_FFMPEG_CAPTURE_OPTIONS' in os.environ:
                del os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS']
    
    def batch_test_paths(self, ip: str, port: int, username: str = None, 
                        password: str = None, brand: str = 'generic') -> List[Dict]:
        """Test multiple paths for a camera brand"""
        print(f"\n🔍 Testing all paths for {brand.title()} camera at {ip}:{port}")
        print("-" * 50)
        
        template = self.BRAND_TEMPLATES.get(brand, self.BRAND_TEMPLATES['generic'])
        paths = template['common_paths']
        
        results = []
        
        for i, path in enumerate(paths, 1):
            config = {
                'ip': ip,
                'port': port,
                'username': username,
                'password': password,
                'path': path
            }
            
            url = self.build_url(config)
            display_url = self.build_url(config, mask_password=True)
            
            print(f"\n{i:2d}. Testing: {path}")
            print(f"    URL: {display_url}")
            
            success = self.test_url(url)
            
            results.append({
                'path': path,
                'url': display_url,
                'success': success
            })
            
            if success:
                print("    ✅ SUCCESS")
            else:
                print("    ❌ FAILED")
        
        # Summary
        working_paths = [r for r in results if r['success']]
        print(f"\n📊 Results Summary:")
        print(f"   Total tested: {len(results)}")
        print(f"   Working paths: {len(working_paths)}")
        
        if working_paths:
            print(f"\n✅ Working paths:")
            for result in working_paths:
                print(f"   - {result['path']}")
        else:
            print(f"\n❌ No working paths found")
            print(f"   Try different brand, check credentials, or verify camera is online")
        
        return results
    
    def validate_credentials(self, ip: str, port: int, username: str, password: str) -> bool:
        """Validate credentials by testing with a simple path"""
        print(f"\n🔐 Validating credentials for {username}@{ip}:{port}")
        
        # Test with most common path
        config = {
            'ip': ip,
            'port': port,
            'username': username,
            'password': password,
            'path': '/stream'
        }
        
        return self.test_url(self.build_url(config))
    
    def encode_special_characters(self, text: str) -> str:
        """URL encode special characters in passwords/usernames"""
        return urllib.parse.quote(text, safe='')
    
    def show_brand_info(self, brand: str = None):
        """Show information about camera brands"""
        if brand:
            brands = [brand] if brand in self.BRAND_TEMPLATES else []
        else:
            brands = list(self.BRAND_TEMPLATES.keys())
        
        if not brands:
            print(f"❌ Unknown brand: {brand}")
            return
        
        print(f"\n📋 Camera Brand Information:")
        print("=" * 50)
        
        for brand_name in brands:
            template = self.BRAND_TEMPLATES[brand_name]
            print(f"\n🏷️  {brand_name.upper()}")
            print(f"   Default port: {template['default_port']}")
            print(f"   Notes: {template['notes']}")
            print(f"   Common paths:")
            for path in template['common_paths']:
                print(f"     - {path}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='RTSP URL Builder and Validator')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Interactive mode
    interactive_parser = subparsers.add_parser('interactive', help='Interactive URL builder')
    
    # Build mode
    build_parser = subparsers.add_parser('build', help='Build URL with parameters')
    build_parser.add_argument('ip', help='Camera IP address')
    build_parser.add_argument('-p', '--port', type=int, default=554, help='Port (default: 554)')
    build_parser.add_argument('-u', '--username', help='Username')
    build_parser.add_argument('-P', '--password', help='Password')
    build_parser.add_argument('-b', '--brand', default='generic', 
                            choices=list(RTSPURLBuilder.BRAND_TEMPLATES.keys()),
                            help='Camera brand')
    build_parser.add_argument('--path', help='Custom stream path')
    build_parser.add_argument('-t', '--test', action='store_true', help='Test the URL')
    
    # Test mode
    test_parser = subparsers.add_parser('test', help='Test all paths for a brand')
    test_parser.add_argument('ip', help='Camera IP address')
    test_parser.add_argument('-p', '--port', type=int, default=554, help='Port (default: 554)')
    test_parser.add_argument('-u', '--username', help='Username')
    test_parser.add_argument('-P', '--password', help='Password')
    test_parser.add_argument('-b', '--brand', default='generic',
                           choices=list(RTSPURLBuilder.BRAND_TEMPLATES.keys()),
                           help='Camera brand')
    
    # Info mode
    info_parser = subparsers.add_parser('info', help='Show brand information')
    info_parser.add_argument('-b', '--brand', help='Specific brand (optional)')
    
    args = parser.parse_args()
    
    builder = RTSPURLBuilder()
    
    if args.command == 'interactive' or not args.command:
        # Interactive mode
        builder.interactive_builder()
    
    elif args.command == 'build':
        # Build mode
        config = {
            'ip': args.ip,
            'port': args.port,
            'username': args.username,
            'password': args.password,
            'brand': args.brand,
            'path': args.path or RTSPURLBuilder.BRAND_TEMPLATES[args.brand]['common_paths'][0]
        }
        
        url = builder.build_url(config)
        display_url = builder.build_url(config, mask_password=True)
        
        print(f"Generated URL: {display_url}")
        
        if args.test:
            print("\nTesting URL...")
            success = builder.test_url(url)
            print(f"Test result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    
    elif args.command == 'test':
        # Test mode
        builder.batch_test_paths(args.ip, args.port, args.username, args.password, args.brand)
    
    elif args.command == 'info':
        # Info mode
        builder.show_brand_info(args.brand)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()