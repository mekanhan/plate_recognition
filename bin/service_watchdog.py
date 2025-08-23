#!/usr/bin/env python3
"""
Service Watchdog
Monitors service health and automatically restarts failed services
"""
import asyncio
import time
import subprocess
import sys
import logging
from pathlib import Path
from typing import Dict, List
import aiohttp
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/service_watchdog.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class ServiceWatchdog:
    """Service health monitor and auto-restart system"""
    
    def __init__(self):
        self.services = {
            'main_api': {
                'port': 8001,
                'health_endpoint': '/health',
                'restart_command': ['python3', '-m', 'api.main'],
                'cwd': '.',
                'process': None,
                'failures': 0,
                'last_restart': 0
            },
            'recording_service': {
                'port': 8002,
                'health_endpoint': '/health',
                'restart_command': ['python3', 'bin/service-management/start_recording_service.py'],
                'cwd': '.',
                'process': None,
                'failures': 0,
                'last_restart': 0
            },
            'frontend': {
                'port': 8080,
                'health_endpoint': '/',
                'restart_command': ['python3', '-m', 'http.server', '8080', '--bind', '0.0.0.0'],
                'cwd': 'frontend',
                'process': None,
                'failures': 0,
                'last_restart': 0
            }
        }
        
        self.check_interval = 30  # Check every 30 seconds
        self.restart_threshold = 3  # Max failures before giving up
        self.restart_delay = 60  # Minimum seconds between restarts
        self.session = None
        
    async def start(self):
        """Start the watchdog"""
        logger.info("Starting Service Watchdog")
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10))
        
        while True:
            try:
                await self.check_all_services()
                await asyncio.sleep(self.check_interval)
            except KeyboardInterrupt:
                logger.info("Watchdog stopping...")
                break
            except Exception as e:
                logger.error(f"Watchdog error: {e}")
                await asyncio.sleep(5)
        
        if self.session:
            await self.session.close()
    
    async def check_all_services(self):
        """Check health of all services"""
        for name, config in self.services.items():
            try:
                is_healthy = await self.check_service_health(name, config)
                
                if not is_healthy:
                    config['failures'] += 1
                    logger.warning(f"Service {name} health check failed (failures: {config['failures']})")
                    
                    if config['failures'] >= self.restart_threshold:
                        logger.error(f"Service {name} exceeded failure threshold, attempting restart")
                        await self.restart_service(name, config)
                else:
                    # Reset failure count on successful health check
                    if config['failures'] > 0:
                        logger.info(f"Service {name} recovered, resetting failure count")
                        config['failures'] = 0
                        
            except Exception as e:
                logger.error(f"Error checking service {name}: {e}")
    
    async def check_service_health(self, name: str, config: Dict) -> bool:
        """Check if a service is healthy"""
        try:
            # Check if service is responding on its port
            url = f"http://localhost:{config['port']}{config['health_endpoint']}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    logger.debug(f"Service {name} is healthy")
                    return True
                else:
                    logger.warning(f"Service {name} returned status {response.status}")
                    return False
                    
        except (aiohttp.ClientError, asyncio.TimeoutError, ConnectionError) as e:
            logger.warning(f"Service {name} connection failed: {e}")
            return False
    
    async def restart_service(self, name: str, config: Dict):
        """Restart a failed service"""
        current_time = time.time()
        
        # Check if enough time has passed since last restart
        if current_time - config['last_restart'] < self.restart_delay:
            logger.info(f"Skipping restart of {name} (too soon since last restart)")
            return
        
        try:
            logger.info(f"Attempting to restart service: {name}")
            
            # Kill existing process if it exists
            await self.stop_service(name, config)
            
            # Wait a moment for cleanup
            await asyncio.sleep(2)
            
            # Start the service
            if await self.start_service(name, config):
                config['last_restart'] = current_time
                config['failures'] = 0  # Reset failure count on successful restart
                logger.info(f"Successfully restarted service: {name}")
            else:
                logger.error(f"Failed to restart service: {name}")
                
        except Exception as e:
            logger.error(f"Error restarting service {name}: {e}")
    
    async def start_service(self, name: str, config: Dict) -> bool:
        """Start a service"""
        try:
            # Use venv Python if available
            venv_python = Path(".venv/bin/python3")
            command = config['restart_command'].copy()
            
            if venv_python.exists() and command[0] in ['python', 'python3', sys.executable]:
                command[0] = str(venv_python.absolute())
            
            # Create log file
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            log_file = Path(f"logs/{name}_{timestamp}.log")
            
            # Start process
            with open(log_file, 'w') as log:
                process = subprocess.Popen(
                    command,
                    cwd=config['cwd'],
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True
                )
            
            config['process'] = process
            logger.info(f"Started {name} (PID: {process.pid})")
            
            # Give service time to start
            await asyncio.sleep(5)
            
            # Verify it's running
            return await self.check_service_health(name, config)
            
        except Exception as e:
            logger.error(f"Failed to start service {name}: {e}")
            return False
    
    async def stop_service(self, name: str, config: Dict):
        """Stop a service gracefully"""
        try:
            if config['process'] and config['process'].poll() is None:
                logger.info(f"Stopping service {name} (PID: {config['process'].pid})")
                config['process'].terminate()
                
                # Wait for graceful shutdown
                try:
                    config['process'].wait(timeout=10)
                except subprocess.TimeoutExpired:
                    logger.warning(f"Force killing service {name}")
                    config['process'].kill()
                
                config['process'] = None
            
            # Also try to find and kill any orphaned processes
            await self.kill_processes_on_port(config['port'])
            
        except Exception as e:
            logger.error(f"Error stopping service {name}: {e}")
    
    async def kill_processes_on_port(self, port: int):
        """Kill any processes listening on the given port"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'connections']):
                try:
                    connections = proc.info['connections']
                    if connections:
                        for conn in connections:
                            if conn.laddr.port == port:
                                logger.info(f"Killing process {proc.info['pid']} ({proc.info['name']}) on port {port}")
                                psutil.Process(proc.info['pid']).terminate()
                                break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            logger.error(f"Error killing processes on port {port}: {e}")

async def main():
    """Main entry point"""
    watchdog = ServiceWatchdog()
    await watchdog.start()

if __name__ == "__main__":
    asyncio.run(main())