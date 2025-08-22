#!/usr/bin/env python3
"""
Media Retention Service for LPR System
Background service for automated storage management and cleanup
"""
import asyncio
import signal
import sys
from datetime import datetime

try:
    from core.storage.media_retention_manager import MediaRetentionManager
    from config.app_config import get_config
    from utils.log_manager import get_service_logger
    HAS_CONFIG = True
except ImportError as e:
    print(f"Import error: {e}")
    HAS_CONFIG = False
    import logging
    
    # Create a dummy class for when imports fail
    class MediaRetentionManager:
        def __init__(self):
            self.logger = logging.getLogger('dummy_retention_manager')
            self.logger.error("MediaRetentionManager not available - import failed")
        
        async def get_storage_overview(self):
            return {"error": "Storage management not available"}
        
        async def perform_cleanup(self, **kwargs):
            return {"error": "Storage management not available"}


class MediaRetentionService:
    """
    Background service for media retention management
    """
    
    def __init__(self):
        if HAS_CONFIG:
            self.config = get_config()
            self.logger = get_service_logger('media_retention_service')
        else:
            self.config = None
            self.logger = logging.getLogger('media_retention_service')
        
        self.retention_manager = MediaRetentionManager()
        self.running = False
    
    async def start(self):
        """Start the media retention service"""
        self.running = True
        self.logger.info("Media retention service starting...")
        
        # Initial storage assessment
        await self.perform_initial_assessment()
        
        # Start monitoring
        await self.retention_manager.start_monitoring()
    
    async def perform_initial_assessment(self):
        """Perform initial storage assessment and emergency cleanup if needed"""
        try:
            self.logger.info("Performing initial storage assessment...")
            
            overview = await self.retention_manager.get_storage_overview()
            
            self.logger.info(f"Total managed storage: {overview['total_managed_size_gb']:.2f}GB")
            self.logger.info(f"Total files: {overview['total_files']:,}")
            
            # Report on each policy
            for policy_info in overview['policies']:
                stats = policy_info['stats']
                policy = policy_info['policy']
                
                self.logger.info(
                    f"Storage: {policy_info['path']} - "
                    f"{stats['total_size_gb']:.2f}GB ({stats['file_count']:,} files), "
                    f"Usage: {stats['usage_percentage']:.1f}% of {policy['max_size_gb']}GB limit"
                )
                
                if stats['requires_cleanup']:
                    self.logger.warning(f"Cleanup required for {policy_info['path']}")
            
            # Perform emergency cleanup if required
            if overview['emergency_cleanup_required']:
                self.logger.warning("Emergency cleanup required! Starting immediate cleanup...")
                await self.retention_manager.perform_cleanup(force=True)
            elif overview['cleanup_recommended']:
                self.logger.info("Standard cleanup recommended, starting cleanup...")
                await self.retention_manager.perform_cleanup(force=False)
            
        except Exception as e:
            self.logger.error(f"Error in initial assessment: {e}")
    
    def stop(self):
        """Stop the service"""
        self.logger.info("Stopping media retention service...")
        self.running = False
        self.retention_manager.stop_monitoring()


async def main():
    """Main function to run the media retention service"""
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='LPR Media Retention Service')
    parser.add_argument('--initial-cleanup', action='store_true',
                       help='Perform initial cleanup and exit')
    parser.add_argument('--force-cleanup', action='store_true',
                       help='Force cleanup regardless of thresholds')
    parser.add_argument('--policy-path', type=str,
                       help='Cleanup specific policy path only')
    parser.add_argument('--status', action='store_true',
                       help='Show storage status and exit')
    
    args = parser.parse_args()
    
    service = MediaRetentionService()
    
    # Handle different modes
    if args.status:
        # Show status and exit
        try:
            overview = await service.retention_manager.get_storage_overview()
            
            print("\n" + "="*60)
            print("MEDIA STORAGE STATUS")
            print("="*60)
            
            print(f"Total managed storage: {overview['total_managed_size_gb']:.2f}GB")
            print(f"Total files: {overview['total_files']:,}")
            print(f"Cleanup recommended: {overview['cleanup_recommended']}")
            print(f"Emergency cleanup required: {overview['emergency_cleanup_required']}")
            
            print("\nPer-Policy Status:")
            for policy_info in overview['policies']:
                stats = policy_info['stats']
                policy = policy_info['policy']
                
                print(f"\n📁 {policy_info['path']}:")
                print(f"   Size: {stats['total_size_gb']:.2f}GB ({stats['file_count']:,} files)")
                print(f"   Usage: {stats['usage_percentage']:.1f}% of {policy['max_size_gb']}GB limit")
                print(f"   Age: {stats['oldest_file_age_days']} - {stats['newest_file_age_days']} days")
                print(f"   Status: {'⚠️ Cleanup Required' if stats['requires_cleanup'] else '✅ OK'}")
            
            # System disk usage
            if 'system_disk_usage' in overview:
                disk = overview['system_disk_usage']
                print(f"\nSystem Disk Usage:")
                print(f"   Total: {disk.get('total_gb', 0):.1f}GB")
                print(f"   Used: {disk.get('used_gb', 0):.1f}GB ({disk.get('percentage_used', 0):.1f}%)")
                print(f"   Free: {disk.get('free_gb', 0):.1f}GB")
            
            # Cleanup history
            history = overview['cleanup_history']
            print(f"\nCleanup History:")
            print(f"   Total cleanups: {history['total_cleanups']}")
            print(f"   Files deleted: {history['total_files_deleted']:,}")
            print(f"   Space freed: {history['total_bytes_freed'] / (1024**3):.2f}GB")
            if history['last_emergency_cleanup']:
                print(f"   Last emergency: {history['last_emergency_cleanup']}")
            
        except Exception as e:
            print(f"Error getting status: {e}")
            return 1
        
        return 0
    
    elif args.initial_cleanup or args.force_cleanup:
        # Perform cleanup and exit
        try:
            print("Starting media storage cleanup...")
            result = await service.retention_manager.perform_cleanup(
                policy_path=args.policy_path,
                force=args.force_cleanup
            )
            
            print(f"\nCleanup Results:")
            print(f"  Policies processed: {len(result['policies_processed'])}")
            print(f"  Files deleted: {result['total_files_deleted']:,}")
            print(f"  Space freed: {result['total_bytes_freed'] / (1024**3):.2f}GB")
            print(f"  Time taken: {result['cleanup_time_seconds']:.1f}s")
            
            if result['emergency_cleanup_performed']:
                print("  ⚠️ Emergency cleanup was performed")
            
            for policy_result in result['policies_processed']:
                print(f"\n  📁 {policy_result['path']}:")
                print(f"     Files deleted: {policy_result['files_deleted']:,}")
                print(f"     Space freed: {policy_result['bytes_freed'] / (1024**3):.2f}GB")
                if policy_result['emergency']:
                    print("     🚨 Emergency cleanup")
            
        except Exception as e:
            print(f"Error during cleanup: {e}")
            return 1
        
        return 0
    
    else:
        # Run as background service
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
    
    return 0


if __name__ == "__main__":
    print("Starting LPR Media Retention Service...")
    print("Press Ctrl+C to stop")
    
    exit_code = asyncio.run(main())
    sys.exit(exit_code)