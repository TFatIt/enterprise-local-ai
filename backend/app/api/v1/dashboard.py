"""API Router for Admin Dashboard & Analytics."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import require_role
from app.models.user import User
from app.schemas.dashboard import DashboardAnalyticsResponse, KnowledgeGapResponse
from app.services.dashboard_service import dashboard_service

router = APIRouter()


@router.get(
    "/stats",
    response_model=DashboardAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Lấy số liệu thống kê tổng quan và biểu đồ phân tích hệ thống"
)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN", "IT_ADMIN"])),
):
    """Retrieve full system metrics, tickets breakdown, and recent activities. Restricted to Super Admin & IT Admin."""
    return dashboard_service.get_analytics(db)


@router.get(
    "/knowledge-gaps",
    response_model=KnowledgeGapResponse,
    status_code=status.HTTP_200_OK,
    summary="Phân tích khoảng trống tri thức doanh nghiệp (Knowledge Gap Analytics)"
)
def get_knowledge_gaps(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN", "IT_ADMIN"])),
):
    """Analyze queries where AI lacked internal documentation, grouped by department and topic."""
    return dashboard_service.get_knowledge_gaps(db)
