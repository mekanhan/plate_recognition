#!/usr/bin/env python3
"""
Manual Log Cleanup Tool for LPR System
Can be run manually or via cron for automatic log maintenance
"""
import sys
import argparse
from utils.log_manager import log_manager


def main():
    parser = argparse.ArgumentParser(description='LPR System Log Cleanup Tool')
    parser.add_argument('--stats', action='store_true', 
                       help='Show log statistics only')
    parser.add_argument('--cleanup', action='store_true',
                       help='Perform regular cleanup (removes old files)')
    parser.add_argument('--emergency', action='store_true',
                       help='Perform emergency cleanup (removes 50% of files)')
    parser.add_argument('--force', action='store_true',
                       help='Skip confirmation prompts')
    
    args = parser.parse_args()
    
    if args.stats:
        show_stats()
    elif args.cleanup:
        perform_cleanup(args.force)
    elif args.emergency:
        perform_emergency_cleanup(args.force)
    else:
        # Default action: show stats and ask what to do
        show_stats()
        prompt_action()


def show_stats():
    """Display current log statistics"""
    stats = log_manager.get_log_stats()
    
    print("=" * 50)
    print("LPR SYSTEM LOG STATISTICS")
    print("=" * 50)
    print(f"Total log files: {stats['total_log_files']}")
    print(f"Total size: {stats['total_size_mb']:.1f} MB")
    print()
    
    print("Disk Usage:")
    disk = stats['disk_usage']
    print(f"  Total space: {disk['total_gb']:.1f} GB")
    print(f"  Used space: {disk['used_gb']:.1f} GB ({disk['usage_percent']*100:.1f}%)")
    print(f"  Free space: {disk['free_gb']:.1f} GB")
    
    if disk['above_threshold']:
        print("  ⚠️  WARNING: Disk usage above 85% threshold!")
    
    print()
    print("Services breakdown:")
    for service, info in stats['services'].items():
        print(f"  {service}: {info['file_count']} files, {info['total_size_mb']:.1f} MB")
    
    print()
    if stats['cleanup_recommended']:
        print("🧹 RECOMMENDATION: Log cleanup is recommended")
        print("   Run with --cleanup to remove old files")
        if disk['above_threshold']:
            print("   Run with --emergency for immediate space recovery")
    else:
        print("✅ Log files are within normal limits")


def perform_cleanup(force=False):
    """Perform regular cleanup"""
    if not force:
        stats = log_manager.get_log_stats()
        print(f"About to clean up logs older than {log_manager.retention_days} days")
        print(f"Current: {stats['total_log_files']} files, {stats['total_size_mb']:.1f} MB")
        
        response = input("Continue? (y/N): ").strip().lower()
        if response != 'y':
            print("Cleanup cancelled")
            return
    
    print("Performing log cleanup...")
    results = log_manager.monitor_and_cleanup()
    
    regular_removed = sum(results['regular_cleanup'].values())
    print(f"Regular cleanup: removed {regular_removed} old files")
    
    if 'emergency_cleanup' in results:
        print(f"Emergency cleanup also performed: removed {results['files_removed']} files")
    
    final_stats = results['final_stats']
    print(f"After cleanup: {final_stats['total_log_files']} files, {final_stats['total_size_mb']:.1f} MB")
    
    if final_stats['cleanup_recommended']:
        print("⚠️  More cleanup may be needed - consider emergency cleanup")
    else:
        print("✅ Cleanup completed successfully")


def perform_emergency_cleanup(force=False):
    """Perform emergency cleanup"""
    if not force:
        print("⚠️  EMERGENCY CLEANUP WARNING")
        print("This will remove 50% of all log files (oldest first)")
        print("This action cannot be undone!")
        
        response = input("Are you sure? Type 'YES' to continue: ").strip()
        if response != 'YES':
            print("Emergency cleanup cancelled")
            return
    
    print("Performing emergency cleanup...")
    results = log_manager.emergency_cleanup()
    
    print(f"Emergency cleanup completed:")
    print(f"  Files removed: {results['files_removed']}")
    print(f"  Files remaining: {results['files_remaining']}")
    
    # Show final stats
    final_stats = log_manager.get_log_stats()
    print(f"After cleanup: {final_stats['total_log_files']} files, {final_stats['total_size_mb']:.1f} MB")


def prompt_action():
    """Interactive prompt for action"""
    print()
    print("What would you like to do?")
    print("1. Regular cleanup (remove old files)")
    print("2. Emergency cleanup (remove 50% of files)")
    print("3. Exit")
    
    try:
        choice = input("Enter choice (1-3): ").strip()
        
        if choice == '1':
            perform_cleanup()
        elif choice == '2':
            perform_emergency_cleanup()
        elif choice == '3':
            print("Exiting...")
        else:
            print("Invalid choice")
    except KeyboardInterrupt:
        print("\nExiting...")


if __name__ == "__main__":
    main()