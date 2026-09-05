"""Pydantic Schemas for Admin Dashboard & Analytics."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class DashboardSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_users: int
    total_departments: int
    total_documents: int
    total_chunks: int
    total_chat_sessions: int
    total_questions: int
    total_tickets: int
    open_tickets: int
    resolved_tickets: int
    ai_resolution_rate: float
    avg_response_time_ms: int


class CategoryCount(BaseModel):
    category: str
    count: int


class StatusCount(BaseModel):
    status: str
    count: int


class PriorityCount(BaseModel):
    priority: str
    count: int


class RecentActivityItem(BaseModel):
    type: str  # TICKET, DOCUMENT, CHAT
    title: str
    user_name: str
    created_at: datetime


class DashboardAnalyticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    summary: DashboardSummary
    tickets_by_category: List[CategoryCount]
    tickets_by_status: List[StatusCount]
    tickets_by_priority: List[PriorityCount]
    recent_activities: List[RecentActivityItem]


class KnowledgeGapItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    topic: str
    sample_query: str
    department_code: str
    department_name: str
    query_count: int
    last_queried_at: str
    suggested_action: str
    status: str  # OPEN, RESOLVED
    has_matching_doc: bool


class KnowledgeGapResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_gaps: int
    open_gaps: int
    resolved_gaps: int
    items: List[KnowledgeGapItem]
