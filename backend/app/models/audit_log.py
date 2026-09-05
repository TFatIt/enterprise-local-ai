"""Audit Log Model for Enterprise Compliance and Security Monitoring."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.db.base import Base, GUID


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    target_user_id = Column(GUID, nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)      # USER_LOGIN, USER_CREATE, USER_LOCK, etc.
    resource = Column(String(100), nullable=False)                # AUTH, DOCUMENTS, TICKETS, USERS
    result = Column(String(20), default="SUCCESS", nullable=False) # SUCCESS, FAILED
    details = Column(JSON, default=dict, nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs", lazy="joined")

    def __repr__(self) -> str:
        return f"<AuditLog action={self.action} resource={self.resource}>"
