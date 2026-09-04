"""User management endpoints strictly protected by RBAC (SUPER_ADMIN)."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import require_role
from app.schemas.user import UserCreate, UserUpdate, UserListResponse
from app.services.user_service import user_service
from app.models.user import User

router = APIRouter()


@router.get(
    "",
    response_model=List[UserListResponse],
    summary="Danh sách người dùng (Super Admin)",
    description="Chỉ SUPER_ADMIN mới có quyền xem danh sách người dùng toàn hệ thống."
)
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    department_id: Optional[int] = Query(None),
    role_code: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_role(["SUPER_ADMIN"]))
) -> List[UserListResponse]:
    """Fetch user accounts with optional filtering."""
    users = user_service.get_users(
        db,
        skip=skip,
        limit=limit,
        department_id=department_id,
        role_code=role_code
    )
    return [
        UserListResponse(
            id=u.id,
            email=u.email,
            username=u.username,
            full_name=u.full_name,
            role=u.role.code if u.role else "EMPLOYEE",
            department=u.department.name if u.department else None,
            is_active=u.is_active,
        )
        for u in users
    ]


@router.post(
    "",
    response_model=UserListResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo tài khoản nhân viên mới (Super Admin)"
)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(["SUPER_ADMIN"]))
) -> UserListResponse:
    """Register new employee or admin."""
    user = user_service.create_user(db, user_in)
    return UserListResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        role=user.role.code if user.role else "EMPLOYEE",
        department=user.department.name if user.department else None,
        is_active=user.is_active,
    )


@router.get(
    "/{user_id}",
    response_model=UserListResponse,
    summary="Chi tiết tài khoản (Super Admin)"
)
def get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(["SUPER_ADMIN"]))
) -> UserListResponse:
    """Retrieve details of a single user."""
    user = user_service.get_user_by_id(db, user_id)
    return UserListResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        role=user.role.code if user.role else "EMPLOYEE",
        department=user.department.name if user.department else None,
        is_active=user.is_active,
    )


@router.put(
    "/{user_id}",
    response_model=UserListResponse,
    summary="Cập nhật tài khoản (Super Admin)"
)
def update_user(
    user_id: UUID,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(["SUPER_ADMIN"]))
) -> UserListResponse:
    """Update profile, department, or role."""
    user = user_service.update_user(db, user_id, user_in)
    return UserListResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        role=user.role.code if user.role else "EMPLOYEE",
        department=user.department.name if user.department else None,
        is_active=user.is_active,
    )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Khóa / Vô hiệu hóa tài khoản (Super Admin)"
)
def deactivate_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(["SUPER_ADMIN"]))
):
    """Soft delete user account."""
    user_service.delete_user(db, user_id)
    return {"success": True, "message": "Tài khoản đã được vô hiệu hóa thành công."}
