"""Document Permission Model for Granular Access Control."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base, GUID


class DocumentPermission(Base):
    __tablename__ = "document_permissions"

    id = Column(GUID, primary_key=True, default=uuid.uuid4, index=True)
    document_id = Column(GUID, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=True, index=True)
    permission_type = Column(String(20), default="VIEW", nullable=False)  # VIEW, EDIT, MANAGE
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    created_by = Column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    document = relationship("Document", back_populates="permissions")
    user = relationship("User", foreign_keys=[user_id], lazy="joined")
    role = relationship("Role", foreign_keys=[role_id], lazy="joined")

    def __repr__(self) -> str:
        return f"<DocumentPermission doc={self.document_id} user={self.user_id} role={self.role_id} type={self.permission_type}>"
