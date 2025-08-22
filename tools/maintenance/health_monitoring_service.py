#!/usr/bin/env python3
"""
Health Monitoring Service for LPR System
Continuous monitoring with alerting and auto-recovery
"""
import asyncio
import json
import signal
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    from config.app_config import get_config
    from utils.log_manager import get_service_logger
    from monitoring.health_monitor import HealthMonitor, HealthStatus
    HAS_CONFIG = True
except ImportError:
    HAS_CONFIG = False
    import logging


class HealthMonitoringService:
    """
    Background service for continuous health monitoring
    """
    
    def __init__(self, check_interval: int = 60, alert_threshold: int = 3):
        self.check_interval = check_interval  # seconds between checks
        self.alert_threshold = alert_threshold  # consecutive failures before alert
        self.running = False
        
        if HAS_CONFIG:
            self.config = get_config()
            self.logger = get_service_logger('health_monitoring')
        else:
            self.config = None
            self.logger = logging.getLogger('health_monitoring')
        
        # Tracking for alerting
        self.consecutive_failures = {}
        self.last_alert_times = {}
        self.alert_cooldown = 300  # 5 minutes between same alerts
        
        # Health status file for external monitoring
        self.status_file = Path("health_status.json")
    
    async def start(self):
        """Start the health monitoring service"""
        self.running = True
        self.logger.info("Health monitoring service starting...")
        
        # Initial health check
        await self.perform_monitoring_cycle()
        
        # Schedule regular monitoring
        while self.running:
            try:
                await asyncio.sleep(self.check_interval)
                if self.running:
                    await self.perform_monitoring_cycle()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring cycle: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
        
        self.logger.info("Health monitoring service stopped")
    
    async def perform_monitoring_cycle(self):
        """Perform one complete monitoring cycle"""
        try:
            self.logger.debug("Starting health monitoring cycle...")
            
            async with HealthMonitor() as monitor:
                health = await monitor.perform_full_health_check()
                
                # Log overall health status
                status_msg = f"System health: {health.overall_status.value} ({len(health.checks)} checks)"
                if health.overall_status == HealthStatus.HEALTHY:
                    self.logger.info(status_msg)
                elif health.overall_status == HealthStatus.WARNING:
                    self.logger.warning(status_msg)
                else:
                    self.logger.error(status_msg)
                
                # Check for issues and handle alerts
                await self.process_health_results(health)
                
                # Update status file
                self.update_status_file(health)
                
                # Get trends for longer-term monitoring
                trends = monitor.get_health_trends(hours=24)
                if trends.get('uptime_percentage', 0) < 95:
                    self.logger.warning(f"24h uptime: {trends.get('uptime_percentage', 0):.1f}%")
        
        except Exception as e:
            self.logger.error(f"Failed to perform health check: {e}")
    
    async def process_health_results(self, health):
        """Process health results and handle alerting/recovery"""
        current_time = datetime.now()
        
        for check in health.checks:
            check_name = check.name
            
            if check.status in [HealthStatus.CRITICAL, HealthStatus.WARNING]:
                # Track consecutive failures
                if check_name not in self.consecutive_failures:
                    self.consecutive_failures[check_name] = 0
                self.consecutive_failures[check_name] += 1
                
                # Check if we need to alert
                if (self.consecutive_failures[check_name] >= self.alert_threshold and
                    self.should_send_alert(check_name, current_time)):
                    
                    await self.send_alert(check)
                    self.last_alert_times[check_name] = current_time
                
                # Attempt auto-recovery for certain issues
                if check.status == HealthStatus.CRITICAL:
                    await self.attempt_auto_recovery(check)
            
            else:
                # Reset failure count on success
                if check_name in self.consecutive_failures:
                    if self.consecutive_failures[check_name] > 0:
                        self.logger.info(f"Health check recovered: {check_name}")
                    del self.consecutive_failures[check_name]
    
    def should_send_alert(self, check_name: str, current_time: datetime) -> bool:
        """Check if we should send an alert based on cooldown"""
        if check_name not in self.last_alert_times:
            return True
        
        time_since_last_alert = current_time - self.last_alert_times[check_name]
        return time_since_last_alert.total_seconds() > self.alert_cooldown
    
    async def send_alert(self, check):
        """Send alert for failed health check"""
        alert_message = f"🚨 HEALTH ALERT: {check.name} - {check.message}"
        
        # Log the alert
        if check.status == HealthStatus.CRITICAL:
            self.logger.error(alert_message)
        else:
            self.logger.warning(alert_message)
        
        # TODO: Add additional alerting mechanisms here:
        # - Email notifications
        # - Slack/Discord webhooks
        # - SMS alerts
        # - External monitoring system integration
        
        # For now, just create an alert file
        alert_file = Path(f"alerts/health_alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        alert_file.parent.mkdir(exist_ok=True)
        
        alert_data = {
            'timestamp': datetime.now().isoformat(),
            'check': check.to_dict(),
            'severity': check.status.value,
            'consecutive_failures': self.consecutive_failures.get(check.name, 1)
        }
        
        with open(alert_file, 'w') as f:
            json.dump(alert_data, f, indent=2)
    
    async def attempt_auto_recovery(self, check):
        """Attempt automatic recovery for certain types of failures"""
        check_name = check.name
        
        try:
            if check_name.startswith('service_'):
                service_name = check_name.replace('service_', '')
                self.logger.info(f"Attempting auto-recovery for service: {service_name}")
                
                # TODO: Implement service restart logic
                # This would depend on how services are managed
                # For now, just log the attempt
                self.logger.warning(f"Auto-recovery not implemented for service: {service_name}")
            
            elif check_name == 'disk_usage':
                self.logger.info("Attempting auto-recovery for disk usage")
                
                # Trigger emergency log cleanup
                try:
                    from utils.log_manager import log_manager
                    cleanup_results = log_manager.emergency_cleanup()
                    self.logger.info(f"Emergency cleanup: removed {cleanup_results['files_removed']} files")
                except Exception as e:
                    self.logger.error(f"Failed to perform emergency cleanup: {e}")
            
            elif check_name.startswith('camera_'):
                camera_id = check_name.replace('camera_', '')
                self.logger.info(f"Camera connectivity issue detected: {camera_id}")
                
                # TODO: Implement camera reconnection logic
                # This might involve restarting camera streams or checking network
                self.logger.warning(f"Auto-recovery not implemented for camera: {camera_id}")
        
        except Exception as e:
            self.logger.error(f"Auto-recovery failed for {check_name}: {e}")
    
    def update_status_file(self, health):
        """Update the health status file for external monitoring"""
        try:
            status_data = {
                'last_updated': datetime.now().isoformat(),
                'overall_status': health.overall_status.value,
                'summary': health.get_summary(),
                'details': health.to_dict()
            }
            
            with open(self.status_file, 'w') as f:
                json.dump(status_data, f, indent=2)
        
        except Exception as e:
            self.logger.error(f"Failed to update status file: {e}")
    
    def stop(self):
        """Stop the monitoring service"""
        self.logger.info("Stopping health monitoring service...")
        self.running = False


async def main():
    """Main function to run the health monitoring service"""
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='LPR Health Monitoring Service')
    parser.add_argument('--interval', type=int, default=60,
                       help='Check interval in seconds (default: 60)')
    parser.add_argument('--alert-threshold', type=int, default=3,
                       help='Consecutive failures before alert (default: 3)')
    
    args = parser.parse_args()
    
    service = HealthMonitoringService(
        check_interval=args.interval,
        alert_threshold=args.alert_threshold
    )
    
    # Handle shutdown signals
    def signal_handler(signum, frame):
        print(f"\nReceived signal {signum}, shutting down...")
        service.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await service.start()
    except KeyboardInterrupt:
        print("\nShutdown requested...")
    finally:
        service.stop()


if __name__ == "__main__":
    print("Starting LPR Health Monitoring Service...")
    print("Press Ctrl+C to stop")
    
    asyncio.run(main())