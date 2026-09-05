"""Document Version Model for Version History Tracking."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, BigInteger, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base, GUID


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(GUID, primary_key=True, default=uuid.uuid4, index=True)
    document_id = Column(GUID, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(String(20), nullable=False)
    file_name = Column(String(255), nullable=False)
    stored_file_name = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    change_notes = Column(Text, nullable=True)
    created_by = Column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    document = relationship("Document", back_populates="versions")
    creator = relationship("User", foreign_keys=[created_by], lazy="joined")

    def __repr__(self) -> str:
        return f"<DocumentVersion doc={self.document_id} ver={self.version_number}>"
