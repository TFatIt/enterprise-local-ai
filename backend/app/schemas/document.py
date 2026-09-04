"""Pydantic schemas for Document and Chunk management."""

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
    uploaded_by: UUID
    status: str
    total_chunks: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

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
