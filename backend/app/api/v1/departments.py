"""Department and Role reference endpoints."""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_active_user, require_role
from app.schemas.user import DepartmentCreate, DepartmentUpdate, DepartmentResponse, RoleResponse
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
    depts = user_service.get_departments(db)
    return [
        DepartmentResponse(
            id=d.id,
            code=d.code,
            name=d.name,
            description=d.description,
            user_count=len(d.users) if d.users else 0,
        )
        for d in depts
    ]


@router.post(
    "",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo phòng ban mới"
)
def create_department(
    dept_in: DepartmentCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(["SUPER_ADMIN", "ADMIN", "IT_ADMIN"]))
) -> DepartmentResponse:
    """Create a new department."""
    d = user_service.create_department(db, dept_in)
    return DepartmentResponse(
        id=d.id,
        code=d.code,
        name=d.name,
        description=d.description,
        user_count=0,
    )


@router.put(
    "/{dept_id}",
    response_model=DepartmentResponse,
    summary="Cập nhật thông tin phòng ban",
)
def update_department(
    dept_id: int,
    dept_in: DepartmentUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(["SUPER_ADMIN", "ADMIN", "IT_ADMIN"])),
) -> DepartmentResponse:
    """Update department name and description."""
    d = user_service.update_department(db, dept_id, dept_in)
    return DepartmentResponse(
        id=d.id,
        code=d.code,
        name=d.name,
        description=d.description,
        user_count=len(d.users) if d.users else 0,
    )


@router.delete(
    "/{dept_id}",
    status_code=status.HTTP_200_OK,
    summary="Xóa phòng ban",
)
def delete_department(
    dept_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(["SUPER_ADMIN", "ADMIN"])),
):
    """Delete department if empty."""
    user_service.delete_department(db, dept_id)
    return {"success": True, "message": "Đã xóa phòng ban thành công."}


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
