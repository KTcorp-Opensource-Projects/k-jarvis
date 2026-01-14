"""
Authentication models (Pydantic schemas)
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
import uuid


class UserCreate(BaseModel):
    """User registration request"""
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=100)
    name: str = Field(min_length=2, max_length=100)


class UserLogin(BaseModel):
    """User login request"""
    username: str  # Can be username or email
    password: str


class UserResponse(BaseModel):
    """User response (without password)"""
    id: uuid.UUID
    email: str
    name: str
    role: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserInDB(BaseModel):
    """User model from database"""
    id: uuid.UUID
    email: str
    password_hash: str
    name: str
    role_id: int
    role_name: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    kauth_user_id: Optional[str] = None  # Option C: K-Auth user ID for MCPHub
    access_token: Optional[str] = None  # Directive 007: Raw token for A2A Identity Propagation


class TokenResponse(BaseModel):
    """Token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: UserResponse


class TokenData(BaseModel):
    """Token payload data"""
    user_id: str
    email: str
    role: str
    exp: Optional[int] = None


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


class PasswordChange(BaseModel):
    """Password change request"""
    current_password: str
    new_password: str = Field(min_length=6, max_length=100)


class UserUpdate(BaseModel):
    """User update request"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None


class AdminUserUpdate(BaseModel):
    """Admin user update request (can change role)"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = None

