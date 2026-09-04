"""API Router for IT Support Helpdesk Tickets and Comments."""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.ticket import (
    TicketCreate,
    TicketResponse,
    TicketDetailResponse,
    TicketStatusUpdate,
    TicketAssignUpdate,
    TicketCommentCreate,
    TicketCommentResponse,
    TicketAutoTriageRequest,
    TicketAutoTriageResponse,
)
from app.services.ticket_service import ticket_service

router = APIRouter()


@router.post(
    "/auto-triage",
    response_model=TicketAutoTriageResponse,
    status_code=status.HTTP_200_OK,
    summary="AI Tự động phân loại danh mục, mức độ khẩn cấp và gợi ý khắc phục cho Ticket"
)
def auto_triage_ticket(
    triage_in: TicketAutoTriageRequest,
    current_user: User = Depends(get_current_user),
):
    return ticket_service.auto_triage(triage_in.title, triage_in.description)


@router.post(
    "",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo yêu cầu hỗ trợ IT Ticket mới"
)
def create_ticket(
    ticket_in: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = ticket_service.create_ticket(db, current_user, ticket_in)
    return {
        "id": ticket.id,
        "ticket_code": ticket.ticket_code,
        "title": ticket.title,
        "description": ticket.description,
        "category": ticket.category,
        "priority": ticket.priority,
        "status": ticket.status,
        "created_by": ticket.created_by,
        "creator_full_name": current_user.full_name,
        "creator_email": current_user.email,
        "assigned_to": ticket.assigned_to,
        "assignee_full_name": None,
        "chat_session_id": ticket.chat_session_id,
        "resolution_notes": ticket.resolution_notes,
        "created_at": ticket.created_at,
        "updated_at": ticket.updated_at,
        "comment_count": 0,
    }


@router.get(
    "",
    response_model=List[TicketResponse],
    summary="Lấy danh sách các yêu cầu hỗ trợ Ticket"
)
def list_tickets(
    ticket_status: Optional[str] = Query(None, alias="status", description="Lọc theo trạng thái"),
    category: Optional[str] = Query(None, description="Lọc theo loại sự cố"),
    priority: Optional[str] = Query(None, description="Lọc theo mức ưu tiên"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ticket_service.get_tickets(
        db=db,
        user=current_user,
        ticket_status=ticket_status,
        category=category,
        priority=priority,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{ticket_id}",
    response_model=TicketDetailResponse,
    summary="Xem chi tiết ticket và danh sách trao đổi"
)
def get_ticket_detail(
    ticket_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ticket_service.get_ticket_by_id(db, ticket_id, current_user)


@router.patch(
    "/{ticket_id}/status",
    response_model=TicketResponse,
    summary="Cập nhật trạng thái và phương án giải quyết ticket"
)
def update_ticket_status(
    ticket_id: uuid.UUID,
    status_in: TicketStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = ticket_service.update_status(db, ticket_id, current_user, status_in)
    return {
        "id": ticket.id,
        "ticket_code": ticket.ticket_code,
        "title": ticket.title,
        "description": ticket.description,
        "category": ticket.category,
        "priority": ticket.priority,
        "status": ticket.status,
        "created_by": ticket.created_by,
        "creator_full_name": ticket.creator.full_name if ticket.creator else None,
        "creator_email": ticket.creator.email if ticket.creator else None,
        "assigned_to": ticket.assigned_to,
        "assignee_full_name": ticket.assignee.full_name if ticket.assignee else None,
        "chat_session_id": ticket.chat_session_id,
        "resolution_notes": ticket.resolution_notes,
        "created_at": ticket.created_at,
        "updated_at": ticket.updated_at,
        "comment_count": len(ticket.comments) if ticket.comments else 0,
    }


@router.patch(
    "/{ticket_id}/assign",
    response_model=TicketResponse,
    summary="Phân công Quản trị viên IT phụ trách xử lý ticket"
)
def assign_ticket(
    ticket_id: uuid.UUID,
    assign_in: TicketAssignUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = ticket_service.assign_ticket(db, ticket_id, current_user, assign_in)
    return {
        "id": ticket.id,
        "ticket_code": ticket.ticket_code,
        "title": ticket.title,
        "description": ticket.description,
        "category": ticket.category,
        "priority": ticket.priority,
        "status": ticket.status,
        "created_by": ticket.created_by,
        "creator_full_name": ticket.creator.full_name if ticket.creator else None,
        "creator_email": ticket.creator.email if ticket.creator else None,
        "assigned_to": ticket.assigned_to,
        "assignee_full_name": ticket.assignee.full_name if ticket.assignee else None,
        "chat_session_id": ticket.chat_session_id,
        "resolution_notes": ticket.resolution_notes,
        "created_at": ticket.created_at,
        "updated_at": ticket.updated_at,
        "comment_count": len(ticket.comments) if ticket.comments else 0,
    }


@router.post(
    "/{ticket_id}/comments",
    response_model=TicketCommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Thêm phản hồi hoặc ghi chú kỹ thuật trong ticket"
)
def add_ticket_comment(
    ticket_id: uuid.UUID,
    comment_in: TicketCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comment = ticket_service.add_comment(db, ticket_id, current_user, comment_in)
    return {
        "id": comment.id,
        "ticket_id": comment.ticket_id,
        "user_id": comment.user_id,
        "user_full_name": current_user.full_name,
        "user_role": current_user.role.name if current_user.role else None,
        "content": comment.content,
        "is_internal": comment.is_internal,
        "created_at": comment.created_at,
    }
