"""
Device Service for managing device identity and authentication
"""
import os
import uuid
import hashlib
import secrets
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

try:
    import jwt
except ImportError:
    jwt = None

import aiohttp
from app.models import DeviceConfig
from app.database import async_session

logger = logging.getLogger(__name__)

class DeviceService:
    """Manages device identity and authentication"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.device_id = None
        self.api_key = None
        self.api_key_hash = None
        self.jwt_token = None
        self.fernet = None
        self.cloud_endpoint = self.config.get('cloud_api_url', 'https://api.lprcloud.com')
        self.config_file = "data/device_config.json"
        
    async def initialize(self) -> bool:
        """Initialize device identity"""
        try:
            # Ensure data directory exists
            os.makedirs("data", exist_ok=True)
            
            # Try to load existing configuration
            if await self._load_existing_config():
                logger.info(f"Loaded existing device configuration: {self.device_id}")
                
                # Validate with cloud if available
                if await self._validate_device():
                    return True
                else:
                    logger.warning("Device validation failed, re-registering...")
            
            # Register new device
            return await self._register_device()
            
        except Exception as e:
            logger.error(f"Device initialization failed: {e}")
            return False
    
    async def _load_existing_config(self) -> bool:
        """Load existing device configuration"""
        try:
            # Try SQLite first
            async with async_session() as session:
                result = await session.execute(
                    select(DeviceConfig).limit(1)
                )
                device_config = result.scalar_one_or_none()
                
                if device_config:
                    self.device_id = device_config.device_id
                    self.api_key_hash = device_config.api_key_hash
                    self.cloud_endpoint = device_config.cloud_endpoint or self.cloud_endpoint
                    
                    # Try to load encryption key
                    self._load_encryption_key()
                    
                    logger.info("Loaded device config from database")
                    return True
            
            # Fallback to JSON file
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                
                self.device_id = config_data.get('device_id')
                self.api_key_hash = config_data.get('api_key_hash')
                self.cloud_endpoint = config_data.get('cloud_endpoint', self.cloud_endpoint)
                
                # Migrate to database
                await self._save_config_to_db(config_data)
                
                # Try to load encryption key
                self._load_encryption_key()
                
                logger.info("Loaded device config from file and migrated to database")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error loading device config: {e}")
            return False
    
    def _load_encryption_key(self):
        """Load or generate encryption key"""
        key_file = "data/device.key"
        try:
            if os.path.exists(key_file):
                with open(key_file, 'rb') as f:
                    self.fernet = Fernet(f.read())
            else:
                # Generate new key
                key = Fernet.generate_key()
                with open(key_file, 'wb') as f:
                    f.write(key)
                self.fernet = Fernet(key)
                logger.info("Generated new encryption key")
        except Exception as e:
            logger.error(f"Error with encryption key: {e}")
    
    def _generate_device_id(self) -> str:
        """Generate unique device ID based on hardware"""
        identifiers = []
        
        # Try to get MAC address
        try:
            import netifaces
            for iface in netifaces.interfaces():
                if iface.startswith(('eth', 'wlan', 'en')):
                    addrs = netifaces.ifaddresses(iface)
                    if netifaces.AF_LINK in addrs:
                        mac = addrs[netifaces.AF_LINK][0]['addr']
                        if mac != '00:00:00:00:00:00':
                            identifiers.append(mac.replace(':', ''))
                            break
        except ImportError:
            pass
        except Exception:
            pass
        
        # Try to get CPU serial (Raspberry Pi)
        try:
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if line.startswith('Serial'):
                        serial = line.split(':')[1].strip()
                        if serial and serial != '0000000000000000':
                            identifiers.append(serial)
                        break
        except Exception:
            pass
        
        # Try to get machine ID
        try:
            with open('/etc/machine-id', 'r') as f:
                machine_id = f.read().strip()
                if machine_id:
                    identifiers.append(machine_id[:12])
        except Exception:
            pass
        
        # Add hostname
        try:
            import socket
            hostname = socket.gethostname()
            if hostname:
                identifiers.append(hostname)
        except Exception:
            pass
        
        # Add randomness if we don't have enough identifiers
        if len(identifiers) < 2:
            identifiers.append(str(uuid.uuid4()).replace('-', '')[:8])
        
        # Generate device ID
        combined = '-'.join(identifiers)
        device_hash = hashlib.sha256(combined.encode()).hexdigest()[:12]
        
        return f"LPR-{device_hash.upper()}"
    
    async def _register_device(self) -> bool:
        """Register device with cloud platform"""
        try:
            self.device_id = self._generate_device_id()
            
            # Generate local API key
            self.api_key = secrets.token_urlsafe(32)
            self.api_key_hash = hashlib.sha256(self.api_key.encode()).hexdigest()
            
            # Prepare registration data
            registration_data = {
                'device_id': self.device_id,
                'device_type': 'edge_lpr',
                'capabilities': {
                    'model_version': '2.0.0',
                    'has_gpu': self._check_gpu_available(),
                    'camera_resolution': '1920x1080'
                },
                'registration_token': self.config.get('registration_token', 'default-token')
            }
            
            # Try to register with cloud
            cloud_registered = await self._register_with_cloud(registration_data)
            
            # Save configuration locally regardless of cloud registration
            await self._save_config()
            
            if cloud_registered:
                logger.info(f"Device registered with cloud: {self.device_id}")
            else:
                logger.warning(f"Device registered locally only: {self.device_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Device registration failed: {e}")
            return False
    
    async def _register_with_cloud(self, registration_data: Dict) -> bool:
        """Attempt to register with cloud platform"""
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{self.cloud_endpoint}/api/v1/devices/register",
                    json=registration_data
                ) as response:
                    if response.status == 201:
                        result = await response.json()
                        # Cloud may provide additional configuration
                        if 'sync_interval' in result:
                            self.config['sync_interval'] = result['sync_interval']
                        return True
                    else:
                        logger.warning(f"Cloud registration failed: {response.status}")
                        return False
                        
        except asyncio.TimeoutError:
            logger.warning("Cloud registration timeout - operating in offline mode")
            return False
        except Exception as e:
            logger.warning(f"Cloud registration error: {e} - operating in offline mode")
            return False
    
    async def _validate_device(self) -> bool:
        """Validate device with cloud platform"""
        if not self.device_id or not self.api_key_hash:
            return False
            
        try:
            headers = self.get_auth_headers()
            timeout = aiohttp.ClientTimeout(total=5)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    f"{self.cloud_endpoint}/api/v1/devices/validate",
                    headers=headers
                ) as response:
                    return response.status == 200
                    
        except Exception:
            # If cloud validation fails, assume device is valid for offline operation
            return True
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API calls"""
        headers = {
            'X-Device-ID': self.device_id or 'unknown',
            'Content-Type': 'application/json'
        }
        
        if self.api_key:
            headers['X-API-Key'] = self.api_key
        elif self.api_key_hash:
            # For local validation, we can use the hash
            headers['X-API-Key-Hash'] = self.api_key_hash
        
        # Generate JWT if possible
        if jwt and self.api_key:
            try:
                token = self._generate_jwt()
                headers['Authorization'] = f'Bearer {token}'
            except Exception as e:
                logger.debug(f"JWT generation failed: {e}")
        
        return headers
    
    def _generate_jwt(self) -> str:
        """Generate JWT token for API authentication"""
        if not jwt:
            raise RuntimeError("PyJWT not available")
            
        payload = {
            'device_id': self.device_id,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=1)
        }
        
        return jwt.encode(payload, self.api_key or 'default-secret', algorithm='HS256')
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data for local storage"""
        if not self.fernet:
            raise RuntimeError("Encryption not initialized")
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted: str) -> str:
        """Decrypt sensitive data from local storage"""
        if not self.fernet:
            raise RuntimeError("Encryption not initialized")
        return self.fernet.decrypt(encrypted.encode()).decode()
    
    async def _save_config(self):
        """Save device configuration"""
        config_data = {
            'device_id': self.device_id,
            'api_key_hash': self.api_key_hash,
            'cloud_endpoint': self.cloud_endpoint,
            'registered_at': datetime.utcnow().isoformat(),
            'device_type': 'edge_lpr',
            'capabilities': {
                'model_version': '2.0.0',
                'has_gpu': self._check_gpu_available()
            }
        }
        
        # Save to database
        await self._save_config_to_db(config_data)
        
        # Also save to file as backup
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save config file: {e}")
    
    async def _save_config_to_db(self, config_data: Dict):
        """Save configuration to database"""
        try:
            async with async_session() as session:
                # Check if config exists
                result = await session.execute(
                    select(DeviceConfig).limit(1)
                )
                device_config = result.scalar_one_or_none()
                
                if device_config:
                    # Update existing
                    device_config.device_id = config_data['device_id']
                    device_config.api_key_hash = config_data['api_key_hash']
                    device_config.cloud_endpoint = config_data['cloud_endpoint']
                    device_config.capabilities = config_data.get('capabilities', {})
                    device_config.updated_at = datetime.utcnow()
                else:
                    # Create new
                    device_config = DeviceConfig(
                        device_id=config_data['device_id'],
                        api_key_hash=config_data['api_key_hash'],
                        cloud_endpoint=config_data['cloud_endpoint'],
                        capabilities=config_data.get('capabilities', {}),
                        registered_at=datetime.utcnow()
                    )
                    session.add(device_config)
                
                await session.commit()
                logger.debug("Device config saved to database")
                
        except Exception as e:
            logger.error(f"Failed to save config to database: {e}")
    
    def _check_gpu_available(self) -> bool:
        """Check if GPU is available"""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    async def update_last_seen(self):
        """Update last seen timestamp"""
        try:
            async with async_session() as session:
                await session.execute(
                    update(DeviceConfig)
                    .where(DeviceConfig.device_id == self.device_id)
                    .values(last_seen=datetime.utcnow())
                )
                await session.commit()
        except Exception as e:
            logger.debug(f"Failed to update last seen: {e}")
    
    def get_device_info(self) -> Dict[str, Any]:
        """Get device information"""
        return {
            'device_id': self.device_id,
            'device_type': 'edge_lpr',
            'cloud_endpoint': self.cloud_endpoint,
            'has_gpu': self._check_gpu_available(),
            'registration_status': 'registered' if self.device_id else 'pending'
        }