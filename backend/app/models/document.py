"""Document Model for Enterprise Knowledge Base."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, BigInteger, Text, DateTime, ForeignKey, Boolean
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
    document_type = Column(String(50), default="POLICY", nullable=False, index=True)  # SOP, POLICY, PROCEDURE, GUIDE, MANUAL, REPORT, FORM
    category = Column(String(100), default="Chung", nullable=False, index=True)
    owner_id = Column(GUID, ForeignKey("users.id"), nullable=True, index=True)
    uploaded_by = Column(GUID, ForeignKey("users.id"), nullable=False, index=True)
    security_level = Column(String(50), default="DEPARTMENT", nullable=False, index=True)  # PUBLIC, INTERNAL, DEPARTMENT, CONFIDENTIAL
    visibility = Column(Boolean, default=True, nullable=False)
    version = Column(String(20), default="1.0", nullable=False)
    status = Column(String(30), default="UPLOADED", nullable=False, index=True)  # UPLOADED, PROCESSING, INDEXED, FAILED
    rag_status = Column(String(30), default="READY", nullable=False, index=True)  # READY, PROCESSING, FAILED, NOT_INDEXED
    total_chunks = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(GUID, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    department = relationship("Department", back_populates="documents", lazy="joined")
    uploader = relationship("User", foreign_keys=[uploaded_by], back_populates="documents_uploaded", lazy="joined")
    owner = relationship("User", foreign_keys=[owner_id], lazy="joined")
    approver = relationship("User", foreign_keys=[approved_by], lazy="joined")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan", lazy="select")
    permissions = relationship("DocumentPermission", back_populates="document", cascade="all, delete-orphan", lazy="select")
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan", lazy="select")

    def __repr__(self) -> str:
        return f"<Document title={self.title} status={self.status} security={self.security_level}>"
