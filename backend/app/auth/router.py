"""
Authentication API routes
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from ..database import get_db
from .models import (
    UserCreate, UserLogin, UserResponse, TokenResponse,
    RefreshTokenRequest, AdminUserUpdate
)
from .service import auth_service
from .dependencies import get_current_user, get_current_admin_user
from .models import UserInDB

auth_router = APIRouter(prefix="/api/auth", tags=["Authentication"])
users_router = APIRouter(prefix="/api/users", tags=["Users"])


# =============================================================================
# Authentication Endpoints
# =============================================================================

@auth_router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user account.
    Default role is 'user' (cannot chat only, no admin access).
    """
    user = await auth_service.create_user(db, user_data)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    return user


@auth_router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with username or email and password.
    Returns access token and refresh token.
    """
    user = await auth_service.authenticate_user(
        db, credentials.username, credentials.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create tokens
    tokens = auth_service.create_tokens(user)
    
    # Store refresh token
    await auth_service.store_refresh_token(
        db,
        str(user.id),
        tokens.refresh_token,
        user_agent=request.headers.get("User-Agent"),
        ip_address=request.client.host if request.client else None
    )
    
    return tokens


@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_request: RefreshTokenRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    """
    user_id = await auth_service.validate_refresh_token(
        db, token_request.refresh_token
    )
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    user = await auth_service.get_user_by_id(db, user_id)
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Revoke old refresh token
    await auth_service.revoke_refresh_token(db, token_request.refresh_token)
    
    # Create new tokens
    tokens = auth_service.create_tokens(user)
    
    # Store new refresh token
    await auth_service.store_refresh_token(
        db,
        str(user.id),
        tokens.refresh_token,
        user_agent=request.headers.get("User-Agent"),
        ip_address=request.client.host if request.client else None
    )
    
    return tokens


@auth_router.post("/logout")
async def logout(
    token_request: RefreshTokenRequest,
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Logout and revoke refresh token.
    """
    await auth_service.revoke_refresh_token(db, token_request.refresh_token)
    return {"message": "Successfully logged out"}


@auth_router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get current user information.
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )


# =============================================================================
# User Management Endpoints (Admin only)
# =============================================================================

@users_router.get("", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: UserInDB = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all users (admin only).
    """
    return await auth_service.get_all_users(db, skip, limit)


@users_router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: UserInDB = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user by ID (admin only).
    """
    user = await auth_service.get_user_by_id(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role_name,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login=user.last_login
    )


@users_router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    update_data: AdminUserUpdate,
    current_user: UserInDB = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user (admin only).
    Can change role, deactivate user, etc.
    """
    user = await auth_service.get_user_by_id(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update role if specified
    if update_data.role_id is not None:
        success = await auth_service.update_user_role(db, user_id, update_data.role_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update user role"
            )
    
    # Refresh user data
    user = await auth_service.get_user_by_id(db, user_id)
    
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role_name,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login=user.last_login
    )


@users_router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: UserInDB = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete user (admin only).
    """
    # Prevent self-deletion
    if str(current_user.id) == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    success = await auth_service.delete_user(db, user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or deletion failed"
        )
    
    return {"message": "User deleted successfully"}

