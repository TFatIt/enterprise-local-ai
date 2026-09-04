"""Pydantic Schemas for IT Support Tickets and Comments."""

import uuid
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class TicketCommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=3000, description="Nội dung phản hồi hoặc ghi chú kỹ thuật")
    is_internal: bool = Field(False, description="Ghi chú nội bộ chỉ IT Admin và Super Admin nhìn thấy")


class TicketCommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ticket_id: uuid.UUID
    user_id: uuid.UUID
    user_full_name: Optional[str] = None
    user_role: Optional[str] = None
    content: str
    is_internal: bool
    created_at: datetime


class TicketCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255, description="Tiêu đề sự cố hoặc yêu cầu hỗ trợ")
    description: str = Field(..., min_length=5, description="Mô tả chi tiết sự cố")
    category: str = Field("GENERAL", description="Phân loại sự cố: NETWORK, HARDWARE, SOFTWARE, ACCOUNT, GENERAL")
    priority: str = Field("MEDIUM", description="Mức độ ưu tiên: LOW, MEDIUM, HIGH, URGENT")
    chat_session_id: Optional[uuid.UUID] = Field(None, description="ID phiên chat AI dẫn tới việc mở ticket")


class TicketStatusUpdate(BaseModel):
    status: str = Field(..., description="Trạng thái mới: OPEN, IN_PROGRESS, WAITING, RESOLVED, CLOSED")
    resolution_notes: Optional[str] = Field(None, description="Ghi chú phương án xử lý / giải pháp khắc phục")


class TicketAssignUpdate(BaseModel):
    assigned_to: Optional[uuid.UUID] = Field(..., description="ID của IT Admin được phân công xử lý")


class TicketUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[uuid.UUID] = None
    resolution_notes: Optional[str] = None


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ticket_code: str
    title: str
    description: str
    category: str
    priority: str
    status: str
    created_by: uuid.UUID
    creator_full_name: Optional[str] = None
    creator_email: Optional[str] = None
    assigned_to: Optional[uuid.UUID] = None
    assignee_full_name: Optional[str] = None
    chat_session_id: Optional[uuid.UUID] = None
    resolution_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    comment_count: int = 0


class TicketDetailResponse(TicketResponse):
    comments: List[TicketCommentResponse] = []


class TicketAutoTriageRequest(BaseModel):
    title: str = Field(..., min_length=2, description="Tiêu đề sơ bộ của sự cố")
    description: str = Field(..., min_length=2, description="Mô tả hiện tượng lỗi gặp phải")


class TicketAutoTriageResponse(BaseModel):
    suggested_category: str = Field(..., description="NETWORK, HARDWARE, SOFTWARE, ACCOUNT, GENERAL")
    suggested_priority: str = Field(..., description="LOW, MEDIUM, HIGH, URGENT")
    reasoning: str = Field(..., description="Giải thích lý do phân loại của AI")
    suggested_initial_actions: List[str] = Field(default_factory=list, description="Các bước khắc phục sơ bộ nhân viên có thể thử")

