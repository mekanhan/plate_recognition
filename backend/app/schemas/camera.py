"""
Camera Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime
import socket


class CameraBase(BaseModel):
    """Base camera schema"""
    name: str
    ip_address: str
    port: int = 80
    connection_type: str = "http"
    stream_path: Optional[str] = None
    location: Optional[str] = None
    username: Optional[str] = "admin"
    password: Optional[str] = ""
    enabled: bool = True

    @validator('ip_address')
    def validate_ip_address(cls, v):
        """Validate IP address format"""
        try:
            socket.inet_aton(v)
            return v
        except socket.error:
            raise ValueError('Invalid IP address format')

    @validator('port')
    def validate_port(cls, v):
        """Validate port range"""
        if not 1 <= v <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v

    @validator('connection_type')
    def validate_connection_type(cls, v):
        """Validate connection type"""
        allowed_types = ["http", "https", "rtsp", "rtsps", "onvif"]
        if v.lower() not in allowed_types:
            raise ValueError(f'Connection type must be one of: {allowed_types}')
        return v.lower()


class CameraCreate(CameraBase):
    """Schema for creating a new camera"""
    pass


class CameraUpdate(BaseModel):
    """Schema for updating an existing camera"""
    name: Optional[str] = None
    ip_address: Optional[str] = None
    port: Optional[int] = None
    connection_type: Optional[str] = None
    stream_path: Optional[str] = None
    location: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    enabled: Optional[bool] = None

    @validator('ip_address')
    def validate_ip_address(cls, v):
        """Validate IP address format"""
        if v is not None:
            try:
                socket.inet_aton(v)
                return v
            except socket.error:
                raise ValueError('Invalid IP address format')
        return v

    @validator('port')
    def validate_port(cls, v):
        """Validate port range"""
        if v is not None and not 1 <= v <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v


class CameraResponse(CameraBase):
    """Schema for camera responses"""
    id: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CameraListResponse(BaseModel):
    """Schema for camera list responses"""
    cameras: list[CameraResponse]
    total: int