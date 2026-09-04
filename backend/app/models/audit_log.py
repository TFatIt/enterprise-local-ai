"""Audit Log Model for Enterprise Compliance and Security Monitoring."""

from datetime import datetime, timezone
from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.db.base import Base, GUID


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)      # USER_LOGIN, DOC_UPLOAD, DOC_DELETE, etc.
    resource = Column(String(100), nullable=False)                # AUTH, DOCUMENTS, TICKETS, USERS
    details = Column(JSON, default=dict, nullable=False)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs", lazy="joined")

    def __repr__(self) -> str:
        return f"<AuditLog action={self.action} resource={self.resource}>"
