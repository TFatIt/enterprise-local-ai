import os
from typing import List, Optional
from uuid import UUID
from urllib.parse import quote
from fastapi import APIRouter, Depends, UploadFile, File, Form, Query, Request, status, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_active_user, require_role, oauth2_scheme
from app.core.security import decode_token
from app.schemas.document import (
    DocumentResponse,
    DocumentChunkResponse,
    DocumentUpdate,
    DocumentPermissionItem,
    DocumentPermissionCreate,
    DocumentVersionResponse,
)
from app.services.document_service import document_service
from app.services.permission_service import permission_service
from app.services.audit_service import audit_service
from app.models.user import User
from app.models.document import Document
from app.models.audit_log import AuditLog

router = APIRouter()


def _serialize_document(doc: Document, user: User, db: Session) -> DocumentResponse:
    """Helper serializer calculating contextual user permissions on document."""
    can_edit = permission_service.can_user_access_document(db, user, doc, "EDIT")
    can_del = permission_service.can_user_access_document(db, user, doc, "DELETE")
    can_manage = permission_service.can_user_access_document(db, user, doc, "MANAGE")

    return DocumentResponse(
        id=doc.id,
        title=doc.title,
        file_name=doc.file_name,
        file_type=doc.file_type,
        file_size=doc.file_size,
        department_id=doc.department_id,
        department_name=doc.department.name if doc.department else "Chung toàn công ty",
        department_code=doc.department.code if doc.department else "GENERAL",
        document_type=doc.document_type or "POLICY",
        category=doc.category or "Chung",
        owner_id=doc.owner_id,
        owner_name=doc.owner.full_name if doc.owner else None,
        uploaded_by=doc.uploaded_by,
        uploader_name=doc.uploader.full_name if doc.uploader else None,
        security_level=doc.security_level or "DEPARTMENT",
        visibility=doc.visibility if doc.visibility is not None else True,
        version=doc.version or "1.0",
        status=doc.status,
        rag_status=doc.rag_status or "READY",
        total_chunks=doc.total_chunks,
        error_message=doc.error_message,
        approved_at=doc.approved_at,
        approved_by=doc.approved_by,
        approved_by_name=doc.approver.full_name if doc.approver else None,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        can_edit=can_edit,
        can_delete=can_del,
        can_manage_permissions=can_manage,
    )


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Nạp tài liệu mới với Metadata và Mức độ Bảo mật",
    description="Tải lên tệp PDF, DOCX, TXT kèm phòng ban, phân loại và mức độ bảo mật."
)
def upload_document(
    request: Request,
    file: UploadFile = File(...),
    title: str = Form(...),
    department_id: Optional[int] = Form(None),
    document_type: str = Form("POLICY"),
    category: str = Form("Chung"),
    security_level: str = Form("DEPARTMENT"),
    version: str = Form("1.0"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> DocumentResponse:
    """Upload and process document with Access Control validation."""
    client_ip = request.client.host if request.client else None
    doc = document_service.upload_document(
        db=db,
        file=file,
        title=title,
        department_id=department_id,
        current_user=current_user,
        document_type=document_type,
        category=category,
        security_level=security_level,
        version=version,
        ip_address=client_ip
    )
    return _serialize_document(doc, current_user, db)


@router.get(
    "",
    response_model=List[DocumentResponse],
    summary="Danh sách tài liệu được cấp quyền",
    description="Truy vấn danh mục tài liệu theo phân quyền Role, Department và Security Level."
)
def list_documents(
    request: Request,
    search: Optional[str] = Query(None, description="Tìm kiếm theo tiêu đề, tên file, danh mục"),
    department_id: Optional[int] = Query(None, description="Lọc theo phòng ban"),
    document_type: Optional[str] = Query(None, description="Lọc theo loại tài liệu (SOP, POLICY, GUIDE...)"),
    category: Optional[str] = Query(None, description="Lọc theo danh mục nghiệp vụ"),
    security_level: Optional[str] = Query(None, description="Lọc theo bảo mật (PUBLIC, INTERNAL, DEPARTMENT, CONFIDENTIAL)"),
    rag_status: Optional[str] = Query(None, description="Lọc theo trạng thái RAG (READY, PROCESSING, FAILED)"),
    status_filter: Optional[str] = Query(None, alias="status", description="Lọc theo trạng thái"),
    owner_id: Optional[UUID] = Query(None, description="Lọc theo người sở hữu"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[DocumentResponse]:
    """Retrieve filtered catalog of permitted documents for authenticated user."""
    client_ip = request.client.host if request.client else None
    docs = document_service.list_documents(
        db=db,
        current_user=current_user,
        search=search,
        department_id=department_id,
        document_type=document_type,
        category=category,
        security_level=security_level,
        rag_status=rag_status,
        status_filter=status_filter,
        owner_id=owner_id,
        ip_address=client_ip
    )
    return [_serialize_document(d, current_user, db) for d in docs]


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Xem chi tiết tài liệu",
    description="Xem metadata chi tiết tài liệu sau khi kiểm tra quyền VIEW."
)
def get_document(
    document_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> DocumentResponse:
    """Fetch single document metadata with access verification."""
    client_ip = request.client.host if request.client else None
    doc = document_service.get_document_by_id(db, document_id, current_user, ip_address=client_ip)
    return _serialize_document(doc, current_user, db)


@router.get(
    "/{document_id}/file",
    summary="Mở hoặc tải về tệp tin tài liệu gốc",
    description="Tải tệp tin gốc (.pdf, .docx, .txt) hoặc mở xem trực tiếp trên trình duyệt sau khi kiểm tra quyền VIEW."
)
def get_document_file(
    document_id: UUID,
    request: Request,
    download: bool = Query(False, description="True để tải tệp về, False để mở inline trên trình duyệt"),
    token: Optional[str] = Query(None, description="Token xác thực khi mở trực tiếp qua URL"),
    header_token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """Serve the raw file content with Enterprise VIEW access check."""
    auth_token = token or header_token
    if not auth_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chưa xác thực hoặc phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại."
        )

    payload = decode_token(auth_token)
    if not payload or payload.get("token_type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc đã hết hạn."
        )

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản không tồn tại hoặc đã bị khóa."
        )

    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy tài liệu yêu cầu."
        )

    # Enforce VIEW permission
    if not permission_service.can_user_access_document(db, user, doc, "VIEW"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền truy cập tệp tin này."
        )

    if not doc.file_path or not os.path.exists(doc.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tệp tin không tồn tại trên hệ thống lưu trữ máy chủ."
        )

    # Determine MIME type
    _, ext = os.path.splitext(doc.file_name or "")
    ext_lower = ext.lower()
    media_types = {
        ".pdf": "application/pdf",
        ".txt": "text/plain; charset=utf-8",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".doc": "application/msword",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xls": "application/vnd.ms-excel",
        ".csv": "text/csv; charset=utf-8",
    }
    media_type = media_types.get(ext_lower, "application/octet-stream")

    disposition = "attachment" if download else "inline"
    encoded_filename = quote(doc.file_name or f"document_{doc.id}{ext_lower}")
    resp_headers = {
        "Content-Disposition": f'{disposition}; filename="{encoded_filename}"; filename*=UTF-8\'\'{encoded_filename}'
    }

    # Audit log event
    client_ip = request.client.host if request.client else None
    audit_service.log_event(
        db=db,
        action="DOWNLOAD" if download else "VIEW",
        resource="DOCUMENTS",
        user_id=user.id,
        ip_address=client_ip,
        details={"document_id": str(doc.id), "title": doc.title, "file_name": doc.file_name}
    )

    return FileResponse(
        path=doc.file_path,
        media_type=media_type,
        filename=doc.file_name,
        headers=resp_headers
    )


@router.get(
    "/{document_id}/download",
    summary="Tải về tệp tin tài liệu gốc",
    description="Tải tệp tin gốc trực tiếp về máy tính (attachment)."
)
def download_document_file(
    document_id: UUID,
    request: Request,
    token: Optional[str] = Query(None),
    header_token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """Convenience alias endpoint to force download of original document file."""
    return get_document_file(
        document_id=document_id,
        request=request,
        download=True,
        token=token,
        header_token=header_token,
        db=db,
    )


@router.put(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Cập nhật thông tin tài liệu",
    description="Chỉnh sửa tiêu đề, phân loại, bảo mật, phiên bản của tài liệu."
)
def update_document(
    document_id: UUID,
    update_in: DocumentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> DocumentResponse:
    """Update document metadata with EDIT authorization check."""
    client_ip = request.client.host if request.client else None
    doc = document_service.update_document(db, document_id, current_user, update_in, ip_address=client_ip)
    return _serialize_document(doc, current_user, db)


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_200_OK,
    summary="Xóa tài liệu và vector chunks",
    description="Xóa vĩnh viễn tệp, vector ChromaDB và dữ liệu sau khi kiểm tra quyền DELETE."
)
def delete_document(
    document_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete document with authorization check."""
    client_ip = request.client.host if request.client else None
    document_service.delete_document(db, document_id, current_user, ip_address=client_ip)
    return {"success": True, "message": "Tài liệu và các đoạn vector đã được xóa thành công."}


@router.get(
    "/{document_id}/chunks",
    response_model=List[DocumentChunkResponse],
    summary="Danh sách các đoạn trích (Chunks) của tài liệu"
)
def get_document_chunks(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[DocumentChunkResponse]:
    """Inspect generated chunks for a document with access control."""
    chunks = document_service.get_document_chunks(db, document_id, current_user)
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


@router.get(
    "/{document_id}/permissions",
    response_model=List[DocumentPermissionItem],
    summary="Lấy danh sách phân quyền cụ thể của tài liệu"
)
def get_document_permissions(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[DocumentPermissionItem]:
    """Fetch all explicit user/role permissions on document."""
    perms = document_service.get_document_permissions(db, document_id, current_user)
    return [
        DocumentPermissionItem(
            id=p.id,
            document_id=p.document_id,
            user_id=p.user_id,
            user_name=p.user.full_name if p.user else None,
            user_email=p.user.email if p.user else None,
            role_id=p.role_id,
            role_code=p.role.code if p.role else None,
            role_name=p.role.name if p.role else None,
            permission_type=p.permission_type,
            created_at=p.created_at,
        )
        for p in perms
    ]


@router.post(
    "/{document_id}/permissions",
    response_model=DocumentPermissionItem,
    status_code=status.HTTP_201_CREATED,
    summary="Cấp quyền cụ thể cho User hoặc Role trên tài liệu"
)
def add_document_permission(
    document_id: UUID,
    perm_in: DocumentPermissionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> DocumentPermissionItem:
    """Grant explicit VIEW, EDIT, or MANAGE permission on document."""
    client_ip = request.client.host if request.client else None
    p = document_service.add_document_permission(db, document_id, current_user, perm_in, ip_address=client_ip)
    return DocumentPermissionItem(
        id=p.id,
        document_id=p.document_id,
        user_id=p.user_id,
        user_name=p.user.full_name if p.user else None,
        user_email=p.user.email if p.user else None,
        role_id=p.role_id,
        role_code=p.role.code if p.role else None,
        role_name=p.role.name if p.role else None,
        permission_type=p.permission_type,
        created_at=p.created_at,
    )


@router.delete(
    "/{document_id}/permissions/{permission_id}",
    status_code=status.HTTP_200_OK,
    summary="Thu hồi quyền cụ thể trên tài liệu"
)
def delete_document_permission(
    document_id: UUID,
    permission_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Revoke explicit permission from document."""
    client_ip = request.client.host if request.client else None
    document_service.delete_document_permission(db, document_id, permission_id, current_user, ip_address=client_ip)
    return {"success": True, "message": "Thu hồi quyền thành công."}


@router.get(
    "/{document_id}/versions",
    response_model=List[DocumentVersionResponse],
    summary="Lịch sử các phiên bản của tài liệu"
)
def get_document_versions(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[DocumentVersionResponse]:
    """Retrieve version history records for document."""
    versions = document_service.get_document_versions(db, document_id, current_user)
    return [
        DocumentVersionResponse(
            id=v.id,
            document_id=v.document_id,
            version_number=v.version_number,
            file_name=v.file_name,
            file_size=v.file_size,
            change_notes=v.change_notes,
            created_by=v.created_by,
            creator_name=v.creator.full_name if v.creator else None,
            created_at=v.created_at,
        )
        for v in versions
    ]


@router.post(
    "/{document_id}/reindex",
    response_model=DocumentResponse,
    summary="Tái tạo chỉ mục ChromaDB (Re-index)"
)
def reindex_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN", "ADMIN", "IT_ADMIN"]))
) -> DocumentResponse:
    """Force re-extract text, recreate chunks, and re-embed in ChromaDB."""
    doc = document_service.process_and_chunk_document(db, document_id)
    return _serialize_document(doc, current_user, db)


@router.get(
    "/audit-logs/recent",
    summary="Lấy lịch sử kiểm toán gần đây (Admin & Management)"
)
def get_document_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN", "ADMIN", "MANAGER", "IT_ADMIN"]))
):
    """Retrieve recent document security & access audit logs."""
    logs = db.query(AuditLog).filter(
        AuditLog.resource == "DOCUMENTS"
    ).order_by(AuditLog.created_at.desc()).limit(limit).all()

    return [
        {
            "id": l.id,
            "user_id": l.user_id,
            "user_name": l.user.full_name if l.user else "Hệ thống",
            "action": l.action,
            "resource": l.resource,
            "details": l.details,
            "ip_address": l.ip_address,
            "created_at": l.created_at,
        }
        for l in logs
    ]
