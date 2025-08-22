#!/usr/bin/env python3
"""
Log Cleanup Service for LPR System
Runs automatic log rotation and cleanup to prevent disk space issues
"""
import time
import asyncio
import signal
import sys
from datetime import datetime
from utils.log_manager import log_manager, get_service_logger


class LogCleanupService:
    """
    Background service for automatic log management
    """
    
    def __init__(self, cleanup_interval: int = 3600):  # 1 hour default
        self.cleanup_interval = cleanup_interval
        self.running = False
        self.logger = get_service_logger('log_cleanup')
        
    async def start(self):
        """
        Start the log cleanup service
        """
        self.running = True
        self.logger.info("Log cleanup service starting...")
        
        # Initial cleanup
        await self.perform_cleanup()
        
        # Schedule regular cleanups
        while self.running:
            try:
                await asyncio.sleep(self.cleanup_interval)
                if self.running:
                    await self.perform_cleanup()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in cleanup cycle: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
        
        self.logger.info("Log cleanup service stopped")
    
    async def perform_cleanup(self):
        """
        Perform log cleanup and monitoring
        """
        try:
            self.logger.info("Starting log cleanup cycle...")
            
            # Get current stats
            stats = log_manager.get_log_stats()
            self.logger.info(f"Current log stats: {stats['total_log_files']} files, "
                           f"{stats['total_size_mb']} MB, "
                           f"disk usage: {stats['disk_usage']['usage_percent']*100:.1f}%")
            
            # Perform cleanup
            results = log_manager.monitor_and_cleanup()
            
            # Log results
            regular_removed = sum(results['regular_cleanup'].values())
            if regular_removed > 0:
                self.logger.info(f"Regular cleanup: removed {regular_removed} old files")
            
            if 'emergency_cleanup' in results:
                self.logger.warning(f"Emergency cleanup performed: "
                                  f"removed {results['files_removed']} files due to disk usage")
            
            # Check final state
            final_stats = results['final_stats']
            if final_stats['cleanup_recommended']:
                self.logger.warning("Log cleanup recommended: high disk usage or file count")
            
            self.logger.info("Log cleanup cycle completed")
            
        except Exception as e:
            self.logger.error(f"Error during log cleanup: {e}")
    
    def stop(self):
        """
        Stop the cleanup service
        """
        self.logger.info("Stopping log cleanup service...")
        self.running = False


async def main():
    """
    Main function to run the log cleanup service
    """
    service = LogCleanupService()
    
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
    # Allow custom cleanup interval
    interval = 3600  # Default 1 hour
    if len(sys.argv) > 1:
        try:
            interval = int(sys.argv[1])
            print(f"Using cleanup interval: {interval} seconds")
        except ValueError:
            print("Invalid interval, using default 1 hour")
    
    print("Starting LPR Log Cleanup Service...")
    print("Press Ctrl+C to stop")
    
    asyncio.run(main())