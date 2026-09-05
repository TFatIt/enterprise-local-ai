"""Enterprise User and Internal Account Management API router."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Request, UploadFile, File, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_active_user, require_role
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserListResponse,
    UserDetailResponse,
    UserStatusUpdateRequest,
    UserDepartmentUpdateRequest,
    UserRoleUpdateRequest,
    PasswordResetResponse,
    UserBulkActionRequest,
    UserProfileUpdateRequest,
    UserChangePasswordRequest,
    UserStatsResponse,
    DepartmentCreate,
    DepartmentResponse,
    RoleResponse,
    PermissionResponse,
)
from app.services.user_service import user_service

router = APIRouter()

# Managers and Admins permitted to manage accounts within their scope
ACCOUNT_MANAGERS = ["SUPER_ADMIN", "ADMIN", "IT_ADMIN", "IT_MANAGER", "DEPARTMENT_MANAGER"]


def _format_user_item(u: User) -> UserListResponse:
    return UserListResponse(
        id=u.id,
        email=u.email,
        username=u.username,
        full_name=u.full_name,
        employee_code=u.employee_code,
        phone=u.phone,
        position=u.position,
        role=u.role.code if u.role else "EMPLOYEE",
        role_name=u.role.name if u.role else "Nhân viên",
        department_id=u.department_id,
        department=u.department.name if u.department else None,
        status=u.status or ("ACTIVE" if u.is_active else "INACTIVE"),
        is_active=u.is_active,
        avatar=u.avatar,
        last_login_at=u.last_login_at,
        created_at=u.created_at,
    )


# -------------------------------------------------------------
# User Stats & Summaries
# -------------------------------------------------------------
@router.get(
    "/stats/summary",
    response_model=UserStatsResponse,
    summary="Thống kê tài khoản người dùng",
)
def get_user_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(ACCOUNT_MANAGERS)),
) -> UserStatsResponse:
    stats = user_service.get_user_stats(db, current_user)
    return UserStatsResponse(**stats)


# -------------------------------------------------------------
# Self-Service Profile (All authenticated users)
# -------------------------------------------------------------
@router.get(
    "/me/profile",
    response_model=UserDetailResponse,
    summary="Hồ sơ tài khoản cá nhân",
)
def get_my_profile(
    current_user: User = Depends(get_current_active_user),
) -> UserDetailResponse:
    item = _format_user_item(current_user)
    perms = user_service.get_user_permissions(current_user)
    return UserDetailResponse(
        **item.model_dump(),
        permissions=perms,
        updated_at=current_user.updated_at,
        force_password_change=current_user.force_password_change,
    )


@router.put(
    "/me/profile",
    response_model=UserDetailResponse,
    summary="Cập nhật thông tin cá nhân",
)
def update_my_profile(
    profile_in: UserProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UserDetailResponse:
    updated = user_service.update_profile(db, current_user, profile_in)
    item = _format_user_item(updated)
    perms = user_service.get_user_permissions(updated)
    return UserDetailResponse(
        **item.model_dump(),
        permissions=perms,
        updated_at=updated.updated_at,
        force_password_change=updated.force_password_change,
    )


@router.post(
    "/me/change-password",
    status_code=status.HTTP_200_OK,
    summary="Tự đổi mật khẩu",
)
def change_my_password(
    pw_in: UserChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    user_service.change_password(db, current_user, pw_in)
    return {"success": True, "message": "Đổi mật khẩu thành công."}


# -------------------------------------------------------------
# Roles & Permissions metadata
# -------------------------------------------------------------
@router.get(
    "/roles",
    response_model=List[RoleResponse],
    summary="Danh sách vai trò và quyền hạn",
)
def list_roles(
    db: Session = Depends(get_db),
    _: User = Depends(require_role(ACCOUNT_MANAGERS)),
) -> List[RoleResponse]:
    roles = user_service.get_roles(db)
    return [
        RoleResponse(
            id=r.id,
            code=r.code,
            name=r.name,
            description=r.description,
            is_system_role=r.is_system_role,
            permissions=[
                PermissionResponse(
                    id=p.id,
                    code=p.code,
                    name=p.name,
                    description=p.description,
                    category=p.category,
                )
                for p in r.permissions
            ],
        )
        for r in roles
    ]


@router.get(
    "/permissions",
    response_model=List[PermissionResponse],
    summary="Danh sách quyền hạn trong hệ thống",
)
def list_permissions(
    db: Session = Depends(get_db),
    _: User = Depends(require_role(ACCOUNT_MANAGERS)),
) -> List[PermissionResponse]:
    perms = user_service.get_permissions(db)
    return [
        PermissionResponse(
            id=p.id,
            code=p.code,
            name=p.name,
            description=p.description,
            category=p.category,
        )
        for p in perms
    ]


@router.get(
    "/departments",
    response_model=List[DepartmentResponse],
    summary="Danh sách phòng ban",
)
def list_departments(
    db: Session = Depends(get_db),
    _: User = Depends(require_role(ACCOUNT_MANAGERS)),
) -> List[DepartmentResponse]:
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
    "/departments",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo phòng ban mới",
)
def create_department(
    dept_in: DepartmentCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(["SUPER_ADMIN", "ADMIN"])),
) -> DepartmentResponse:
    d = user_service.create_department(db, dept_in)
    return DepartmentResponse(id=d.id, code=d.code, name=d.name, description=d.description, user_count=0)


# -------------------------------------------------------------
# User List & Queries
# -------------------------------------------------------------
@router.get(
    "",
    response_model=List[UserListResponse],
    summary="Danh sách tài khoản người dùng",
)
def list_users(
    search: Optional[str] = Query(None, description="Tìm kiếm username, tên, email, mã NV, sđt"),
    department_id: Optional[int] = Query(None),
    role_code: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    position: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(ACCOUNT_MANAGERS)),
) -> List[UserListResponse]:
    users, _ = user_service.get_users_paginated(
        db,
        actor=current_user,
        search=search,
        department_id=department_id,
        role_code=role_code,
        user_status=status,
        position=position,
        skip=skip,
        limit=limit,
    )
    return [_format_user_item(u) for u in users]


# -------------------------------------------------------------
# CSV Export & Import
# -------------------------------------------------------------
@router.get(
    "/export/csv",
    summary="Xuất danh sách người dùng ra tệp CSV",
)
def export_users_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(ACCOUNT_MANAGERS)),
):
    csv_data = user_service.export_users_csv(db, current_user)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=enterprise_users.csv"},
    )


@router.post(
    "/import/csv",
    summary="Nhập danh sách người dùng từ tệp CSV",
)
async def import_users_csv(
    file: UploadFile = File(...),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN", "ADMIN", "IT_ADMIN"])),
):
    content = (await file.read()).decode("utf-8-sig", errors="replace")
    client_ip = request.client.host if request and request.client else None
    res = user_service.import_users_csv(db, current_user, content, ip_address=client_ip)
    return res


# -------------------------------------------------------------
# Bulk Action
# -------------------------------------------------------------
@router.post(
    "/bulk-action",
    summary="Thao tác hàng loạt trên tài khoản",
)
def bulk_user_action(
    bulk_in: UserBulkActionRequest,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN", "ADMIN", "IT_ADMIN"])),
):
    client_ip = request.client.host if request and request.client else None
    return user_service.bulk_action(db, current_user, bulk_in, ip_address=client_ip)


# -------------------------------------------------------------
# Single User CRUD & Actions
# -------------------------------------------------------------
@router.post(
    "",
    response_model=UserListResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo mới tài khoản người dùng",
)
def create_user(
    user_in: UserCreate,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(ACCOUNT_MANAGERS)),
) -> UserListResponse:
    client_ip = request.client.host if request and request.client else None
    user = user_service.create_user(db, current_user, user_in, ip_address=client_ip)
    return _format_user_item(user)


@router.get(
    "/{user_id}",
    response_model=UserDetailResponse,
    summary="Chi tiết người dùng",
)
def get_user_detail(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(ACCOUNT_MANAGERS)),
) -> UserDetailResponse:
    user = user_service.get_user_by_id(db, user_id, actor=current_user)
    item = _format_user_item(user)
    perms = user_service.get_user_permissions(user)
    return UserDetailResponse(
        **item.model_dump(),
        permissions=perms,
        updated_at=user.updated_at,
        force_password_change=user.force_password_change,
    )


@router.put(
    "/{user_id}",
    response_model=UserListResponse,
    summary="Chỉnh sửa thông tin tài khoản",
)
def update_user(
    user_id: UUID,
    user_in: UserUpdate,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(ACCOUNT_MANAGERS)),
) -> UserListResponse:
    client_ip = request.client.host if request and request.client else None
    user = user_service.update_user(db, current_user, user_id, user_in, ip_address=client_ip)
    return _format_user_item(user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Vô hiệu hóa tài khoản (Soft Delete)",
)
def delete_user(
    user_id: UUID,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(ACCOUNT_MANAGERS)),
):
    client_ip = request.client.host if request and request.client else None
    user_service.delete_user(db, current_user, user_id, ip_address=client_ip)
    return {"success": True, "message": "Tài khoản đã được vô hiệu hóa thành công."}


@router.patch(
    "/{user_id}/status",
    response_model=UserListResponse,
    summary="Thay đổi trạng thái tài khoản",
)
def update_user_status(
    user_id: UUID,
    status_in: UserStatusUpdateRequest,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(ACCOUNT_MANAGERS)),
) -> UserListResponse:
    client_ip = request.client.host if request and request.client else None
    user = user_service.update_user(
        db,
        current_user,
        user_id,
        UserUpdate(status=status_in.status),
        ip_address=client_ip,
    )
    return _format_user_item(user)


@router.patch(
    "/{user_id}/department",
    response_model=UserListResponse,
    summary="Điều chuyển phòng ban",
)
def update_user_department(
    user_id: UUID,
    dept_in: UserDepartmentUpdateRequest,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(ACCOUNT_MANAGERS)),
) -> UserListResponse:
    client_ip = request.client.host if request and request.client else None
    user = user_service.update_user(
        db,
        current_user,
        user_id,
        UserUpdate(department_id=dept_in.department_id),
        ip_address=client_ip,
    )
    return _format_user_item(user)


@router.patch(
    "/{user_id}/role",
    response_model=UserListResponse,
    summary="Thay đổi vai trò (Role)",
)
def update_user_role(
    user_id: UUID,
    role_in: UserRoleUpdateRequest,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN", "ADMIN", "IT_ADMIN"])),
) -> UserListResponse:
    client_ip = request.client.host if request and request.client else None
    user = user_service.update_user(
        db,
        current_user,
        user_id,
        UserUpdate(role_code=role_in.role_code),
        ip_address=client_ip,
    )
    return _format_user_item(user)


@router.post(
    "/{user_id}/reset-password",
    response_model=PasswordResetResponse,
    summary="Đặt lại mật khẩu (Cấp mật khẩu tạm thời)",
)
def reset_password(
    user_id: UUID,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(ACCOUNT_MANAGERS)),
) -> PasswordResetResponse:
    client_ip = request.client.host if request and request.client else None
    user = user_service.get_user_by_id(db, user_id, actor=current_user)
    temp_pw = user_service.reset_password(db, current_user, user_id, ip_address=client_ip)
    return PasswordResetResponse(
        success=True,
        message="Mật khẩu đã được đặt lại thành công. Người dùng sẽ phải đổi mật khẩu ở lần đăng nhập tiếp theo.",
        temporary_password=temp_pw,
        user_id=user.id,
        username=user.username,
    )


@router.post(
    "/{user_id}/lock",
    response_model=UserListResponse,
    summary="Khóa tài khoản",
)
def lock_user(
    user_id: UUID,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(ACCOUNT_MANAGERS)),
) -> UserListResponse:
    client_ip = request.client.host if request and request.client else None
    user = user_service.lock_user(db, current_user, user_id, ip_address=client_ip)
    return _format_user_item(user)


@router.post(
    "/{user_id}/unlock",
    response_model=UserListResponse,
    summary="Mở khóa tài khoản",
)
def unlock_user(
    user_id: UUID,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(ACCOUNT_MANAGERS)),
) -> UserListResponse:
    client_ip = request.client.host if request and request.client else None
    user = user_service.unlock_user(db, current_user, user_id, ip_address=client_ip)
    return _format_user_item(user)


@router.get(
    "/{user_id}/permissions",
    response_model=List[str],
    summary="Danh sách quyền hạn của tài khoản",
)
def get_user_permissions(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(ACCOUNT_MANAGERS)),
) -> List[str]:
    user = user_service.get_user_by_id(db, user_id, actor=current_user)
    return user_service.get_user_permissions(user)


@router.get(
    "/{user_id}/activity",
    summary="Nhật ký hoạt động của tài khoản",
)
def get_user_activity(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(ACCOUNT_MANAGERS)),
):
    user = user_service.get_user_by_id(db, user_id, actor=current_user)
    # Fetch logs where user was actor OR user was target
    logs = (
        db.query(AuditLog)
        .filter(
            or_(
                AuditLog.user_id == user.id,
                AuditLog.target_user_id == user.id
            )
        )
        .order_by(AuditLog.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": l.id,
            "action": l.action,
            "resource": l.resource,
            "result": l.result,
            "details": l.details,
            "ip_address": l.ip_address,
            "created_at": l.created_at,
        }
        for l in logs
    ]
