"""Department and Role reference endpoints."""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_active_user, require_role
from app.schemas.user import DepartmentCreate, DepartmentResponse, RoleResponse
from app.services.user_service import user_service
from app.models.user import User

router = APIRouter()


@router.get(
    "",
    response_model=List[DepartmentResponse],
    summary="Danh sách phòng ban",
    description="Tất cả nhân viên đã đăng nhập đều có thể xem danh sách phòng ban."
)
def list_departments(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user)
) -> List[DepartmentResponse]:
    """Return all enterprise departments."""
    return user_service.get_departments(db)


@router.post(
    "",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo phòng ban mới (Super Admin)"
)
def create_department(
    dept_in: DepartmentCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(["SUPER_ADMIN"]))
) -> DepartmentResponse:
    """Create a new department."""
    return user_service.create_department(db, dept_in)


@router.get(
    "/roles",
    response_model=List[RoleResponse],
    summary="Danh sách vai trò RBAC"
)
def list_roles(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user)
) -> List[RoleResponse]:
    """Return available system roles."""
    return user_service.get_roles(db)
