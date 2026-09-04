"""Schemas for User, Role, and Department management."""

from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class DepartmentBase(BaseModel):
    code: str = Field(..., max_length=50, description="Unique code e.g. IT, HR, FINANCE")
    name: str = Field(..., max_length=100, description="Display name of department")
    description: Optional[str] = Field(None, description="Detailed description")


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentResponse(DepartmentBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class RoleResponse(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    email: str = Field(..., description="Corporate email address")
    username: str = Field(..., min_length=3, max_length=50)
    full_name: str = Field(..., min_length=2, max_length=150)
    password: str = Field(..., min_length=6)
    role_code: str = Field("EMPLOYEE", description="Role code: SUPER_ADMIN, IT_ADMIN, EMPLOYEE")
    department_id: Optional[int] = Field(None, description="Department ID")


class UserUpdate(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    role_code: Optional[str] = None
    department_id: Optional[int] = None
    is_active: Optional[bool] = None


class UserListResponse(BaseModel):
    id: UUID
    email: str
    username: str
    full_name: str
    role: str
    department: Optional[str] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
