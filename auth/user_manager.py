"""
Simple User Management System
For production, replace with proper database-backed user storage
"""
import os
import json
import hashlib
from typing import Optional, Dict, List
from datetime import datetime
from .models import User, UserRole, CreateUserRequest
from pathlib import Path


class SimpleUserManager:
    """Simple file-based user management (replace with database in production)"""
    
    def __init__(self, users_file: str = "data/users.json"):
        self.users_file = Path(users_file)
        self.users_file.parent.mkdir(exist_ok=True)
        self._users: Dict[str, Dict] = {}
        self._load_users()
        self._ensure_default_admin()
    
    def _load_users(self):
        """Load users from file"""
        if self.users_file.exists():
            try:
                with open(self.users_file, 'r') as f:
                    self._users = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                self._users = {}
    
    def _save_users(self):
        """Save users to file"""
        with open(self.users_file, 'w') as f:
            json.dump(self._users, f, indent=2, default=str)
    
    def _hash_password(self, password: str) -> str:
        """Hash password with salt"""
        salt = os.urandom(32)
        key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return salt.hex() + key.hex()
    
    def _verify_password(self, stored_password: str, provided_password: str) -> bool:
        """Verify password against stored hash"""
        try:
            salt = bytes.fromhex(stored_password[:64])
            stored_key = stored_password[64:]
            new_key = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
            return stored_key == new_key.hex()
        except (ValueError, TypeError):
            return False
    
    def _ensure_default_admin(self):
        """Ensure default admin user exists"""
        if not self._users:
            # Create default admin user
            default_password = os.getenv("ADMIN_PASSWORD", "admin123")
            print("🔐 Creating default admin user...")
            print(f"   Username: admin")
            print(f"   Password: {default_password}")
            print("   ⚠️  Change this password immediately!")
            
            self.create_user(CreateUserRequest(
                username="admin",
                password=default_password,
                email="admin@localhost",
                role=UserRole.ADMIN
            ))
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username/password"""
        user_data = self._users.get(username)
        if not user_data:
            return None
        
        if not self._verify_password(user_data["password_hash"], password):
            return None
        
        # Update last login
        user_data["last_login"] = datetime.utcnow().isoformat()
        self._save_users()
        
        return User(
            username=user_data["username"],
            email=user_data.get("email"),
            role=UserRole(user_data["role"]),
            is_active=user_data.get("is_active", True),
            created_at=datetime.fromisoformat(user_data["created_at"]),
            last_login=datetime.utcnow()
        )
    
    def get_user(self, username: str) -> Optional[User]:
        """Get user by username"""
        user_data = self._users.get(username)
        if not user_data:
            return None
        
        return User(
            username=user_data["username"],
            email=user_data.get("email"),
            role=UserRole(user_data["role"]),
            is_active=user_data.get("is_active", True),
            created_at=datetime.fromisoformat(user_data["created_at"]),
            last_login=datetime.fromisoformat(user_data["last_login"]) if user_data.get("last_login") else None
        )
    
    def create_user(self, request: CreateUserRequest) -> User:
        """Create new user"""
        if request.username in self._users:
            raise ValueError(f"User '{request.username}' already exists")
        
        user_data = {
            "username": request.username,
            "email": request.email,
            "role": request.role.value,
            "password_hash": self._hash_password(request.password),
            "is_active": True,
            "created_at": datetime.utcnow().isoformat(),
            "last_login": None
        }
        
        self._users[request.username] = user_data
        self._save_users()
        
        return User(
            username=request.username,
            email=request.email,
            role=request.role,
            is_active=True,
            created_at=datetime.utcnow(),
            last_login=None
        )
    
    def update_user(self, username: str, **kwargs) -> Optional[User]:
        """Update user"""
        if username not in self._users:
            return None
        
        user_data = self._users[username]
        
        # Update allowed fields
        if "email" in kwargs:
            user_data["email"] = kwargs["email"]
        if "role" in kwargs:
            user_data["role"] = kwargs["role"].value if isinstance(kwargs["role"], UserRole) else kwargs["role"]
        if "is_active" in kwargs:
            user_data["is_active"] = kwargs["is_active"]
        if "password" in kwargs:
            user_data["password_hash"] = self._hash_password(kwargs["password"])
        
        self._save_users()
        return self.get_user(username)
    
    def delete_user(self, username: str) -> bool:
        """Delete user"""
        if username in self._users:
            del self._users[username]
            self._save_users()
            return True
        return False
    
    def list_users(self) -> List[User]:
        """List all users"""
        users = []
        for user_data in self._users.values():
            users.append(User(
                username=user_data["username"],
                email=user_data.get("email"),
                role=UserRole(user_data["role"]),
                is_active=user_data.get("is_active", True),
                created_at=datetime.fromisoformat(user_data["created_at"]),
                last_login=datetime.fromisoformat(user_data["last_login"]) if user_data.get("last_login") else None
            ))
        return users


# Global user manager instance
user_manager = SimpleUserManager()