"""
Authentication Database Models
User management and API key models for security system
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import uuid

# Use the same Base as the main models
from .models import Base

class User(Base):
    """User account model"""
    __tablename__ = 'users'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # User profile
    first_name = Column(String(100))
    last_name = Column(String(100))
    role = Column(String(20), nullable=False, default='viewer')
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime)
    
    # Security settings
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_secret = Column(String(32))  # TOTP secret
    
    # Relationships
    api_keys = relationship("ApiKey", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")
    user_sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id='{self.id}', username='{self.username}', role='{self.role}')>"
    
    @property
    def full_name(self):
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary"""
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'role': self.role,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'mfa_enabled': self.mfa_enabled
        }
        
        if include_sensitive:
            data['password_hash'] = self.password_hash
            data['mfa_secret'] = self.mfa_secret
        
        return data

class ApiKey(Base):
    """API key model for programmatic access"""
    __tablename__ = 'api_keys'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    
    # Key details
    name = Column(String(100), nullable=False)
    description = Column(Text)
    key_hash = Column(String(64), nullable=False, unique=True, index=True)  # SHA-256 hash
    key_prefix = Column(String(10), nullable=False)  # First 8 chars for identification
    
    # Permissions and scope
    scopes = Column(Text)  # JSON array of allowed scopes
    
    # Status and expiry
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    
    # Usage tracking
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_used = Column(DateTime)
    usage_count = Column(Integer, default=0, nullable=False)
    
    # Rate limiting
    rate_limit_per_hour = Column(Integer, default=1000)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    
    def __repr__(self):
        return f"<ApiKey(id='{self.id}', name='{self.name}', user_id='{self.user_id}')>"
    
    @classmethod
    def create_expiry_date(cls, days=365):
        """Create expiry date (default 1 year)"""
        return datetime.utcnow() + timedelta(days=days)
    
    def is_expired(self):
        """Check if API key is expired"""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self):
        """Check if API key is valid (active and not expired)"""
        return self.is_active and not self.is_expired()
    
    def to_dict(self, include_sensitive=False):
        """Convert API key to dictionary"""
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'key_prefix': self.key_prefix,
            'scopes': self.scopes,
            'is_active': self.is_active,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'usage_count': self.usage_count,
            'rate_limit_per_hour': self.rate_limit_per_hour
        }
        
        if include_sensitive:
            data['key_hash'] = self.key_hash
        
        return data

class UserSession(Base):
    """User session tracking"""
    __tablename__ = 'user_sessions'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    
    # Session details
    session_token = Column(String(255), nullable=False, unique=True, index=True)
    jwt_token_hash = Column(String(64))  # Hash of JWT token for revocation
    
    # Session metadata
    ip_address = Column(String(45))  # IPv6 support
    user_agent = Column(Text)
    device_fingerprint = Column(String(64))
    
    # Session status
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="user_sessions")
    
    def __repr__(self):
        return f"<UserSession(id='{self.id}', user_id='{self.user_id}', active='{self.is_active}')>"
    
    def is_expired(self):
        """Check if session is expired"""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self):
        """Check if session is valid"""
        return self.is_active and not self.is_expired()
    
    def extend_session(self, hours=24):
        """Extend session expiry"""
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
        self.last_activity = datetime.utcnow()
    
    def end_session(self):
        """End the session"""
        self.is_active = False
        self.ended_at = datetime.utcnow()
    
    def to_dict(self):
        """Convert session to dictionary"""
        return {
            'id': self.id,
            'session_token': self.session_token,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'is_active': self.is_active,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None
        }

class AuditLog(Base):
    """Security audit log"""
    __tablename__ = 'audit_logs'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), nullable=True)  # Nullable for system events
    
    # Event details
    event_type = Column(String(50), nullable=False, index=True)  # login, logout, permission_change, etc.
    event_category = Column(String(20), nullable=False, index=True)  # auth, admin, data, system
    resource_type = Column(String(50))  # camera, recording, user, etc.
    resource_id = Column(String(36))
    
    # Event description and metadata
    description = Column(Text, nullable=False)
    event_metadata = Column(Text)  # JSON metadata
    
    # Request context
    ip_address = Column(String(45))
    user_agent = Column(Text)
    endpoint = Column(String(255))
    method = Column(String(10))
    
    # Security flags
    severity = Column(String(20), default='info', nullable=False)  # info, warning, error, critical
    success = Column(Boolean, nullable=False)
    
    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog(id='{self.id}', event_type='{self.event_type}', severity='{self.severity}')>"
    
    def to_dict(self):
        """Convert audit log to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'event_type': self.event_type,
            'event_category': self.event_category,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'description': self.description,
            'event_metadata': self.event_metadata,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'endpoint': self.endpoint,
            'method': self.method,
            'severity': self.severity,
            'success': self.success,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

class SecurityEvent(Base):
    """Security event tracking"""
    __tablename__ = 'security_events'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Event identification
    event_type = Column(String(50), nullable=False, index=True)
    event_subtype = Column(String(50))
    severity = Column(String(20), default='medium', nullable=False)
    
    # Event details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    source_ip = Column(String(45))
    target_resource = Column(String(255))
    
    # Status and resolution
    status = Column(String(20), default='open', nullable=False)  # open, investigating, resolved, false_positive
    assigned_to = Column(String(36))  # User ID
    resolution_notes = Column(Text)
    
    # Timestamps
    detected_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    acknowledged_at = Column(DateTime)
    resolved_at = Column(DateTime)
    
    # Event metadata
    event_metadata = Column(Text)  # JSON metadata
    risk_score = Column(Integer, default=50)  # 0-100 risk score
    
    def __repr__(self):
        return f"<SecurityEvent(id='{self.id}', type='{self.event_type}', severity='{self.severity}')>"
    
    def to_dict(self):
        """Convert security event to dictionary"""
        return {
            'id': self.id,
            'event_type': self.event_type,
            'event_subtype': self.event_subtype,
            'severity': self.severity,
            'title': self.title,
            'description': self.description,
            'source_ip': self.source_ip,
            'target_resource': self.target_resource,
            'status': self.status,
            'assigned_to': self.assigned_to,
            'resolution_notes': self.resolution_notes,
            'detected_at': self.detected_at.isoformat() if self.detected_at else None,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'event_metadata': self.event_metadata,
            'risk_score': self.risk_score
        }