"""Authentication API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import LoginRequest, RefreshTokenRequest, TokenResponse, UserResponse
from app.services.auth_service import auth_service
from app.api.deps import get_current_active_user
from app.models.user import User

router = APIRouter()


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Đăng nhập tài khoản",
    description="Xác thực người dùng bằng Email hoặc Username và trả về cặp JWT Access Token / Refresh Token."
)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
) -> TokenResponse:
    """Authenticate credentials and generate token response."""
    user = auth_service.authenticate_user(
        db,
        username_or_email=login_data.username_or_email,
        password=login_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email/Username hoặc mật khẩu không chính xác.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return auth_service.create_user_token_response(user)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Làm mới Token",
    description="Sử dụng Refresh Token hợp lệ để cấp mới Access Token mà không cần nhập lại mật khẩu."
)
def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
) -> TokenResponse:
    """Exchange a valid refresh token for a new token pair."""
    token_response = auth_service.refresh_user_token(db, refresh_data.refresh_token)
    if not token_response:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token không hợp lệ hoặc đã hết hạn.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_response


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Thông tin tài khoản hiện tại",
    description="Lấy hồ sơ người dùng, vai trò (RBAC) và phòng ban từ Bearer Token."
)
def get_me(
    current_user: User = Depends(get_current_active_user)
) -> UserResponse:
    """Return currently authenticated user profile."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        role=current_user.role.code if current_user.role else "EMPLOYEE",
        department=current_user.department.name if current_user.department else None,
        is_active=current_user.is_active,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Đăng xuất",
    description="Đăng xuất tài khoản và kết thúc phiên làm việc trên client."
)
def logout(
    current_user: User = Depends(get_current_active_user)
):
    """Client handles clearing token; server returns acknowledgment."""
    return {
        "success": True,
        "message": f"Tài khoản {current_user.username} đã đăng xuất thành công."
    }
