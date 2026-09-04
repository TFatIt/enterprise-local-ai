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
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    role = relationship("Role", back_populates="users", lazy="joined")
    department = relationship("Department", back_populates="users", lazy="joined")
    documents_uploaded = relationship("Document", back_populates="uploader", lazy="selectin")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan", lazy="selectin")
    tickets_created = relationship("Ticket", foreign_keys="Ticket.created_by", back_populates="creator", lazy="selectin")
    tickets_assigned = relationship("Ticket", foreign_keys="Ticket.assigned_to", back_populates="assignee", lazy="selectin")
    ticket_comments = relationship("TicketComment", back_populates="user", lazy="selectin")
    audit_logs = relationship("AuditLog", back_populates="user", lazy="selectin")

    def __repr__(self) -> str:
        return f"<User username={self.username} email={self.email}>"
