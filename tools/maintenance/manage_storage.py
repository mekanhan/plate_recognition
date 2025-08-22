#!/usr/bin/env python3
"""
Storage Management CLI Tool for LPR System
Provides command-line interface for storage monitoring and cleanup operations
"""
import sys
import asyncio
import argparse
from datetime import datetime

try:
    from core.storage.media_retention_manager import MediaRetentionManager
    from config.app_config import get_config
    from utils.log_manager import get_service_logger
    HAS_STORAGE_MANAGER = True
except ImportError:
    HAS_STORAGE_MANAGER = False


def print_status_line(text, status="info"):
    """Print formatted status line"""
    icons = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌",
        "cleanup": "🧹"
    }
    print(f"{icons.get(status, '•')} {text}")


def format_size(bytes_val):
    """Format byte size to human readable string"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.1f}{unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f}PB"


async def show_status(detailed=False):
    """Show storage status overview"""
    if not HAS_STORAGE_MANAGER:
        print_status_line("Storage management not available", "error")
        return 1
    
    manager = MediaRetentionManager()
    overview = await manager.get_storage_overview()
    
    print("\n" + "=" * 60)
    print("STORAGE STATUS OVERVIEW")
    print("=" * 60)
    
    # Summary
    print(f"📊 Total managed storage: {overview['total_managed_size_gb']:.1f}GB")
    print(f"📁 Total files: {overview['total_files']:,}")
    
    # Overall health
    if overview['emergency_cleanup_required']:
        print_status_line("Emergency cleanup required!", "error")
    elif overview['cleanup_recommended']:
        print_status_line("Cleanup recommended", "warning")
    else:
        print_status_line("Storage within acceptable limits", "success")
    
    # Per-policy status
    print("\n📂 Storage Policies:")
    for policy_info in overview['policies']:
        stats = policy_info['stats']
        policy = policy_info['policy']
        
        status_icon = "❌" if stats['usage_percentage'] > 95 else \
                     "⚠️" if stats['usage_percentage'] > 85 else "✅"
        
        print(f"\n  {status_icon} {policy_info['path']}:")
        print(f"     Size: {stats['total_size_gb']:.1f}GB ({stats['file_count']:,} files)")
        print(f"     Usage: {stats['usage_percentage']:.1f}% of {policy['max_size_gb']:.0f}GB limit")
        print(f"     File age: {stats['oldest_file_age_days']} - {stats['newest_file_age_days']} days")
        
        if detailed:
            available = policy['max_size_gb'] - stats['total_size_gb']
            print(f"     Available: {available:.1f}GB")
            print(f"     Priority: {stats['priority']}")
    
    # System disk usage
    if 'system_disk_usage' in overview:
        disk = overview['system_disk_usage']
        print(f"\n💾 System Disk Usage:")
        print(f"   Total: {disk.get('total_gb', 0):.1f}GB")
        print(f"   Used: {disk.get('used_gb', 0):.1f}GB ({disk.get('percentage_used', 0):.1f}%)")
        print(f"   Free: {disk.get('free_gb', 0):.1f}GB")
    
    # Cleanup history
    if detailed:
        history = overview['cleanup_history']
        print(f"\n🧹 Cleanup History:")
        print(f"   Total cleanups: {history['total_cleanups']}")
        print(f"   Files deleted: {history['total_files_deleted']:,}")
        print(f"   Space freed: {history['total_bytes_freed'] / (1024**3):.2f}GB")
        if history['last_emergency_cleanup']:
            print(f"   Last emergency: {history['last_emergency_cleanup']}")
    
    print()
    return 0


async def perform_cleanup(policy_path=None, force=False, dry_run=False):
    """Perform storage cleanup"""
    if not HAS_STORAGE_MANAGER:
        print_status_line("Storage management not available", "error")
        return 1
    
    manager = MediaRetentionManager()
    
    if dry_run:
        print_status_line("DRY RUN MODE - No files will be deleted", "info")
        # For dry run, just show what would be cleaned
        await show_status(detailed=True)
        return 0
    
    print_status_line("Starting storage cleanup...", "cleanup")
    
    if policy_path:
        print(f"   Target: {policy_path}")
    else:
        print("   Target: All policies")
    
    if force:
        print("   Mode: Force cleanup")
    else:
        print("   Mode: Standard cleanup")
    
    try:
        result = await manager.perform_cleanup(
            policy_path=policy_path,
            force=force
        )
        
        print(f"\n🎯 Cleanup Results:")
        print(f"   Policies processed: {len(result['policies_processed'])}")
        print(f"   Files deleted: {result['total_files_deleted']:,}")
        print(f"   Space freed: {result['total_bytes_freed'] / (1024**3):.2f}GB")
        print(f"   Time taken: {result['cleanup_time_seconds']:.1f}s")
        
        if result['emergency_cleanup_performed']:
            print_status_line("Emergency cleanup was performed", "warning")
        
        # Detailed results per policy
        for policy_result in result['policies_processed']:
            print(f"\n  📁 {policy_result['path']}:")
            print(f"     Files deleted: {policy_result['files_deleted']:,}")
            print(f"     Space freed: {policy_result['bytes_freed'] / (1024**3):.2f}GB")
            if policy_result['emergency']:
                print("     🚨 Emergency cleanup performed")
        
        if result['total_files_deleted'] > 0:
            print_status_line("Cleanup completed successfully", "success")
        else:
            print_status_line("No cleanup was needed", "info")
        
        return 0
        
    except Exception as e:
        print_status_line(f"Cleanup failed: {e}", "error")
        return 1


async def monitor_storage(interval=300):
    """Monitor storage continuously"""
    if not HAS_STORAGE_MANAGER:
        print_status_line("Storage management not available", "error")
        return 1
    
    print_status_line(f"Starting storage monitoring (checking every {interval}s)", "info")
    print("Press Ctrl+C to stop\n")
    
    manager = MediaRetentionManager()
    
    try:
        while True:
            overview = await manager.get_storage_overview()
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] Storage: {overview['total_managed_size_gb']:.1f}GB, "
                  f"Files: {overview['total_files']:,}")
            
            # Check for issues
            if overview['emergency_cleanup_required']:
                print_status_line("Emergency cleanup required!", "error")
                await manager.perform_cleanup(force=True)
            elif overview['cleanup_recommended']:
                print_status_line("Cleanup recommended", "warning")
            
            await asyncio.sleep(interval)
            
    except KeyboardInterrupt:
        print_status_line("Monitoring stopped", "info")
        return 0


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description='LPR Storage Management Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s status                    # Show storage status
  %(prog)s status --detailed         # Show detailed status
  %(prog)s cleanup                   # Standard cleanup
  %(prog)s cleanup --force           # Force cleanup all policies
  %(prog)s cleanup --policy recordings  # Cleanup specific policy
  %(prog)s cleanup --dry-run         # Show what would be cleaned
  %(prog)s monitor                   # Monitor continuously
  %(prog)s monitor --interval 600    # Monitor every 10 minutes
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show storage status')
    status_parser.add_argument('--detailed', action='store_true',
                              help='Show detailed information')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Perform storage cleanup')
    cleanup_parser.add_argument('--policy', type=str,
                               help='Cleanup specific policy path only')
    cleanup_parser.add_argument('--force', action='store_true',
                               help='Force cleanup regardless of thresholds')
    cleanup_parser.add_argument('--dry-run', action='store_true',
                               help='Show what would be cleaned without doing it')
    
    # Monitor command
    monitor_parser = subparsers.add_parser('monitor', help='Monitor storage continuously')
    monitor_parser.add_argument('--interval', type=int, default=300,
                               help='Check interval in seconds (default: 300)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Check if storage manager is available
    if not HAS_STORAGE_MANAGER:
        print_status_line("Storage management system not available", "error")
        print("Make sure all dependencies are installed and configuration is valid.")
        return 1
    
    # Execute command
    try:
        if args.command == 'status':
            return asyncio.run(show_status(detailed=args.detailed))
        elif args.command == 'cleanup':
            return asyncio.run(perform_cleanup(
                policy_path=args.policy,
                force=args.force,
                dry_run=args.dry_run
            ))
        elif args.command == 'monitor':
            return asyncio.run(monitor_storage(interval=args.interval))
        else:
            parser.print_help()
            return 1
            
    except KeyboardInterrupt:
        print_status_line("Operation cancelled", "info")
        return 0
    except Exception as e:
        print_status_line(f"Error: {e}", "error")
        return 1


if __name__ == "__main__":
    sys.exit(main())