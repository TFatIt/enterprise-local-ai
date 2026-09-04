"""Authentication and User Data Transfer Objects (Pydantic Schemas)."""

from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class LoginRequest(BaseModel):
    """Schema for user login request supporting email or username."""
    username_or_email: str = Field(..., description="Email address or username")
    password: str = Field(..., min_length=6, description="Plain text password")


class RefreshTokenRequest(BaseModel):
    """Schema for refreshing expired access token."""
    refresh_token: str = Field(..., description="Valid refresh token")


class UserResponse(BaseModel):
    """Schema for public user profile representation.
    Accepts both public internet and enterprise intranet (.local, .internal) email formats.
    """
    id: UUID
    email: str
    username: str
    full_name: str
    role: str
    department: Optional[str] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Schema for successful authentication response with tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # in seconds
    user: UserResponse


class TokenPayload(BaseModel):
    """Schema for decoded JWT token payload."""
    sub: str  # User ID as UUID string
    role: str
    department_id: Optional[int] = None
    token_type: str  # 'access' or 'refresh'
    exp: Optional[int] = None
