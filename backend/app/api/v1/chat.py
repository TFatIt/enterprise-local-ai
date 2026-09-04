"""API Router for Chat Sessions and AI Messages."""

import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.chat import (
    ChatSessionCreate,
    ChatSessionUpdate,
    ChatSessionResponse,
    ChatSessionDetailResponse,
    ChatMessageCreate,
    ChatMessageResponse,
)
from app.services.chat_service import chat_service

router = APIRouter()


@router.post(
    "/sessions",
    response_model=ChatSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo phiên hội thoại mới"
)
def create_chat_session(
    session_in: ChatSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = chat_service.create_session(db, current_user, session_in)
    return {
        "id": session.id,
        "user_id": session.user_id,
        "title": session.title,
        "is_active": session.is_active,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "message_count": 0,
    }


@router.get(
    "/sessions",
    response_model=List[ChatSessionResponse],
    summary="Lấy danh sách các phiên hội thoại của người dùng"
)
def list_chat_sessions(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return chat_service.get_user_sessions(db, current_user, skip=skip, limit=limit)


@router.get(
    "/sessions/{session_id}",
    response_model=ChatSessionDetailResponse,
    summary="Xem chi tiết một phiên hội thoại và toàn bộ tin nhắn"
)
def get_chat_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return chat_service.get_session_by_id(db, session_id, current_user)


@router.put(
    "/sessions/{session_id}",
    response_model=ChatSessionResponse,
    summary="Cập nhật tiêu đề hoặc trạng thái phiên hội thoại"
)
def update_chat_session(
    session_id: uuid.UUID,
    update_in: ChatSessionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = chat_service.update_session(db, session_id, current_user, update_in)
    return {
        "id": session.id,
        "user_id": session.user_id,
        "title": session.title,
        "is_active": session.is_active,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "message_count": len(session.messages) if session.messages else 0,
    }


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa vĩnh viễn một phiên hội thoại và toàn bộ tin nhắn"
)
def delete_chat_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chat_service.delete_session(db, session_id, current_user)
    return None


@router.post(
    "/sessions/{session_id}/messages",
    response_model=ChatMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Gửi câu hỏi của người dùng và nhận câu trả lời từ Trợ lý AI RAG"
)
def send_chat_message(
    session_id: uuid.UUID,
    message_in: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return chat_service.send_message(db, session_id, current_user, message_in)


from fastapi.responses import StreamingResponse

@router.post(
    "/sessions/{session_id}/messages/stream",
    summary="Gửi câu hỏi và nhận câu trả lời dạng Streaming SSE thời gian thực"
)
def send_chat_message_stream(
    session_id: uuid.UUID,
    message_in: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stream_generator = chat_service.send_message_stream(db, session_id, current_user, message_in)
    return StreamingResponse(
        stream_generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get(
    "/sessions/{session_id}/messages",
    response_model=List[ChatMessageResponse],
    summary="Lấy danh sách tin nhắn trong một phiên hội thoại"
)
def get_session_messages(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = chat_service.get_session_by_id(db, session_id, current_user)
    return session.messages
