#!/usr/bin/env python3
"""
ONVIF Camera Discovery CLI Tool
Discovers ONVIF cameras on the network and optionally adds them to Vision Port
"""

import sys
import os
import asyncio
import json
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.onvif_discovery_service import ONVIFDiscoveryService
from database.service import DatabaseService
from utils.camera_utils import generate_camera_id

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ONVIFDiscoveryCLI:
    """Command-line interface for ONVIF camera discovery"""
    
    def __init__(self):
        self.discovery = ONVIFDiscoveryService()
        self.db = DatabaseService()
        self.discovered_cameras = []
        
    async def run(self):
        """Main CLI execution"""
        print("\n" + "="*60)
        print("🔍 Vision Port ONVIF Camera Discovery Tool")
        print("="*60)
        
        # Initialize database
        await self.db.init_db()
        
        # Choose discovery method
        method = self.choose_discovery_method()
        
        # Get subnets if needed
        subnets = None
        if method in ['unicast', 'both']:
            subnets = self.get_subnets()
        
        # Perform discovery
        print(f"\n🔄 Starting {method} discovery...")
        print("This may take up to 30 seconds...\n")
        
        cameras = self.discovery.discover(method=method, subnets=subnets)
        
        if not cameras:
            print("❌ No ONVIF cameras found on the network")
            print("\nPossible reasons:")
            print("  • Cameras are not ONVIF compliant")
            print("  • Cameras are on a different network segment")
            print("  • Firewall is blocking UDP port 3702")
            print("  • ONVIF is disabled on the cameras")
            return
        
        # Filter out existing cameras
        existing_cameras = await self.get_existing_cameras()
        new_cameras = [cam for cam in cameras if cam.ip not in existing_cameras]
        
        print(f"\n✅ Discovery complete!")
        print(f"   Total found: {len(cameras)}")
        print(f"   Already in system: {len(cameras) - len(new_cameras)}")
        print(f"   New cameras: {len(new_cameras)}")
        
        if not new_cameras:
            print("\n📌 All discovered cameras are already in the system")
            self.display_cameras(cameras, show_existing=True)
            return
        
        self.discovered_cameras = new_cameras
        
        # Display discovered cameras
        self.display_cameras(new_cameras)
        
        # Offer to add cameras
        await self.handle_camera_addition()
    
    def choose_discovery_method(self):
        """Let user choose discovery method"""
        print("\n📡 Select discovery method:")
        print("1. Both (Recommended) - Multicast + Network Scan")
        print("2. Multicast Only - Fast but may miss some cameras")
        print("3. Network Scan - Thorough but slower")
        
        while True:
            choice = input("\nEnter choice (1-3) [1]: ").strip() or "1"
            if choice == "1":
                return "both"
            elif choice == "2":
                return "multicast"
            elif choice == "3":
                return "unicast"
            else:
                print("❌ Invalid choice. Please enter 1, 2, or 3.")
    
    def get_subnets(self):
        """Get subnet(s) to scan"""
        print("\n🌐 Network Configuration:")
        
        # Get local subnet
        local_subnet = self.discovery.get_local_subnet()
        print(f"   Detected local subnet: {local_subnet}")
        
        custom = input("\nEnter custom subnet (or press Enter to use local): ").strip()
        
        if custom:
            # Validate subnet format
            try:
                import ipaddress
                ipaddress.ip_network(custom)
                return [custom]
            except ValueError:
                print(f"⚠️  Invalid subnet format. Using local subnet: {local_subnet}")
                return [local_subnet]
        else:
            return [local_subnet]
    
    def display_cameras(self, cameras, show_existing=False):
        """Display discovered cameras"""
        print("\n📹 Discovered Cameras:")
        print("-" * 60)
        
        for i, camera in enumerate(cameras, 1):
            brand = self.discovery.detect_brand(camera)
            config = self.discovery.get_camera_config(camera)
            
            status = " [Already in system]" if show_existing else ""
            
            print(f"\n{i}. {config['name']}{status}")
            print(f"   IP Address:    {camera.ip}")
            print(f"   Manufacturer:  {camera.manufacturer or 'Unknown'}")
            print(f"   Model:         {camera.model or 'Unknown'}")
            print(f"   Brand:         {brand.upper()}")
            print(f"   ONVIF Port:    {config['onvif_port']}")
            print(f"   RTSP Port:     {config['port']}")
            print(f"   Stream Path:   {config['stream_path']}")
            print(f"   Default User:  {config['username']}")
    
    async def get_existing_cameras(self):
        """Get list of existing camera IPs"""
        try:
            cameras = await self.db.get_all_cameras()
            return {cam.ip_address for cam in cameras}
        except Exception as e:
            logger.error(f"Error getting existing cameras: {e}")
            return set()
    
    async def handle_camera_addition(self):
        """Handle adding discovered cameras to the system"""
        print("\n" + "-"*60)
        print("🔧 What would you like to do?")
        print("1. Add all cameras")
        print("2. Add selected cameras")
        print("3. Export to JSON file")
        print("4. Exit without adding")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            await self.add_all_cameras()
        elif choice == "2":
            await self.add_selected_cameras()
        elif choice == "3":
            self.export_to_json()
        else:
            print("\n👋 Exiting without changes")
    
    async def add_all_cameras(self):
        """Add all discovered cameras"""
        print("\n🔐 Camera credentials required")
        print("Enter credentials for all cameras (or different for each):")
        
        use_same = input("Use same credentials for all? (y/n) [y]: ").strip().lower() or "y"
        
        if use_same == "y":
            username = input("Username [admin]: ").strip() or "admin"
            password = input("Password: ").strip()
            
            credentials = {cam.ip: {"username": username, "password": password} 
                          for cam in self.discovered_cameras}
        else:
            credentials = {}
            for cam in self.discovered_cameras:
                config = self.discovery.get_camera_config(cam)
                print(f"\n{config['name']} ({cam.ip}):")
                username = input(f"  Username [{config['username']}]: ").strip() or config['username']
                password = input("  Password: ").strip()
                credentials[cam.ip] = {"username": username, "password": password}
        
        # Add cameras
        await self.add_cameras_to_system(self.discovered_cameras, credentials)
    
    async def add_selected_cameras(self):
        """Add selected cameras"""
        print("\n📋 Select cameras to add (comma-separated numbers):")
        
        for i, cam in enumerate(self.discovered_cameras, 1):
            config = self.discovery.get_camera_config(cam)
            print(f"{i}. {config['name']} ({cam.ip})")
        
        selection = input("\nEnter camera numbers: ").strip()
        
        try:
            indices = [int(x.strip()) - 1 for x in selection.split(',')]
            selected = [self.discovered_cameras[i] for i in indices 
                       if 0 <= i < len(self.discovered_cameras)]
            
            if not selected:
                print("❌ No valid cameras selected")
                return
            
            # Get credentials for selected cameras
            print("\n🔐 Enter credentials for selected cameras:")
            credentials = {}
            for cam in selected:
                config = self.discovery.get_camera_config(cam)
                print(f"\n{config['name']} ({cam.ip}):")
                username = input(f"  Username [{config['username']}]: ").strip() or config['username']
                password = input("  Password: ").strip()
                credentials[cam.ip] = {"username": username, "password": password}
            
            # Add cameras
            await self.add_cameras_to_system(selected, credentials)
            
        except (ValueError, IndexError) as e:
            print(f"❌ Invalid selection: {e}")
    
    async def add_cameras_to_system(self, cameras, credentials):
        """Add cameras to the Vision Port system"""
        print(f"\n🔄 Adding {len(cameras)} camera(s) to system...")
        
        success_count = 0
        failed = []
        
        for camera in cameras:
            config = self.discovery.get_camera_config(camera)
            creds = credentials.get(camera.ip, {})
            
            # Update config with credentials
            config['username'] = creds.get('username', config['username'])
            config['password'] = creds.get('password', '')
            
            try:
                # Create camera in database
                camera_dict = {
                    'camera_id': config['camera_id'],
                    'name': config['name'],
                    'ip_address': config['ip_address'],
                    'port': config['port'],
                    'connection_type': config['connection_type'],
                    'stream_path': config['stream_path'],
                    'username': config['username'],
                    'password': config['password'],
                    'brand': config.get('manufacturer'),
                    'model': config.get('model'),
                    'onvif_service_url': config.get('onvif_service_url'),
                    'onvif_port': config.get('onvif_port'),
                    'manufacturer': config.get('manufacturer'),
                    'discovered_via': 'onvif',
                    'hardware_id': config.get('hardware_id'),
                    'onvif_scopes': json.dumps(config.get('onvif_scopes', []))
                }
                
                await self.db.add_camera(camera_dict)
                print(f"  ✅ Added: {config['name']}")
                success_count += 1
                
            except Exception as e:
                print(f"  ❌ Failed to add {config['name']}: {e}")
                failed.append(config['name'])
        
        print(f"\n📊 Results:")
        print(f"   Successfully added: {success_count}")
        print(f"   Failed: {len(failed)}")
        
        if failed:
            print(f"\n❌ Failed cameras:")
            for name in failed:
                print(f"   • {name}")
        
        if success_count > 0:
            print(f"\n✅ {success_count} camera(s) added successfully!")
            print("\n📋 Next steps:")
            print("1. Test camera connections in the web interface")
            print("2. Adjust stream settings if needed")
            print("3. Enable recording for desired cameras")
    
    def export_to_json(self):
        """Export discovered cameras to JSON file"""
        filename = Path("discovered_cameras.json")
        
        # Convert cameras to dictionaries
        camera_configs = []
        for camera in self.discovered_cameras:
            config = self.discovery.get_camera_config(camera)
            camera_configs.append(config)
        
        # Save to file
        with open(filename, 'w') as f:
            json.dump(camera_configs, f, indent=2)
        
        print(f"\n💾 Exported {len(camera_configs)} camera(s) to {filename}")
        print("   Review the file and add cameras manually as needed")

async def main():
    """Main entry point"""
    cli = ONVIFDiscoveryCLI()
    
    try:
        await cli.run()
    except KeyboardInterrupt:
        print("\n\n⚠️  Discovery cancelled by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"\n❌ An error occurred: {e}")
    finally:
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    asyncio.run(main())