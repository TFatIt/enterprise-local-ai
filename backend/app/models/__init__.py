"""Export all SQLAlchemy models for registry and migrations."""

from app.models.role import Role
from app.models.department import Department
from app.models.user import User
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.chat import ChatSession, ChatMessage
from app.models.ticket import Ticket, TicketComment
from app.models.audit_log import AuditLog

__all__ = [
    "Role",
    "Department",
    "User",
    "Document",
    "DocumentChunk",
    "ChatSession",
    "ChatMessage",
    "Ticket",
    "TicketComment",
    "AuditLog",
]
