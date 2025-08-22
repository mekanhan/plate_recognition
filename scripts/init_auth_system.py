#!/usr/bin/env python3
"""
Authentication System Initialization Script
Creates database tables and default admin user
"""
import sys
import asyncio
import os
from pathlib import Path
import getpass

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db_config import db_config
from database.models import Base
from database.auth_models import User, AuditLog
from security.auth_manager import security_manager, UserRole

async def create_auth_tables():
    """Create authentication tables"""
    try:
        engine = await db_config.init_engine()
        
        async with engine.begin() as conn:
            # Create all tables including auth tables
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ Authentication tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create authentication tables: {e}")
        return False

async def create_admin_user(username: str, email: str, password: str):
    """Create default admin user"""
    try:
        async with db_config.get_session() as session:
            from sqlalchemy import select
            
            # Check if admin user already exists
            result = await session.execute(
                select(User).where(User.username == username)
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print(f"⚠️  Admin user '{username}' already exists")
                return False
            
            # Validate password
            password_validation = security_manager.validate_password_strength(password)
            if not password_validation['valid']:
                print("❌ Password validation failed:")
                for error in password_validation['errors']:
                    print(f"   - {error}")
                return False
            
            # Create admin user
            password_hash = security_manager.hash_password(password)
            
            admin_user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                first_name="System",
                last_name="Administrator",
                role=UserRole.ADMIN.value,
                is_active=True,
                is_verified=True
            )
            
            session.add(admin_user)
            await session.commit()
            await session.refresh(admin_user)
            
            # Log admin user creation
            audit_log = AuditLog(
                user_id=admin_user.id,
                event_type='admin_user_created',
                event_category='admin',
                description=f"Initial admin user created: {username}",
                severity='info',
                success=True
            )
            session.add(audit_log)
            await session.commit()
            
            print(f"✅ Admin user '{username}' created successfully")
            print(f"   Email: {email}")
            print(f"   Role: {UserRole.ADMIN.value}")
            return True
            
    except Exception as e:
        print(f"❌ Failed to create admin user: {e}")
        return False

async def check_auth_system():
    """Check authentication system status"""
    try:
        print("🔍 Checking authentication system status...")
        
        # Check database connection
        health = await db_config.health_check()
        if health['status'] != 'healthy':
            print("❌ Database connection failed")
            return False
        
        print("✅ Database connection healthy")
        
        # Check if auth tables exist
        auth_tables = ['users', 'api_keys', 'user_sessions', 'audit_logs', 'security_events']
        existing_tables = health.get('tables', [])
        
        missing_tables = [table for table in auth_tables if table not in existing_tables]
        if missing_tables:
            print(f"⚠️  Missing auth tables: {missing_tables}")
            return False
        
        print("✅ All authentication tables present")
        
        # Check for admin users
        async with db_config.get_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.role == UserRole.ADMIN.value)
            )
            admin_users = result.scalars().all()
            
            if not admin_users:
                print("⚠️  No admin users found")
                return False
            
            print(f"✅ Found {len(admin_users)} admin user(s)")
            for admin in admin_users:
                print(f"   - {admin.username} ({admin.email})")
        
        return True
        
    except Exception as e:
        print(f"❌ Authentication system check failed: {e}")
        return False

def get_user_input():
    """Get user input for admin account creation"""
    print("\n📝 Admin User Creation")
    print("=" * 30)
    
    username = input("Enter admin username: ").strip()
    if not username:
        print("❌ Username cannot be empty")
        return None
    
    email = input("Enter admin email: ").strip()
    if not email or '@' not in email:
        print("❌ Valid email required")
        return None
    
    password = getpass.getpass("Enter admin password: ").strip()
    if not password:
        print("❌ Password cannot be empty")
        return None
    
    confirm_password = getpass.getpass("Confirm admin password: ").strip()
    if password != confirm_password:
        print("❌ Passwords do not match")
        return None
    
    return username, email, password

async def main():
    """Main initialization function"""
    print("🔒 LPR AUTHENTICATION SYSTEM INITIALIZATION")
    print("=" * 50)
    
    # Check if system is already initialized
    try:
        system_ok = await check_auth_system()
        if system_ok:
            print("\n✅ Authentication system is already initialized and healthy")
            response = input("\nReinitialize anyway? (y/N): ").strip().lower()
            if response != 'y':
                print("Exiting...")
                return 0
    except:
        print("⚠️  Authentication system not initialized")
    
    # Create database tables
    print("\n🏗️  Creating authentication tables...")
    if not await create_auth_tables():
        print("❌ Failed to create tables. Exiting.")
        return 1
    
    # Get admin user details
    user_input = get_user_input()
    if not user_input:
        print("❌ Invalid input. Exiting.")
        return 1
    
    username, email, password = user_input
    
    # Create admin user
    print(f"\n👤 Creating admin user '{username}'...")
    if not await create_admin_user(username, email, password):
        print("❌ Failed to create admin user. Exiting.")
        return 1
    
    # Final verification
    print("\n🔍 Verifying initialization...")
    if await check_auth_system():
        print("\n🎉 AUTHENTICATION SYSTEM INITIALIZED SUCCESSFULLY!")
        print("\nNext steps:")
        print("1. Restart the LPR services: python3 start_lpr.py")
        print("2. Access authentication endpoints at http://localhost:8001/docs")
        print("3. Login with your admin credentials")
        return 0
    else:
        print("\n❌ Initialization verification failed")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nInitialization cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Initialization failed: {e}")
        sys.exit(1)
    finally:
        # Ensure database connections are closed
        try:
            asyncio.run(db_config.close())
        except:
            pass