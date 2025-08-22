#!/usr/bin/env python3
"""
Database Migration Manager
Unified management of database schema migrations using Alembic
"""
import asyncio
import sys
import os
from pathlib import Path
import subprocess
from typing import Optional

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from database.service import DatabaseService
from database.models import Base

class MigrationManager:
    """Manages database migrations with Alembic integration"""
    
    def __init__(self):
        self.db_path = Path("data/license_plates.db")
        self.alembic_ini = Path("alembic.ini")
        self.db_service = DatabaseService()
    
    def run_command(self, command: list, description: str) -> bool:
        """Run a command and capture output"""
        try:
            print(f"🔧 {description}...")
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent
            )
            
            if result.returncode == 0:
                print(f"   ✅ {description} completed successfully")
                if result.stdout.strip():
                    for line in result.stdout.strip().split('\n'):
                        if line.strip():
                            print(f"   {line}")
                return True
            else:
                print(f"   ❌ {description} failed")
                if result.stderr:
                    for line in result.stderr.strip().split('\n'):
                        if line.strip():
                            print(f"   ERROR: {line}")
                return False
                
        except Exception as e:
            print(f"   ❌ {description} failed: {e}")
            return False
    
    def check_alembic_setup(self) -> bool:
        """Check if Alembic is properly set up"""
        if not self.alembic_ini.exists():
            print("❌ Alembic not initialized. Run: alembic init migrations")
            return False
        
        migrations_dir = Path("migrations")
        if not migrations_dir.exists():
            print("❌ Migrations directory not found")
            return False
        
        print("✅ Alembic setup verified")
        return True
    
    def get_current_revision(self) -> Optional[str]:
        """Get current database revision"""
        try:
            result = subprocess.run(
                ["./venv/bin/alembic", "current"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent
            )
            
            if result.returncode == 0 and result.stdout.strip():
                # Extract revision from output like "INFO  [alembic.runtime.migration] Context impl SQLiteImpl."
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'Current revision' in line or '(head)' in line:
                        return line.split()[-1].replace('(head)', '').strip()
                return "none"
            return None
        except Exception:
            return None
    
    def get_head_revision(self) -> Optional[str]:
        """Get the latest migration revision"""
        try:
            result = subprocess.run(
                ["./venv/bin/alembic", "heads"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent
            )
            
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().split('\n')[0].split()[0]
            return None
        except Exception:
            return None
    
    def create_migration(self, message: str, autogenerate: bool = True) -> bool:
        """Create a new migration"""
        command = ["./venv/bin/alembic", "revision"]
        if autogenerate:
            command.append("--autogenerate")
        command.extend(["-m", message])
        
        return self.run_command(command, f"Creating migration: {message}")
    
    def upgrade_database(self, revision: str = "head") -> bool:
        """Upgrade database to specified revision"""
        command = ["./venv/bin/alembic", "upgrade", revision]
        return self.run_command(command, f"Upgrading database to {revision}")
    
    def downgrade_database(self, revision: str) -> bool:
        """Downgrade database to specified revision"""
        command = ["./venv/bin/alembic", "downgrade", revision]
        return self.run_command(command, f"Downgrading database to {revision}")
    
    def show_history(self) -> bool:
        """Show migration history"""
        command = ["./venv/bin/alembic", "history", "--verbose"]
        return self.run_command(command, "Showing migration history")
    
    def show_current(self) -> bool:
        """Show current revision"""
        command = ["./venv/bin/alembic", "current", "--verbose"]
        return self.run_command(command, "Showing current revision")
    
    async def backup_database(self) -> Optional[Path]:
        """Create a backup of the current database"""
        if not self.db_path.exists():
            print("❌ Database file not found")
            return None
        
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = Path(f"data/backups/license_plates_backup_{timestamp}.db")
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            import shutil
            shutil.copy2(self.db_path, backup_path)
            
            print(f"✅ Database backed up to {backup_path}")
            return backup_path
            
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return None
    
    async def validate_schema(self) -> bool:
        """Validate that the database schema matches the models"""
        try:
            print("🔍 Validating database schema...")
            
            # Try to create a connection and verify tables
            await self.db_service.init_db()
            
            # Check if all expected tables exist
            from sqlalchemy import inspect
            inspector = inspect(self.db_service.engine.sync_engine)
            actual_tables = set(inspector.get_table_names())
            
            expected_tables = set(Base.metadata.tables.keys())
            
            missing_tables = expected_tables - actual_tables
            extra_tables = actual_tables - expected_tables
            
            if missing_tables:
                print(f"   ⚠️  Missing tables: {missing_tables}")
            
            if extra_tables:
                print(f"   ℹ️  Extra tables (may be legacy): {extra_tables}")
            
            if not missing_tables:
                print("   ✅ All required tables present")
                return True
            else:
                print("   ❌ Schema validation failed")
                return False
                
        except Exception as e:
            print(f"   ❌ Schema validation failed: {e}")
            return False
        finally:
            await self.db_service.close()
    
    def stamp_database(self, revision: str = "head") -> bool:
        """Mark database as being at a particular revision without running migrations"""
        command = ["./venv/bin/alembic", "stamp", revision]
        return self.run_command(command, f"Stamping database as {revision}")
    
    async def migrate_from_legacy(self) -> bool:
        """Migrate from legacy ad-hoc schema updates to Alembic"""
        print("🔄 Migrating from legacy schema management to Alembic...")
        
        # Check if database exists and has data
        if not self.db_path.exists():
            print("   ℹ️  No existing database found, will create new one")
            return await self.initialize_new_database()
        
        # Create backup
        backup = await self.backup_database()
        if not backup:
            print("   ❌ Cannot proceed without backup")
            return False
        
        try:
            # Validate current schema
            schema_valid = await self.validate_schema()
            
            if schema_valid:
                # Database appears to be up to date, stamp it
                print("   ✅ Database schema is current, stamping as head revision")
                return self.stamp_database("head")
            else:
                # Schema needs updates, run upgrade
                print("   🔄 Database schema needs updates, running migration")
                return self.upgrade_database("head")
                
        except Exception as e:
            print(f"   ❌ Migration failed: {e}")
            print(f"   💾 Database backup available at: {backup}")
            return False
    
    async def initialize_new_database(self) -> bool:
        """Initialize a new database with current schema"""
        print("🆕 Initializing new database...")
        
        try:
            # Create database directory
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Run upgrade to create all tables
            if self.upgrade_database("head"):
                print("   ✅ New database initialized successfully")
                return True
            else:
                print("   ❌ Database initialization failed")
                return False
                
        except Exception as e:
            print(f"   ❌ Database initialization failed: {e}")
            return False

async def main():
    """Main migration management interface"""
    manager = MigrationManager()
    
    if len(sys.argv) < 2:
        print("🗄️  Database Migration Manager")
        print("=" * 50)
        print()
        print("Available commands:")
        print("  init          - Initialize new database")
        print("  migrate       - Migrate from legacy to Alembic")
        print("  upgrade       - Upgrade database to latest")
        print("  create <msg>  - Create new migration")
        print("  history       - Show migration history")
        print("  current       - Show current revision")
        print("  validate      - Validate schema")
        print("  backup        - Create database backup")
        print("  stamp <rev>   - Mark database as specific revision")
        print()
        print("Examples:")
        print("  python db_migration_manager.py migrate")
        print("  python db_migration_manager.py create 'Add new column'")
        print("  python db_migration_manager.py upgrade")
        return
    
    command = sys.argv[1].lower()
    
    # Check Alembic setup for most commands
    if command not in ['init'] and not manager.check_alembic_setup():
        return
    
    if command == "init":
        success = await manager.initialize_new_database()
        
    elif command == "migrate":
        success = await manager.migrate_from_legacy()
        
    elif command == "upgrade":
        revision = sys.argv[2] if len(sys.argv) > 2 else "head"
        success = manager.upgrade_database(revision)
        
    elif command == "create":
        if len(sys.argv) < 3:
            print("❌ Please provide a migration message")
            return
        message = " ".join(sys.argv[2:])
        success = manager.create_migration(message, autogenerate=True)
        
    elif command == "history":
        success = manager.show_history()
        
    elif command == "current":
        success = manager.show_current()
        
    elif command == "validate":
        success = await manager.validate_schema()
        
    elif command == "backup":
        backup_path = await manager.backup_database()
        success = backup_path is not None
        
    elif command == "stamp":
        revision = sys.argv[2] if len(sys.argv) > 2 else "head"
        success = manager.stamp_database(revision)
        
    elif command == "downgrade":
        if len(sys.argv) < 3:
            print("❌ Please specify target revision")
            return
        revision = sys.argv[2]
        success = manager.downgrade_database(revision)
        
    else:
        print(f"❌ Unknown command: {command}")
        return
    
    if success:
        print("\n🎉 Operation completed successfully!")
    else:
        print("\n❌ Operation failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())