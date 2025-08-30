# scripts/onvif_integration.py
"""
ONVIF Integration for Vision Port
Combines your existing ONVIF documentation with your current camera management system
"""

import asyncio
import json
from typing import List, Dict, Optional
from pathlib import Path
import logging

# Import your existing ONVIF discovery implementation
from docs.features.Camera.ONVIF.onvif_discovery_implementation import ONVIFDiscovery, ONVIFDevice

# Import your existing camera management
from ai_pipeline.camera_manager import CameraManager, CameraConfig
from database.service import DatabaseService

logger = logging.getLogger(__name__)

class VisionPortONVIFIntegration:
    """
    Integration of ONVIF discovery with Vision Port's existing camera management
    Based on your documented ONVIF implementation
    """
    
    def __init__(self, camera_manager: CameraManager, db_service: DatabaseService):
        self.camera_manager = camera_manager
        self.db_service = db_service
        self.onvif_discovery = ONVIFDiscovery(timeout=10.0)
        self.discovery_cache_file = Path("data/onvif_discovery_cache.json")
        
        # Brand-specific configurations from your documentation
        self.brand_configs = {
            'reolink': {
                'default_paths': {
                    'main': '/h264Preview_01_main',
                    'sub': '/h264Preview_01_sub',
                    'snapshot': '/cgi-bin/api.cgi?cmd=Snap'
                },
                'default_port': 554,
                'default_username': 'admin',
                'onvif_port': 8080
            },
            'hikvision': {
                'default_paths': {
                    'main': '/Streaming/Channels/101',
                    'sub': '/Streaming/Channels/102',
                    'snapshot': '/Streaming/Channels/1/picture'
                },
                'default_port': 554,
                'default_username': 'admin',
                'onvif_port': 80
            },
            'dahua': {
                'default_paths': {
                    'main': '/cam/realmonitor?channel=1&subtype=0',
                    'sub': '/cam/realmonitor?channel=1&subtype=1',
                    'snapshot': '/cgi-bin/snapshot.cgi'
                },
                'default_port': 554,
                'default_username': 'admin',
                'onvif_port': 80
            },
            'axis': {
                'default_paths': {
                    'main': '/axis-media/media.amp',
                    'sub': '/axis-media/media.amp?resolution=640x480',
                    'snapshot': '/axis-cgi/jpg/image.cgi'
                },
                'default_port': 554,
                'default_username': 'root',
                'onvif_port': 80
            },
            'generic': {
                'default_paths': {
                    'main': '/stream1',
                    'sub': '/stream2', 
                    'snapshot': '/snapshot.jpg'
                },
                'default_port': 554,
                'default_username': 'admin',
                'onvif_port': 80
            }
        }
    
    async def discover_and_integrate_cameras(self) -> List[Dict]:
        """
        Discover ONVIF cameras and prepare them for integration
        Returns list of camera configurations ready for your system
        """
        logger.info("🔍 Starting ONVIF camera discovery...")
        
        # Use your documented discovery implementation
        discovered_devices = self.onvif_discovery.discover_all()
        
        camera_configs = []
        existing_cameras = await self._get_existing_camera_ips()
        
        for ip, device in discovered_devices.items():
            if ip not in existing_cameras:
                config = self._create_camera_config(device)
                if config:
                    camera_configs.append(config)
                    logger.info(f"📹 Prepared config for: {device}")
        
        # Cache discoveries
        await self._cache_discoveries(discovered_devices)
        
        logger.info(f"✅ Found {len(camera_configs)} new cameras ready for integration")
        return camera_configs
    
    def _create_camera_config(self, device: ONVIFDevice) -> Optional[Dict]:
        """
        Create Vision Port camera configuration from ONVIF device
        Uses brand-specific defaults from your documentation
        """
        try:
            # Determine brand configuration
            brand_key = self._detect_brand(device)
            brand_config = self.brand_configs.get(brand_key, self.brand_configs['generic'])
            
            # Create configuration matching your CameraConfig structure
            config = {
                # Basic identification
                'camera_id': f"onvif_{device.ip.replace('.', '_')}",
                'name': f"{device.manufacturer} {device.model}".strip() or f"Camera {device.ip}",
                'ip_address': device.ip,
                'port': brand_config['default_port'],
                
                # Authentication (will need manual configuration)
                'username': brand_config['default_username'],
                'password': '',  # Must be set manually for security
                
                # Stream paths based on brand
                'stream_path': brand_config['default_paths']['main'],
                'sub_stream_path': brand_config['default_paths']['sub'],
                'snapshot_path': brand_config['default_paths']['snapshot'],
                
                # Protocol and connection
                'protocol': 'rtsp',
                'timeout': 30,
                'retry_attempts': 3,
                
                # ONVIF-specific information
                'onvif_service_url': device.service_address,
                'onvif_port': brand_config['onvif_port'],
                'discovered_via': 'onvif',
                'discovery_timestamp': self._get_current_timestamp(),
                
                # Metadata
                'manufacturer': device.manufacturer or 'Unknown',
                'model': device.model or 'Unknown',
                'hardware_id': device.hardware_id,
                'scopes': device.scopes,
                
                # Default settings
                'enabled': False,  # Require manual activation
                'recording_enabled': True,
                'ai_processing_enabled': True
            }
            
            return config
            
        except Exception as e:
            logger.error(f"Error creating config for {device.ip}: {e}")
            return None
    
    def _detect_brand(self, device: ONVIFDevice) -> str:
        """Detect camera brand from manufacturer or model information"""
        manufacturer = (device.manufacturer or '').lower()
        model = (device.model or '').lower()
        
        brand_keywords = {
            'reolink': ['reolink'],
            'hikvision': ['hikvision', 'hikvis'],
            'dahua': ['dahua'],
            'axis': ['axis']
        }
        
        for brand, keywords in brand_keywords.items():
            for keyword in keywords:
                if keyword in manufacturer or keyword in model:
                    return brand
        
        return 'generic'
    
    async def _get_existing_camera_ips(self) -> set:
        """Get IPs of cameras already in the system"""
        try:
            cameras = await self.db_service.get_all_cameras()
            return {camera.ip_address for camera in cameras}
        except Exception as e:
            logger.error(f"Error getting existing cameras: {e}")
            return set()
    
    async def add_discovered_camera(self, config: Dict) -> bool:
        """
        Add a discovered camera to your Vision Port system
        """
        try:
            # Create CameraConfig object
            camera_config = CameraConfig(
                camera_id=config['camera_id'],
                name=config['name'],
                ip_address=config['ip_address'],
                username=config['username'],
                password=config['password'],
                port=config['port'],
                stream_path=config['stream_path'],
                protocol=config['protocol']
            )
            
            # Add to camera manager (your existing system)
            success = await self.camera_manager.add_camera(camera_config)
            
            if success:
                # Save additional ONVIF metadata to database
                await self._save_onvif_metadata(config)
                logger.info(f"✅ Successfully added camera: {config['name']}")
                return True
            else:
                logger.error(f"❌ Failed to add camera: {config['name']}")
                return False
                
        except Exception as e:
            logger.error(f"Error adding camera {config['camera_id']}: {e}")
            return False
    
    async def _save_onvif_metadata(self, config: Dict):
        """Save ONVIF-specific metadata for future reference"""
        metadata = {
            'onvif_service_url': config.get('onvif_service_url'),
            'onvif_port': config.get('onvif_port'),
            'manufacturer': config.get('manufacturer'),
            'model': config.get('model'),
            'hardware_id': config.get('hardware_id'),
            'scopes': config.get('scopes'),
            'discovery_timestamp': config.get('discovery_timestamp'),
            'brand_detected': self._detect_brand_from_config(config)
        }
        
        # Save to your database (extend your existing schema if needed)
        await self.db_service.save_camera_metadata(config['camera_id'], metadata)
    
    async def _cache_discoveries(self, devices: Dict):
        """Cache discovered devices for faster subsequent access"""
        cache_data = {
            'timestamp': self._get_current_timestamp(),
            'devices': {
                ip: {
                    'ip': device.ip,
                    'port': device.port,
                    'manufacturer': device.manufacturer,
                    'model': device.model,
                    'service_address': device.service_address,
                    'scopes': device.scopes
                }
                for ip, device in devices.items()
            }
        }
        
        try:
            self.discovery_cache_file.parent.mkdir(exist_ok=True)
            with open(self.discovery_cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            logger.debug(f"💾 Cached {len(devices)} discoveries")
        except Exception as e:
            logger.error(f"Error caching discoveries: {e}")
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _detect_brand_from_config(self, config: Dict) -> str:
        """Helper to detect brand from config"""
        class MockDevice:
            def __init__(self, manufacturer, model):
                self.manufacturer = manufacturer
                self.model = model
        
        mock_device = MockDevice(config.get('manufacturer'), config.get('model'))
        return self._detect_brand(mock_device)

# CLI interface for manual discovery
async def run_onvif_discovery():
    """
    Command-line interface for ONVIF discovery
    Integrates with your existing Vision Port system
    """
    print("🚀 Vision Port ONVIF Discovery")
    print("=" * 40)
    
    # Initialize with your existing services
    from ai_pipeline.camera_manager import CameraManager
    from database.service import DatabaseService
    
    camera_manager = CameraManager()
    db_service = DatabaseService()
    
    # Create integration service
    onvif_integration = VisionPortONVIFIntegration(camera_manager, db_service)
    
    # Discover cameras
    discovered_configs = await onvif_integration.discover_and_integrate_cameras()
    
    if not discovered_configs:
        print("\n📭 No new ONVIF cameras found")
        print("\n💡 Troubleshooting:")
        print("  1. Ensure cameras are on the same network")
        print("  2. Check firewall settings for UDP port 3702")
        print("  3. Verify cameras are ONVIF-compliant")
        return
    
    # Display discovered cameras
    print(f"\n📹 Found {len(discovered_configs)} new cameras:")
    for i, config in enumerate(discovered_configs, 1):
        print(f"\n{i}. {config['name']}")
        print(f"   IP: {config['ip_address']}")
        print(f"   Brand: {config['manufacturer']}")
        print(f"   Model: {config['model']}")
        print(f"   Stream: rtsp://{config['ip_address']}:{config['port']}{config['stream_path']}")
        print(f"   ⚠️  Password required: Set manually after adding")
    
    # Interactive addition
    print(f"\n🔧 Integration Options:")
    print("1. Add all cameras to Vision Port")
    print("2. Add selected cameras")
    print("3. Export configurations for manual review")
    print("4. Exit without adding")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    if choice == "1":
        await _add_all_cameras(onvif_integration, discovered_configs)
    elif choice == "2":
        await _add_selected_cameras(onvif_integration, discovered_configs)
    elif choice == "3":
        _export_configurations(discovered_configs)
    else:
        print("👋 Exiting without changes")

async def _add_all_cameras(integration, configs):
    """Add all discovered cameras to Vision Port"""
    print(f"\n🔄 Adding {len(configs)} cameras to Vision Port...")
    
    success_count = 0
    for config in configs:
        if await integration.add_discovered_camera(config):
            success_count += 1
    
    print(f"\n✅ Successfully added {success_count}/{len(configs)} cameras")
    if success_count < len(configs):
        print("⚠️  Some cameras failed to add - check logs for details")
    
    print("\n📋 Next steps:")
    print("1. Set passwords for each camera in Vision Port interface")
    print("2. Test camera connections")
    print("3. Enable recording and AI processing as needed")

async def _add_selected_cameras(integration, configs):
    """Allow user to select which cameras to add"""
    print("\n🎯 Select cameras to add (comma-separated numbers):")
    
    for i, config in enumerate(configs, 1):
        print(f"{i}. {config['name']} ({config['ip_address']})")
    
    selection = input("\nEnter camera numbers: ").strip()
    
    try:
        indices = [int(x.strip()) - 1 for x in selection.split(',')]
        selected_configs = [configs[i] for i in indices if 0 <= i < len(configs)]
        
        for config in selected_configs:
            await integration.add_discovered_camera(config)
            
        print(f"✅ Added {len(selected_configs)} selected cameras")
        
    except (ValueError, IndexError) as e:
        print(f"❌ Invalid selection: {e}")

def _export_configurations(configs):
    """Export configurations to JSON file for manual review"""
    export_file = Path("onvif_discovered_cameras.json")
    
    with open(export_file, 'w') as f:
        json.dump(configs, f, indent=2)
    
    print(f"💾 Exported {len(configs)} camera configurations to {export_file}")
    print("📋 Review the file and manually add cameras as needed")

if __name__ == "__main__":
    # Run the discovery integration
    asyncio.run(run_onvif_discovery())
