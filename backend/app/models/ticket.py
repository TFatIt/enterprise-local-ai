"""Ticket and TicketComment Models for IT Support Helpdesk."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base, GUID


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(GUID, primary_key=True, default=uuid.uuid4, index=True)
    ticket_code = Column(String(30), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), default="GENERAL", nullable=False)     # NETWORK, HARDWARE, SOFTWARE, ACCOUNT, GENERAL
    priority = Column(String(20), default="MEDIUM", nullable=False)      # LOW, MEDIUM, HIGH, URGENT
    status = Column(String(20), default="OPEN", nullable=False, index=True)  # OPEN, IN_PROGRESS, WAITING, RESOLVED, CLOSED
    created_by = Column(GUID, ForeignKey("users.id"), nullable=False, index=True)
    assigned_to = Column(GUID, ForeignKey("users.id"), nullable=True, index=True)
    chat_session_id = Column(GUID, ForeignKey("chat_sessions.id"), nullable=True, index=True)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    creator = relationship("User", foreign_keys=[created_by], back_populates="tickets_created", lazy="joined")
    assignee = relationship("User", foreign_keys=[assigned_to], back_populates="tickets_assigned", lazy="joined")
    chat_session = relationship("ChatSession", back_populates="tickets", lazy="joined")
    comments = relationship(
        "TicketComment",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="TicketComment.created_at",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Ticket code={self.ticket_code} status={self.status}>"


class TicketComment(Base):
    __tablename__ = "ticket_comments"

    id = Column(GUID, primary_key=True, default=uuid.uuid4, index=True)
    ticket_id = Column(GUID, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    ticket = relationship("Ticket", back_populates="comments", lazy="joined")
    user = relationship("User", back_populates="ticket_comments", lazy="joined")

    def __repr__(self) -> str:
        return f"<TicketComment ticket={self.ticket_id} user={self.user_id}>"
