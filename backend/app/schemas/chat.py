"""Pydantic Schemas for AI Chat Sessions and Messages."""

import uuid
from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class SourceItem(BaseModel):
    source_index: int
    document_id: Optional[str] = None
    document_title: str
    file_name: str
    page_number: int = 1
    similarity_score: float
    snippet: str


class ChatMessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000, description="Nội dung câu hỏi của người dùng")


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    sender_type: str
    content: str
    sources: List[Dict[str, Any]] = []
    suggest_ticket: bool = False
    response_time_ms: Optional[int] = None
    created_at: datetime


class ChatSessionCreate(BaseModel):
    title: Optional[str] = Field(None, max_length=255, description="Tiêu đề phiên hội thoại")


class ChatSessionUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None


class ChatSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


class ChatSessionDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessageResponse] = []


class MessageFeedbackCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Đánh giá từ 1 đến 5 sao hoặc 1 (dislike) / 5 (like)")
    comment: Optional[str] = Field(None, max_length=1000, description="Ý kiến đóng góp chi tiết")
