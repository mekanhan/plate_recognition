"""
Application lifecycle management service for graceful startup, shutdown, and restart operations.
Follows industry standards for service lifecycle management.
"""
import asyncio
import signal
import sys
import os
import time
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class ServiceState(Enum):
    """Service state enumeration"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    RESTARTING = "restarting"
    FAILED = "failed"

class RestartType(Enum):
    """Types of restart operations"""
    GRACEFUL = "graceful"          # Graceful service restart
    IMMEDIATE = "immediate"        # Immediate restart without graceful shutdown
    FULL_PROCESS = "full_process"  # Full application process restart

class LifecycleService:
    """
    Centralized service for managing application lifecycle operations.
    Handles graceful shutdown, restart, and service coordination.
    """
    
    def __init__(self):
        self.state = ServiceState.STOPPED
        self.services = {}  # Registry of managed services
        self.shutdown_callbacks = []  # Callbacks to execute during shutdown
        self.startup_callbacks = []   # Callbacks to execute during startup
        self.signal_handlers_installed = False
        self.shutdown_timeout = 30.0  # Timeout for graceful shutdown
        self.restart_timeout = 60.0   # Timeout for restart operations
        self._shutdown_event = asyncio.Event()
        self._restart_event = asyncio.Event()
        self.health_checks = {}
        self.last_health_check = None
        
        # State persistence
        self.state_file = "data/application_state.json"
        
    async def initialize(self):
        """Initialize the lifecycle service"""
        try:
            self.state = ServiceState.STARTING
            
            # Install signal handlers for graceful shutdown
            await self._install_signal_handlers()
            
            # Load previous application state if available
            await self._load_application_state()
            
            self.state = ServiceState.RUNNING
            logger.info("Lifecycle service initialized successfully")
            
        except Exception as e:
            self.state = ServiceState.FAILED
            logger.error(f"Failed to initialize lifecycle service: {e}")
            raise
    
    def register_service(self, name: str, service_instance: Any, 
                        shutdown_method: str = "shutdown",
                        startup_method: str = "initialize",
                        health_check_method: str = None,
                        shutdown_order: int = 100):
        """
        Register a service for lifecycle management
        
        Args:
            name: Service name
            service_instance: The service instance
            shutdown_method: Method name to call for shutdown
            startup_method: Method name to call for startup
            health_check_method: Method name for health checks
            shutdown_order: Order of shutdown (lower numbers shutdown first)
        """
        self.services[name] = {
            "instance": service_instance,
            "shutdown_method": shutdown_method,
            "startup_method": startup_method,
            "health_check_method": health_check_method,
            "shutdown_order": shutdown_order,
            "state": ServiceState.STOPPED,
            "last_restart": None,
            "restart_count": 0
        }
        
        logger.info(f"Registered service: {name}")
    
    def add_shutdown_callback(self, callback: Callable, order: int = 100):
        """Add a callback to execute during shutdown"""
        self.shutdown_callbacks.append({"callback": callback, "order": order})
        self.shutdown_callbacks.sort(key=lambda x: x["order"])
    
    def add_startup_callback(self, callback: Callable, order: int = 100):
        """Add a callback to execute during startup"""
        self.startup_callbacks.append({"callback": callback, "order": order})
        self.startup_callbacks.sort(key=lambda x: x["order"])
    
    async def graceful_shutdown(self, timeout: Optional[float] = None) -> bool:
        """
        Perform graceful shutdown of all services
        
        Args:
            timeout: Maximum time to wait for shutdown
            
        Returns:
            True if shutdown completed successfully
        """
        if self.state in [ServiceState.STOPPING, ServiceState.STOPPED]:
            logger.warning("Shutdown already in progress or completed")
            return True
            
        logger.info("Starting graceful shutdown...")
        self.state = ServiceState.STOPPING
        shutdown_timeout = timeout or self.shutdown_timeout
        
        try:
            # Save current application state
            await self._save_application_state()
            
            # Execute shutdown callbacks
            await self._execute_shutdown_callbacks()
            
            # Shutdown services in order
            await self._shutdown_services(shutdown_timeout)
            
            self.state = ServiceState.STOPPED
            self._shutdown_event.set()
            
            logger.info("Graceful shutdown completed successfully")
            return True
            
        except asyncio.TimeoutError:
            logger.error(f"Shutdown timeout after {shutdown_timeout} seconds")
            self.state = ServiceState.FAILED
            return False
        except Exception as e:
            logger.error(f"Error during graceful shutdown: {e}")
            self.state = ServiceState.FAILED
            return False
    
    async def restart_application(self, restart_type: RestartType = RestartType.GRACEFUL) -> Dict[str, Any]:
        """
        Restart the entire application
        
        Args:
            restart_type: Type of restart to perform
            
        Returns:
            Dictionary with restart results
        """
        if self.state == ServiceState.RESTARTING:
            return {
                "success": False,
                "message": "Restart already in progress",
                "timestamp": datetime.now().isoformat()
            }
        
        logger.info(f"Starting application restart (type: {restart_type.value})")
        self.state = ServiceState.RESTARTING
        
        try:
            if restart_type == RestartType.FULL_PROCESS:
                return await self._restart_full_process()
            else:
                return await self._restart_services(restart_type)
                
        except Exception as e:
            logger.error(f"Error during restart: {e}")
            self.state = ServiceState.FAILED
            return {
                "success": False,
                "message": f"Restart failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def restart_service(self, service_name: str) -> Dict[str, Any]:
        """
        Restart a specific service
        
        Args:
            service_name: Name of the service to restart
            
        Returns:
            Dictionary with restart results
        """
        if service_name not in self.services:
            return {
                "success": False,
                "message": f"Service '{service_name}' not found",
                "timestamp": datetime.now().isoformat()
            }
        
        service_info = self.services[service_name]
        service_instance = service_info["instance"]
        
        try:
            logger.info(f"Restarting service: {service_name}")
            
            # Shutdown the service
            if hasattr(service_instance, service_info["shutdown_method"]):
                shutdown_method = getattr(service_instance, service_info["shutdown_method"])
                if asyncio.iscoroutinefunction(shutdown_method):
                    await shutdown_method()
                else:
                    shutdown_method()
            
            service_info["state"] = ServiceState.STOPPED
            
            # Wait a moment for cleanup
            await asyncio.sleep(1)
            
            # Restart the service
            if hasattr(service_instance, service_info["startup_method"]):
                startup_method = getattr(service_instance, service_info["startup_method"])
                if asyncio.iscoroutinefunction(startup_method):
                    await startup_method()
                else:
                    startup_method()
            
            service_info["state"] = ServiceState.RUNNING
            service_info["last_restart"] = datetime.now().isoformat()
            service_info["restart_count"] += 1
            
            logger.info(f"Service '{service_name}' restarted successfully")
            
            return {
                "success": True,
                "message": f"Service '{service_name}' restarted successfully",
                "service": service_name,
                "restart_count": service_info["restart_count"],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to restart service '{service_name}': {e}")
            service_info["state"] = ServiceState.FAILED
            
            return {
                "success": False,
                "message": f"Failed to restart service '{service_name}': {str(e)}",
                "service": service_name,
                "timestamp": datetime.now().isoformat()
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all registered services
        
        Returns:
            Dictionary with health check results
        """
        health_results = {
            "overall_status": "healthy",
            "services": {},
            "timestamp": datetime.now().isoformat(),
            "application_state": self.state.value
        }
        
        failed_services = 0
        
        for service_name, service_info in self.services.items():
            try:
                service_instance = service_info["instance"]
                health_method = service_info.get("health_check_method")
                
                if health_method and hasattr(service_instance, health_method):
                    check_method = getattr(service_instance, health_method)
                    
                    if asyncio.iscoroutinefunction(check_method):
                        result = await check_method()
                    else:
                        result = check_method()
                    
                    health_results["services"][service_name] = {
                        "status": "healthy" if result else "unhealthy",
                        "details": result if isinstance(result, dict) else {"healthy": result}
                    }
                    
                    if not result:
                        failed_services += 1
                        
                else:
                    # Basic health check - service is registered and state is not failed
                    is_healthy = service_info["state"] != ServiceState.FAILED
                    health_results["services"][service_name] = {
                        "status": "healthy" if is_healthy else "unhealthy",
                        "details": {"state": service_info["state"].value}
                    }
                    
                    if not is_healthy:
                        failed_services += 1
                        
            except Exception as e:
                logger.error(f"Health check failed for service '{service_name}': {e}")
                health_results["services"][service_name] = {
                    "status": "unhealthy",
                    "details": {"error": str(e)}
                }
                failed_services += 1
        
        # Determine overall status
        if failed_services > 0:
            if failed_services == len(self.services):
                health_results["overall_status"] = "critical"
            else:
                health_results["overall_status"] = "degraded"
        
        self.last_health_check = health_results
        return health_results
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current application status"""
        return {
            "application_state": self.state.value,
            "services": {
                name: {
                    "state": info["state"].value,
                    "restart_count": info["restart_count"],
                    "last_restart": info["last_restart"]
                }
                for name, info in self.services.items()
            },
            "shutdown_event_set": self._shutdown_event.is_set(),
            "restart_event_set": self._restart_event.is_set(),
            "timestamp": datetime.now().isoformat()
        }
    
    async def wait_for_shutdown(self):
        """Wait for shutdown signal"""
        await self._shutdown_event.wait()
    
    async def _install_signal_handlers(self):
        """Install signal handlers for graceful shutdown"""
        if self.signal_handlers_installed:
            return
            
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            asyncio.create_task(self.graceful_shutdown())
        
        try:
            signal.signal(signal.SIGTERM, signal_handler)
            signal.signal(signal.SIGINT, signal_handler)
            
            # On Unix systems, also handle SIGHUP for restart
            if hasattr(signal, 'SIGHUP'):
                def restart_handler(signum, frame):
                    logger.info(f"Received SIGHUP signal, initiating restart...")
                    asyncio.create_task(self.restart_application(RestartType.GRACEFUL))
                signal.signal(signal.SIGHUP, restart_handler)
            
            self.signal_handlers_installed = True
            logger.info("Signal handlers installed successfully")
            
        except Exception as e:
            logger.warning(f"Could not install signal handlers: {e}")
    
    async def _execute_shutdown_callbacks(self):
        """Execute all shutdown callbacks"""
        for callback_info in self.shutdown_callbacks:
            try:
                callback = callback_info["callback"]
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
                    
            except Exception as e:
                logger.error(f"Error executing shutdown callback: {e}")
    
    async def _shutdown_services(self, timeout: float):
        """Shutdown all services in order"""
        # Sort services by shutdown order
        sorted_services = sorted(
            self.services.items(),
            key=lambda x: x[1]["shutdown_order"]
        )
        
        shutdown_tasks = []
        
        for service_name, service_info in sorted_services:
            service_instance = service_info["instance"]
            shutdown_method = service_info["shutdown_method"]
            
            if hasattr(service_instance, shutdown_method):
                try:
                    method = getattr(service_instance, shutdown_method)
                    
                    if asyncio.iscoroutinefunction(method):
                        task = asyncio.create_task(method())
                        shutdown_tasks.append((service_name, task))
                    else:
                        method()
                        service_info["state"] = ServiceState.STOPPED
                        logger.info(f"Shutdown service: {service_name}")
                        
                except Exception as e:
                    logger.error(f"Error shutting down service '{service_name}': {e}")
                    service_info["state"] = ServiceState.FAILED
        
        # Wait for async shutdowns with timeout
        if shutdown_tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*[task for _, task in shutdown_tasks], return_exceptions=True),
                    timeout=timeout
                )
                
                for service_name, task in shutdown_tasks:
                    if task.done() and not task.exception():
                        self.services[service_name]["state"] = ServiceState.STOPPED
                        logger.info(f"Shutdown service: {service_name}")
                    else:
                        logger.error(f"Failed to shutdown service: {service_name}")
                        self.services[service_name]["state"] = ServiceState.FAILED
                        
            except asyncio.TimeoutError:
                logger.error(f"Service shutdown timeout after {timeout} seconds")
                # Cancel remaining tasks
                for _, task in shutdown_tasks:
                    if not task.done():
                        task.cancel()
                raise
    
    async def _restart_services(self, restart_type: RestartType) -> Dict[str, Any]:
        """Restart services without full process restart"""
        try:
            # Graceful shutdown first
            if restart_type == RestartType.GRACEFUL:
                await self._shutdown_services(self.shutdown_timeout)
            
            # Wait a moment for cleanup
            await asyncio.sleep(2)
            
            # Execute startup callbacks
            await self._execute_startup_callbacks()
            
            # Restart services
            restart_results = {}
            for service_name in self.services:
                result = await self.restart_service(service_name)
                restart_results[service_name] = result["success"]
            
            # Determine overall success
            all_success = all(restart_results.values())
            
            if all_success:
                self.state = ServiceState.RUNNING
                self._restart_event.set()
                
                return {
                    "success": True,
                    "message": "Application restarted successfully",
                    "restart_type": restart_type.value,
                    "services_restarted": list(restart_results.keys()),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                failed_services = [name for name, success in restart_results.items() if not success]
                self.state = ServiceState.FAILED
                
                return {
                    "success": False,
                    "message": f"Restart partially failed. Failed services: {failed_services}",
                    "restart_type": restart_type.value,
                    "failed_services": failed_services,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            self.state = ServiceState.FAILED
            return {
                "success": False,
                "message": f"Restart failed: {str(e)}",
                "restart_type": restart_type.value,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _restart_full_process(self) -> Dict[str, Any]:
        """Restart the entire process"""
        try:
            logger.info("Initiating full process restart...")
            
            # Save state before restart
            await self._save_application_state()
            
            # Schedule the restart (this will exit the current process)
            asyncio.get_event_loop().call_later(2.0, self._exit_for_restart)
            
            return {
                "success": True,
                "message": "Full process restart initiated",
                "restart_type": RestartType.FULL_PROCESS.value,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to initiate process restart: {str(e)}",
                "restart_type": RestartType.FULL_PROCESS.value,
                "timestamp": datetime.now().isoformat()
            }
    
    def _exit_for_restart(self):
        """Exit the process for restart (should be handled by process manager)"""
        logger.info("Exiting process for restart...")
        sys.exit(3)  # Exit code 3 indicates restart request
    
    async def _execute_startup_callbacks(self):
        """Execute all startup callbacks"""
        for callback_info in self.startup_callbacks:
            try:
                callback = callback_info["callback"]
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
                    
            except Exception as e:
                logger.error(f"Error executing startup callback: {e}")
    
    async def _save_application_state(self):
        """Save current application state to file"""
        try:
            state_data = {
                "shutdown_time": datetime.now().isoformat(),
                "application_state": self.state.value,
                "services": {
                    name: {
                        "state": info["state"].value,
                        "restart_count": info["restart_count"],
                        "last_restart": info["last_restart"]
                    }
                    for name, info in self.services.items()
                }
            }
            
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            
            import json
            with open(self.state_file, 'w') as f:
                json.dump(state_data, f, indent=2)
                
            logger.debug(f"Application state saved to {self.state_file}")
            
        except Exception as e:
            logger.warning(f"Could not save application state: {e}")
    
    async def _load_application_state(self):
        """Load previous application state from file"""
        try:
            if os.path.exists(self.state_file):
                import json
                with open(self.state_file, 'r') as f:
                    state_data = json.load(f)
                
                logger.info(f"Loaded previous application state from {state_data.get('shutdown_time', 'unknown time')}")
                
                # You could use this data to restore service states or perform recovery
                
        except Exception as e:
            logger.debug(f"Could not load application state: {e}")

# Global lifecycle service instance
lifecycle_service = LifecycleService()