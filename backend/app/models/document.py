"""Document Model for Enterprise Knowledge Base."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, BigInteger, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base, GUID


class Document(Base):
    __tablename__ = "documents"

    id = Column(GUID, primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String(255), nullable=False)
    file_name = Column(String(255), nullable=False)
    stored_file_name = Column(String(255), unique=True, nullable=False, index=True)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(20), nullable=False)  # PDF, DOCX, TXT
    file_size = Column(BigInteger, nullable=False)   # in bytes
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True, index=True)
    uploaded_by = Column(GUID, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String(30), default="UPLOADED", nullable=False, index=True)  # UPLOADED, PROCESSING, INDEXED, FAILED
    total_chunks = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    department = relationship("Department", back_populates="documents", lazy="joined")
    uploader = relationship("User", back_populates="documents_uploaded", lazy="joined")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Document title={self.title} status={self.status}>"
