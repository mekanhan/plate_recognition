#!/usr/bin/env python3
"""
Configuration Validation Tool for LPR System
Validates configuration settings and checks system readiness
"""
import sys
import argparse
from pathlib import Path
from config.app_config import load_config


def main():
    parser = argparse.ArgumentParser(description='LPR System Configuration Validator')
    parser.add_argument('--env-file', help='Path to .env file to load')
    parser.add_argument('--check-paths', action='store_true',
                       help='Check if all configured paths exist')
    parser.add_argument('--check-ports', action='store_true',
                       help='Check if configured ports are available')
    parser.add_argument('--show-config', action='store_true',
                       help='Show full configuration (without secrets)')
    parser.add_argument('--fix-issues', action='store_true',
                       help='Attempt to fix configuration issues automatically')
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        config = load_config(args.env_file)
        print("✅ Configuration loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return 1
    
    # Validate configuration
    validation = config.validate_config()
    
    print("\n" + "="*60)
    print("CONFIGURATION VALIDATION RESULTS")
    print("="*60)
    
    if validation['valid']:
        print("✅ Configuration is valid")
    else:
        print("❌ Configuration has issues")
    
    # Show issues
    if validation['issues']:
        print("\n🚨 Issues found:")
        for issue in validation['issues']:
            print(f"   • {issue}")
    
    # Show warnings
    if validation.get('warnings'):
        print("\n⚠️  Warnings:")
        for warning in validation['warnings']:
            print(f"   • {warning}")
    
    # Additional checks
    if args.check_paths:
        check_paths(config)
    
    if args.check_ports:
        check_ports(config)
    
    if args.show_config:
        show_config(config)
    
    if args.fix_issues and validation['issues']:
        fix_issues(config, validation['issues'])
    
    return 0 if validation['valid'] else 1


def check_paths(config):
    """Check if all configured paths exist and are accessible"""
    print("\n" + "="*40)
    print("PATH VALIDATION")
    print("="*40)
    
    paths_to_check = [
        ("Database path", Path(config.database.path).parent),
        ("Database backup dir", Path(config.database.backup_dir)),
        ("Log directory", Path(config.logging.log_dir)),
        ("Recordings directory", Path(config.storage.recordings_dir)),
        ("Detections directory", Path(config.storage.detections_dir)),
        ("Models directory", Path(config.storage.models_dir)),
        ("Temp directory", Path(config.storage.temp_dir)),
        ("YOLO model file", Path(config.ai.yolo_model_path)),
    ]
    
    for name, path in paths_to_check:
        if path.exists():
            if path.is_file():
                print(f"✅ {name}: {path} (file exists)")
            else:
                print(f"✅ {name}: {path} (directory exists)")
        else:
            if name.endswith("file"):
                print(f"❌ {name}: {path} (file not found)")
            else:
                print(f"⚠️  {name}: {path} (directory will be created)")


def check_ports(config):
    """Check if configured ports are available"""
    print("\n" + "="*40)
    print("PORT AVAILABILITY")
    print("="*40)
    
    import socket
    
    ports_to_check = [
        ("Main API", config.services.main_api_port),
        ("Recording API", config.services.recording_api_port),
        ("Frontend", config.services.frontend_port),
    ]
    
    for name, port in ports_to_check:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                if result == 0:
                    print(f"❌ {name}: Port {port} is already in use")
                else:
                    print(f"✅ {name}: Port {port} is available")
        except Exception as e:
            print(f"⚠️  {name}: Port {port} check failed: {e}")


def show_config(config):
    """Show full configuration (without secrets)"""
    print("\n" + "="*40)
    print("CONFIGURATION DETAILS")
    print("="*40)
    
    import json
    config_dict = config.to_dict()
    print(json.dumps(config_dict, indent=2))


def fix_issues(config, issues):
    """Attempt to fix configuration issues automatically"""
    print("\n" + "="*40)
    print("FIXING CONFIGURATION ISSUES")
    print("="*40)
    
    for issue in issues:
        print(f"\nAttempting to fix: {issue}")
        
        if "directory does not exist" in issue:
            # Extract directory path and create it
            try:
                path_start = issue.find(": ") + 2
                dir_path = Path(issue[path_start:])
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"✅ Created directory: {dir_path}")
            except Exception as e:
                print(f"❌ Failed to create directory: {e}")
        
        elif "model file not found" in issue:
            print("⚠️  Model file issue - please download or configure correct path")
            print("   Check README for model download instructions")
        
        elif "Port conflicts" in issue:
            print("⚠️  Port conflicts - please update configuration manually")
            print("   Use different ports in .env file")
        
        else:
            print(f"⚠️  Cannot auto-fix: {issue}")


def create_sample_env():
    """Create a sample .env file if it doesn't exist"""
    env_file = Path(".env")
    if not env_file.exists():
        print("Creating sample .env file...")
        try:
            import shutil
            shutil.copy(".env.example", ".env")
            print("✅ Created .env file from template")
            print("   Please edit .env file to customize settings")
        except FileNotFoundError:
            print("❌ .env.example not found - cannot create sample .env")
        except Exception as e:
            print(f"❌ Failed to create .env: {e}")


if __name__ == "__main__":
    sys.exit(main())