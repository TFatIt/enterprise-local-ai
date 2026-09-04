"""Document management and upload API endpoints."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, UploadFile, File, Form, Query, status, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_active_user, require_role
from app.schemas.document import DocumentResponse, DocumentChunkResponse
from app.services.document_service import document_service
from app.models.user import User

router = APIRouter()


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tải lên tài liệu mới (IT Admin & Super Admin)",
    description="Upload tệp PDF, DOCX, TXT để hệ thống tự động bóc tách text và chia chunk."
)
def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    department_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN", "IT_ADMIN"]))
) -> DocumentResponse:
    """Upload and process document."""
    doc = document_service.upload_document(
        db=db,
        file=file,
        title=title,
        department_id=department_id,
        current_user=current_user
    )
    return DocumentResponse(
        id=doc.id,
        title=doc.title,
        file_name=doc.file_name,
        file_type=doc.file_type,
        file_size=doc.file_size,
        department_id=doc.department_id,
        department_name=doc.department.name if doc.department else None,
        uploaded_by=doc.uploaded_by,
        status=doc.status,
        total_chunks=doc.total_chunks,
        error_message=doc.error_message,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@router.get(
    "",
    response_model=List[DocumentResponse],
    summary="Danh sách tài liệu",
    description="Xem danh mục tài liệu và trạng thái Indexing."
)
def list_documents(
    department_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user)
) -> List[DocumentResponse]:
    """Retrieve all available documents."""
    docs = document_service.list_documents(db, department_id, status_filter)
    return [
        DocumentResponse(
            id=d.id,
            title=d.title,
            file_name=d.file_name,
            file_type=d.file_type,
            file_size=d.file_size,
            department_id=d.department_id,
            department_name=d.department.name if d.department else None,
            uploaded_by=d.uploaded_by,
            status=d.status,
            total_chunks=d.total_chunks,
            error_message=d.error_message,
            created_at=d.created_at,
            updated_at=d.updated_at,
        )
        for d in docs
    ]


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Chi tiết tài liệu"
)
def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user)
) -> DocumentResponse:
    """Retrieve document metadata."""
    doc = document_service.get_document_by_id(db, document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy tài liệu.")
    return DocumentResponse(
        id=doc.id,
        title=doc.title,
        file_name=doc.file_name,
        file_type=doc.file_type,
        file_size=doc.file_size,
        department_id=doc.department_id,
        department_name=doc.department.name if doc.department else None,
        uploaded_by=doc.uploaded_by,
        status=doc.status,
        total_chunks=doc.total_chunks,
        error_message=doc.error_message,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@router.get(
    "/{document_id}/chunks",
    response_model=List[DocumentChunkResponse],
    summary="Danh sách các đoạn trích (Chunks) của tài liệu"
)
def get_document_chunks(
    document_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user)
) -> List[DocumentChunkResponse]:
    """Inspect generated chunks for a document."""
    doc = document_service.get_document_by_id(db, document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy tài liệu.")
    chunks = document_service.get_document_chunks(db, document_id)
    return [
        DocumentChunkResponse(
            id=c.id,
            document_id=c.document_id,
            chunk_index=c.chunk_index,
            content=c.content,
            metadata_json=c.metadata_json,
            chroma_id=c.chroma_id,
            created_at=c.created_at,
        )
        for c in chunks
    ]


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_200_OK,
    summary="Xóa tài liệu (IT Admin & Super Admin)"
)
def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(["SUPER_ADMIN", "IT_ADMIN"]))
):
    """Delete document and its corresponding chunk records."""
    document_service.delete_document(db, document_id)
    return {"success": True, "message": "Tài liệu và các đoạn chunks đã được xóa thành công."}
