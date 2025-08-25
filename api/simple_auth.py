"""
Simplified Authentication Endpoints
Basic authentication without complex dependencies
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import bcrypt
import secrets
import jwt
from datetime import datetime, timedelta
import sqlite3
import os
import logging

router = APIRouter(prefix="/api/auth", tags=["authentication"])
logger = logging.getLogger(__name__)

# Simple configuration
JWT_SECRET = os.getenv('JWT_SECRET_KEY', secrets.token_urlsafe(64))
DB_PATH = 'data/license_plates.db'

class LoginRequest(BaseModel):
    username: str
    password: str

class QuickSetupRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

def get_db_connection():
    """Get SQLite database connection"""
    return sqlite3.connect(DB_PATH)

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(user_id: str, username: str, role: str) -> str:
    """Create JWT token"""
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def ensure_users_table():
    """Ensure users table exists"""
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS simple_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'viewer',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        conn.commit()

@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """Simple login endpoint"""
    try:
        ensure_users_table()
        
        with get_db_connection() as conn:
            cursor = conn.execute(
                "SELECT id, username, email, password_hash, role FROM simple_users WHERE username = ?",
                (login_data.username,)
            )
            user = cursor.fetchone()
            
            if not user:
                logger.warning(f"User not found: {login_data.username}")
                raise HTTPException(status_code=401, detail="Invalid username or password")
            
            if not verify_password(login_data.password, user[3]):
                logger.warning(f"Password verification failed for user: {login_data.username}")
                raise HTTPException(status_code=401, detail="Invalid username or password")
            
            user_id, username, email, _, role = user
            
            # Update last login
            conn.execute(
                "UPDATE simple_users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                (user_id,)
            )
            conn.commit()
            
            # Create JWT token
            token = create_jwt_token(str(user_id), username, role)
            
            logger.info(f"User logged in successfully: {username}")
            
            return LoginResponse(
                access_token=token,
                user={
                    'id': str(user_id),
                    'username': username,
                    'email': email,
                    'role': role
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Authentication service error")

@router.post("/quick-setup")
async def quick_setup(setup_data: QuickSetupRequest):
    """Quick setup endpoint for creating admin user"""
    try:
        ensure_users_table()
        
        # Validate password strength
        if len(setup_data.password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
        
        password_hash = hash_password(setup_data.password)
        
        with get_db_connection() as conn:
            # Check if user already exists
            cursor = conn.execute(
                "SELECT id FROM simple_users WHERE username = ? OR email = ?",
                (setup_data.username, setup_data.email)
            )
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="User already exists")
            
            # Create admin user
            conn.execute(
                "INSERT INTO simple_users (username, email, password_hash, role) VALUES (?, ?, ?, 'admin')",
                (setup_data.username, setup_data.email, password_hash)
            )
            conn.commit()
            
            logger.info(f"Admin user created via quick setup: {setup_data.username}")
            
            return {"message": "Admin user created successfully"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quick setup error: {e}")
        raise HTTPException(status_code=500, detail="Setup service error")

@router.get("/me")
async def get_current_user(request: Request):
    """Get current user info"""
    auth_header = request.headers.get('authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="No valid authentication token")
    
    token = auth_header[7:]
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        user_id = payload.get('user_id')
        
        ensure_users_table()
        
        with get_db_connection() as conn:
            cursor = conn.execute(
                "SELECT id, username, email, role, created_at, last_login FROM simple_users WHERE id = ?",
                (user_id,)
            )
            user = cursor.fetchone()
            
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            return {
                'id': str(user[0]),
                'username': user[1],
                'email': user[2],
                'role': user[3],
                'created_at': user[4],
                'last_login': user[5]
            }
            
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.error(f"Get user error: {e}")
        raise HTTPException(status_code=500, detail="User service error")

@router.get("/users")
async def list_users(request: Request):
    """List all users (admin only for now)"""
    # For now, just return empty list to indicate the endpoint exists
    # TODO: Add proper authorization check
    try:
        ensure_users_table()
        
        with get_db_connection() as conn:
            cursor = conn.execute(
                "SELECT id, username, email, role, created_at, last_login FROM simple_users"
            )
            users = cursor.fetchall()
            
            return [
                {
                    'id': str(user[0]),
                    'username': user[1],
                    'email': user[2],
                    'role': user[3],
                    'created_at': user[4],
                    'last_login': user[5],
                    'is_active': True
                }
                for user in users
            ]
            
    except Exception as e:
        logger.error(f"List users error: {e}")
        raise HTTPException(status_code=500, detail="User service error")

@router.post("/logout")
async def logout(request: Request):
    """Logout user - invalidate session"""
    try:
        # Get token from header
        auth_header = request.headers.get('authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]
            
            # Verify token is valid
            try:
                payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
                user_id = payload.get('user_id')
                username = payload.get('sub')
                
                # Log successful logout
                logger.info(f"User logged out successfully: {username}")
                
            except jwt.ExpiredSignatureError:
                # Token already expired, that's fine
                logger.info("Expired token logout attempt")
            except jwt.InvalidTokenError:
                # Invalid token, still allow logout
                logger.info("Invalid token logout attempt")
        
        # For simple auth, we don't maintain server-side sessions
        # Client will handle token removal
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        # Return success even on error to not leak information
        return {"message": "Logged out successfully"}