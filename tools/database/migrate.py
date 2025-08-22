#!/usr/bin/env python3
"""
Simple Database Migration Script
Handles database schema migrations using Alembic
"""
import subprocess
import sys
import os
from pathlib import Path

def run_alembic_command(args, description):
    """Run an Alembic command"""
    try:
        print(f"🔧 {description}...")
        cmd = ["./venv/bin/alembic"] + args
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent)
        
        if result.returncode == 0:
            print(f"   ✅ {description} completed")
            if result.stdout.strip():
                for line in result.stdout.strip().split('\n'):
                    if line.strip() and 'INFO' in line:
                        print(f"   {line}")
            return True
        else:
            print(f"   ❌ {description} failed")
            if result.stderr:
                print(f"   ERROR: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"   ❌ {description} failed: {e}")
        return False

def main():
    """Main migration interface"""
    if len(sys.argv) < 2:
        print("📋 Database Migration Tool")
        print("=" * 40)
        print()
        print("Commands:")
        print("  current          - Show current revision")
        print("  history          - Show migration history")
        print("  upgrade [rev]    - Upgrade to revision (default: head)")
        print("  create <message> - Create new migration")
        print("  downgrade <rev>  - Downgrade to revision")
        print()
        print("Examples:")
        print("  python migrate.py current")
        print("  python migrate.py create 'Add user preferences'")
        print("  python migrate.py upgrade")
        return
    
    command = sys.argv[1].lower()
    
    if command == "current":
        run_alembic_command(["current", "--verbose"], "Showing current revision")
        
    elif command == "history":
        run_alembic_command(["history", "--verbose"], "Showing migration history")
        
    elif command == "upgrade":
        revision = sys.argv[2] if len(sys.argv) > 2 else "head"
        run_alembic_command(["upgrade", revision], f"Upgrading to {revision}")
        
    elif command == "create":
        if len(sys.argv) < 3:
            print("❌ Please provide a migration message")
            return
        message = " ".join(sys.argv[2:])
        run_alembic_command(["revision", "--autogenerate", "-m", message], f"Creating migration: {message}")
        
    elif command == "downgrade":
        if len(sys.argv) < 3:
            print("❌ Please specify target revision")
            return
        revision = sys.argv[2]
        run_alembic_command(["downgrade", revision], f"Downgrading to {revision}")
        
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()