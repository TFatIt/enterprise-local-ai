"""Export all SQLAlchemy models for registry and migrations."""

from app.models.role import Role
from app.models.department import Department
from app.models.user import User
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.chat import ChatSession, ChatMessage
from app.models.ticket import Ticket, TicketComment
from app.models.audit_log import AuditLog
from app.models.document_permission import DocumentPermission
from app.models.department_permission import DepartmentPermission
from app.models.document_version import DocumentVersion

from app.models.permission import Permission, role_permissions

__all__ = [
    "Role",
    "Department",
    "User",
    "Permission",
    "role_permissions",
    "Document",
    "DocumentChunk",
    "DocumentPermission",
    "DepartmentPermission",
    "DocumentVersion",
    "ChatSession",
    "ChatMessage",
    "Ticket",
    "TicketComment",
    "AuditLog",
]
