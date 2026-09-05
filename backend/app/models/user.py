"""User Model for Enterprise Employees and Administrators."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base, GUID


class User(Base):
    __tablename__ = "users"

    id = Column(GUID, primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=False)
    employee_code = Column(String(50), unique=True, nullable=True, index=True)
    phone = Column(String(30), nullable=True)
    position = Column(String(100), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False, index=True)
    status = Column(String(20), default="ACTIVE", nullable=False, index=True)  # ACTIVE, INACTIVE, LOCKED, SUSPENDED, PENDING
    avatar = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    force_password_change = Column(Boolean, default=False, nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    created_by = Column(GUID, nullable=True)
    updated_by = Column(GUID, nullable=True)
    deleted_by = Column(GUID, nullable=True)

    # Relationships
    role = relationship("Role", back_populates="users", lazy="joined")
    department = relationship("Department", back_populates="users", lazy="joined")
    documents_uploaded = relationship("Document", foreign_keys="Document.uploaded_by", back_populates="uploader", lazy="select")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan", lazy="select")
    tickets_created = relationship("Ticket", foreign_keys="Ticket.created_by", back_populates="creator", lazy="select")
    tickets_assigned = relationship("Ticket", foreign_keys="Ticket.assigned_to", back_populates="assignee", lazy="select")
    ticket_comments = relationship("TicketComment", back_populates="user", lazy="select")
    audit_logs = relationship("AuditLog", back_populates="user", lazy="select")

    def __repr__(self) -> str:
        return f"<User username={self.username} email={self.email}>"
