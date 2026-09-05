"""Pydantic schemas for Enterprise Document Access Control and Lifecycle."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class DocumentResponse(BaseModel):
    id: UUID
    title: str
    file_name: str
    file_type: str
    file_size: int
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    department_code: Optional[str] = None
    document_type: str = "POLICY"
    category: str = "Chung"
    owner_id: Optional[UUID] = None
    owner_name: Optional[str] = None
    uploaded_by: UUID
    uploader_name: Optional[str] = None
    security_level: str = "DEPARTMENT"  # PUBLIC, INTERNAL, DEPARTMENT, CONFIDENTIAL
    visibility: bool = True
    version: str = "1.0"
    status: str = "UPLOADED"
    rag_status: str = "READY"
    total_chunks: int = 0
    error_message: Optional[str] = None
    approved_at: Optional[datetime] = None
    approved_by: Optional[UUID] = None
    approved_by_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    can_edit: bool = False
    can_delete: bool = False
    can_manage_permissions: bool = False

    model_config = ConfigDict(from_attributes=True)


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    department_id: Optional[int] = None
    document_type: Optional[str] = None
    category: Optional[str] = None
    security_level: Optional[str] = None
    visibility: Optional[bool] = None
    version: Optional[str] = None
    owner_id: Optional[UUID] = None


class DocumentPermissionItem(BaseModel):
    id: UUID
    document_id: UUID
    user_id: Optional[UUID] = None
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    role_id: Optional[int] = None
    role_code: Optional[str] = None
    role_name: Optional[str] = None
    permission_type: str = "VIEW"  # VIEW, EDIT, MANAGE
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentPermissionCreate(BaseModel):
    user_id: Optional[UUID] = None
    role_id: Optional[int] = None
    permission_type: str = "VIEW"  # VIEW, EDIT, MANAGE


class DocumentVersionResponse(BaseModel):
    id: UUID
    document_id: UUID
    version_number: str
    file_name: str
    file_size: int
    change_notes: Optional[str] = None
    created_by: Optional[UUID] = None
    creator_name: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentChunkResponse(BaseModel):
    id: UUID
    document_id: UUID
    chunk_index: int
    content: str
    metadata_json: Dict[str, Any]
    chroma_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
