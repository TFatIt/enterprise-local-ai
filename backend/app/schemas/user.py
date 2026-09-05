"""Schemas for User, Role, Department, and Enterprise Account Management."""

from datetime import datetime
from typing import Optional, List, Any, Dict
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict, EmailStr


class DepartmentBase(BaseModel):
    code: str = Field(..., max_length=50, description="Unique code e.g. IT, HR, FINANCE")
    name: str = Field(..., max_length=100, description="Display name of department")
    description: Optional[str] = Field(None, description="Detailed description")


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None


class DepartmentResponse(DepartmentBase):
    id: int
    user_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)


class PermissionResponse(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str] = None
    category: str

    model_config = ConfigDict(from_attributes=True)


class RoleResponse(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str] = None
    is_system_role: bool = True
    permissions: List[PermissionResponse] = []

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    email: str = Field(..., description="Corporate email address")
    username: str = Field(..., min_length=3, max_length=50)
    full_name: str = Field(..., min_length=2, max_length=150)
    password: str = Field(..., min_length=6)
    employee_code: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=30)
    position: Optional[str] = Field(None, max_length=100)
    role_code: str = Field("EMPLOYEE", description="Role code: SUPER_ADMIN, IT_ADMIN, EMPLOYEE...")
    department_id: Optional[int] = Field(None, description="Department ID")
    status: str = Field("ACTIVE", description="ACTIVE, INACTIVE, LOCKED, SUSPENDED, PENDING")


class UserUpdate(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    employee_code: Optional[str] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    role_code: Optional[str] = None
    department_id: Optional[int] = None
    status: Optional[str] = None
    avatar: Optional[str] = None
    is_active: Optional[bool] = None


class UserStatusUpdateRequest(BaseModel):
    status: str = Field(..., description="ACTIVE, INACTIVE, LOCKED, SUSPENDED, PENDING")
    reason: Optional[str] = None


class UserDepartmentUpdateRequest(BaseModel):
    department_id: int


class UserRoleUpdateRequest(BaseModel):
    role_code: str


class UserListResponse(BaseModel):
    id: UUID
    email: str
    username: str
    full_name: str
    employee_code: Optional[str] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    role: str
    role_name: Optional[str] = None
    department_id: Optional[int] = None
    department: Optional[str] = None
    status: str
    is_active: bool
    avatar: Optional[str] = None
    last_login_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserDetailResponse(UserListResponse):
    permissions: List[str] = []
    updated_at: Optional[datetime] = None
    force_password_change: bool = False


class PasswordResetResponse(BaseModel):
    success: bool
    message: str
    temporary_password: str
    user_id: UUID
    username: str


class UserBulkActionRequest(BaseModel):
    user_ids: List[UUID]
    action: str = Field(..., description="ACTIVATE, DEACTIVATE, LOCK, UNLOCK, ASSIGN_DEPARTMENT")
    target_department_id: Optional[int] = None


class UserProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None


class UserChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)


class UserStatsResponse(BaseModel):
    total_users: int
    active_users: int
    inactive_users: int
    locked_users: int
    pending_users: int
    total_departments: int
    it_users: int
    admin_users: int
