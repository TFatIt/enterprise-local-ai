"""Document storage, parsing orchestration, chunk lifecycle, and Enterprise Access Control service."""

import os
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.document_permission import DocumentPermission
from app.models.document_version import DocumentVersion
from app.models.user import User
from app.core.config import settings
from app.rag.parser import parser
from app.rag.chunker import chunker
from app.services.permission_service import permission_service
from app.services.audit_service import audit_service
from app.schemas.document import DocumentUpdate, DocumentPermissionCreate


class DocumentService:
    """Service handling document upload, storage, parsing, chunks, and Enterprise Access Control."""

    ALLOWED_EXTENSIONS = {
        ".pdf": "PDF",
        ".docx": "DOCX",
        ".txt": "TXT",
        ".xlsx": "XLSX",
        ".csv": "CSV",
        ".md": "TXT",
        ".bat": "TXT",
        ".ps1": "TXT",
        ".sh": "TXT",
        ".sql": "TXT",
        ".json": "TXT",
        ".log": "TXT",
        ".ini": "TXT",
        ".yaml": "TXT",
        ".yml": "TXT",
        # Image formats (processed via Ollama Vision AI)
        ".png": "IMAGE",
        ".jpg": "IMAGE",
        ".jpeg": "IMAGE",
        ".webp": "IMAGE",
        ".bmp": "IMAGE",
        ".gif": "IMAGE",
        ".tiff": "IMAGE",
        ".tif": "IMAGE",
        # Video formats (processed via keyframe extraction + Vision AI)
        ".mp4": "VIDEO",
        ".mkv": "VIDEO",
        ".avi": "VIDEO",
        ".mov": "VIDEO",
        ".webm": "VIDEO",
    }

    @staticmethod
    def _ensure_upload_dir() -> str:
        """Guarantee that upload directory exists."""
        upload_path = os.path.abspath(settings.UPLOAD_DIRECTORY)
        os.makedirs(upload_path, exist_ok=True)
        return upload_path

    @classmethod
    def upload_document(
        cls,
        db: Session,
        file: UploadFile,
        title: str,
        department_id: Optional[int],
        current_user: User,
        document_type: str = "POLICY",
        category: str = "Chung",
        security_level: str = "DEPARTMENT",
        version: str = "1.0",
        ip_address: Optional[str] = None
    ) -> Document:
        """Validate, store on disk, verify permissions, and register new document in database."""
        # 1. Validate permissions to upload into department
        if not permission_service.can_user_upload_to_department(current_user, department_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền nạp tài liệu vào phòng ban này."
            )

        # 2. Validate file extension
        _, ext = os.path.splitext(file.filename or "")
        ext_lower = ext.lower()
        if ext_lower not in cls.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Định dạng tệp '{ext}' không được hỗ trợ. Chấp nhận: .pdf, .docx, .txt, .md, .xlsx, .csv, .bat, .ps1, .sh, .sql, .json, .log"
            )

        file_type = cls.ALLOWED_EXTENSIONS[ext_lower]

        # 3. Prepare file destination
        upload_dir = cls._ensure_upload_dir()
        unique_file_id = uuid.uuid4()
        stored_file_name = f"{unique_file_id}{ext_lower}"
        target_path = os.path.join(upload_dir, stored_file_name)

        # 4. Stream content to disk and check file size
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        file_size = 0

        try:
            with open(target_path, "wb") as buffer:
                while chunk := file.file.read(1024 * 1024):
                    file_size += len(chunk)
                    if file_size > max_bytes:
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f"Dung lượng tệp vượt quá giới hạn tối đa ({settings.MAX_UPLOAD_SIZE_MB}MB)."
                        )
                    buffer.write(chunk)
        except Exception as e:
            if os.path.exists(target_path):
                os.remove(target_path)
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Lỗi khi lưu tệp tin: {str(e)}")

        # 5. Insert Document record
        doc = Document(
            id=unique_file_id,
            title=title.strip() if title else file.filename,
            file_name=file.filename or "unknown",
            stored_file_name=stored_file_name,
            file_path=target_path,
            file_type=file_type,
            file_size=file_size,
            department_id=department_id,
            document_type=document_type.strip() if document_type else "POLICY",
            category=category.strip() if category else "Chung",
            owner_id=current_user.id,
            uploaded_by=current_user.id,
            security_level=security_level.upper() if security_level else "DEPARTMENT",
            visibility=True,
            version=version.strip() if version else "1.0",
            status="UPLOADED",
            rag_status="READY",
            total_chunks=0,
        )
        db.add(doc)

        # 6. Record Initial Version Entry
        initial_version = DocumentVersion(
            document_id=doc.id,
            version_number=doc.version,
            file_name=doc.file_name,
            stored_file_name=doc.stored_file_name,
            file_size=doc.file_size,
            change_notes="Bản khởi tạo đầu tiên khi nạp tài liệu.",
            created_by=current_user.id,
        )
        db.add(initial_version)

        db.commit()
        db.refresh(doc)

        # 7. Audit log UPLOAD
        audit_service.log_event(
            db=db,
            action="UPLOAD",
            resource="DOCUMENTS",
            user_id=current_user.id,
            ip_address=ip_address,
            details={"document_id": str(doc.id), "title": doc.title, "security_level": doc.security_level}
        )

        # 8. Automatically trigger parsing and chunking
        try:
            cls.process_and_chunk_document(db, doc.id)
        except Exception as e:
            doc.status = "FAILED"
            doc.rag_status = "FAILED"
            doc.error_message = str(e)
            db.commit()

        return doc

    @classmethod
    def process_and_chunk_document(cls, db: Session, document_id: UUID) -> Document:
        """Extract text and generate chunks for a document with Enterprise ACL metadata."""
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu.")

        doc.status = "PROCESSING"
        doc.rag_status = "PROCESSING"
        db.commit()

        try:
            pages = parser.parse_file(doc.file_path, doc.file_type)
            if not pages:
                doc.status = "INDEXED"
                doc.rag_status = "READY"
                doc.total_chunks = 0
                db.commit()
                return doc

            # Gather explicit allowed roles and users
            perms = db.query(DocumentPermission).filter(DocumentPermission.document_id == doc.id).all()
            allowed_users = [str(p.user_id) for p in perms if p.user_id]
            allowed_roles = [str(p.role.code) for p in perms if p.role]

            doc_meta = {
                "document_id": str(doc.id),
                "title": doc.title,
                "file_name": doc.file_name,
                "department_id": doc.department_id if doc.department_id is not None else 0,
                "department_code": doc.department.code if doc.department else "GENERAL",
                "document_type": doc.document_type or "POLICY",
                "category": doc.category or "Chung",
                "security_level": doc.security_level or "DEPARTMENT",
                "visibility": 1 if doc.visibility else 0,
                "version": doc.version or "1.0",
                "status": doc.status,
                "owner_id": str(doc.owner_id) if doc.owner_id else "",
                "allowed_roles": ",".join(allowed_roles),
                "allowed_users": ",".join(allowed_users),
            }
            chunks_data = chunker.chunk_document(pages, doc_meta)

            # Generate Vector Embeddings & Chroma items
            texts = [c["content"] for c in chunks_data]
            embeddings = []
            chroma_items = []
            vec_error = None

            if texts:
                try:
                    from app.rag.embeddings import embeddings_client
                    embeddings = embeddings_client.embed_documents(texts)
                    for c in chunks_data:
                        chroma_items.append({
                            "chroma_id": f"doc_{doc.id}_chunk_{c['chunk_index']}",
                            "content": c["content"],
                            "metadata": c["metadata"]
                        })
                except Exception as vec_err:
                    vec_error = str(vec_err)

            # Fast atomic DB write
            db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).delete()

            chunk_records = []
            for c in chunks_data:
                chunk_rec = DocumentChunk(
                    document_id=doc.id,
                    chunk_index=c["chunk_index"],
                    content=c["content"],
                    metadata_json=c["metadata"],
                    chroma_id=f"doc_{doc.id}_chunk_{c['chunk_index']}",
                )
                chunk_records.append(chunk_rec)

            db.add_all(chunk_records)
            doc.total_chunks = len(chunk_records)

            if chroma_items and embeddings:
                try:
                    from app.rag.vectorstore import vector_store
                    vector_store.add_chunks(chroma_items, embeddings)
                    doc.status = "INDEXED"
                    doc.rag_status = "READY"
                except Exception as e:
                    doc.status = "PROCESSED"
                    doc.rag_status = "FAILED"
                    doc.error_message = f"ChromaDB index error: {str(e)}"
            elif vec_error:
                doc.status = "PROCESSED"
                doc.rag_status = "FAILED"
                doc.error_message = f"Vector indexing deferred: {vec_error}"
            else:
                doc.status = "INDEXED"
                doc.rag_status = "READY"

            db.commit()
            db.refresh(doc)
            return doc

        except Exception as e:
            doc.status = "FAILED"
            doc.rag_status = "FAILED"
            doc.error_message = f"Lỗi xử lý tài liệu: {str(e)}"
            db.commit()
            raise e

    @staticmethod
    def list_documents(
        db: Session,
        current_user: User,
        search: Optional[str] = None,
        department_id: Optional[int] = None,
        document_type: Optional[str] = None,
        category: Optional[str] = None,
        security_level: Optional[str] = None,
        rag_status: Optional[str] = None,
        status_filter: Optional[str] = None,
        owner_id: Optional[UUID] = None,
        ip_address: Optional[str] = None
    ) -> List[Document]:
        """Query document catalog strictly restricted by Enterprise Access Control."""
        query = db.query(Document)

        # 1. Enforce Backend Authorization Filter (never trust frontend)
        perm_filter = permission_service.get_document_query_filter(db, current_user)
        if perm_filter is not None:
            query = query.filter(perm_filter)

        # 2. Apply query filters
        if department_id is not None:
            query = query.filter(Document.department_id == department_id)
        if document_type:
            query = query.filter(Document.document_type == document_type)
        if category:
            query = query.filter(Document.category == category)
        if security_level:
            query = query.filter(Document.security_level == security_level)
        if rag_status:
            query = query.filter(Document.rag_status == rag_status)
        if status_filter:
            query = query.filter(Document.status == status_filter)
        if owner_id:
            query = query.filter(Document.owner_id == owner_id)

        # 3. Apply search query
        if search and search.strip():
            term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Document.title.ilike(term),
                    Document.file_name.ilike(term),
                    Document.category.ilike(term),
                    Document.document_type.ilike(term)
                )
            )
            audit_service.log_event(
                db=db,
                action="SEARCH",
                resource="DOCUMENTS",
                user_id=current_user.id,
                ip_address=ip_address,
                details={"search_query": search.strip()}
            )

        return query.order_by(Document.created_at.desc()).all()

    @staticmethod
    def get_document_by_id(
        db: Session,
        document_id: UUID,
        current_user: User,
        ip_address: Optional[str] = None
    ) -> Document:
        """Fetch document by ID with strict permission check."""
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy tài liệu.")

        if not permission_service.can_user_access_document(db, current_user, doc, action="VIEW"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền truy cập tài liệu này."
            )

        audit_service.log_event(
            db=db,
            action="VIEW",
            resource="DOCUMENTS",
            user_id=current_user.id,
            ip_address=ip_address,
            details={"document_id": str(doc.id), "title": doc.title}
        )
        return doc

    @staticmethod
    def update_document(
        db: Session,
        document_id: UUID,
        current_user: User,
        update_in: DocumentUpdate,
        ip_address: Optional[str] = None
    ) -> Document:
        """Update document metadata with authorization check."""
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu.")

        if not permission_service.can_user_access_document(db, current_user, doc, action="EDIT"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền chỉnh sửa tài liệu này."
            )

        version_changed = False
        if update_in.title is not None:
            doc.title = update_in.title.strip()
        if update_in.department_id is not None:
            doc.department_id = update_in.department_id
        if update_in.document_type is not None:
            doc.document_type = update_in.document_type.strip()
        if update_in.category is not None:
            doc.category = update_in.category.strip()
        if update_in.security_level is not None:
            doc.security_level = update_in.security_level.upper()
        if update_in.visibility is not None:
            doc.visibility = update_in.visibility
        if update_in.owner_id is not None:
            doc.owner_id = update_in.owner_id
        if update_in.version is not None and update_in.version.strip() != doc.version:
            doc.version = update_in.version.strip()
            version_changed = True

        doc.updated_at = datetime.now(timezone.utc)

        if version_changed:
            new_ver = DocumentVersion(
                document_id=doc.id,
                version_number=doc.version,
                file_name=doc.file_name,
                stored_file_name=doc.stored_file_name,
                file_size=doc.file_size,
                change_notes=f"Cập nhật phiên bản {doc.version}",
                created_by=current_user.id
            )
            db.add(new_ver)

        db.commit()
        db.refresh(doc)

        audit_service.log_event(
            db=db,
            action="EDIT",
            resource="DOCUMENTS",
            user_id=current_user.id,
            ip_address=ip_address,
            details={"document_id": str(doc.id), "title": doc.title}
        )
        return doc

    @staticmethod
    def delete_document(
        db: Session,
        document_id: UUID,
        current_user: User,
        ip_address: Optional[str] = None
    ) -> None:
        """Delete document file from disk, vector store, and database."""
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu.")

        if not permission_service.can_user_access_document(db, current_user, doc, action="DELETE"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền xóa tài liệu này."
            )

        title = doc.title

        # Remove file from disk
        if doc.file_path and os.path.exists(doc.file_path):
            try:
                os.remove(doc.file_path)
            except OSError:
                pass

        # Remove vector chunks from ChromaDB
        try:
            from app.rag.vectorstore import vector_store
            vector_store.delete_document(str(document_id))
        except Exception:
            pass

        db.delete(doc)
        db.commit()

        audit_service.log_event(
            db=db,
            action="DELETE",
            resource="DOCUMENTS",
            user_id=current_user.id,
            ip_address=ip_address,
            details={"document_id": str(document_id), "title": title}
        )

    @staticmethod
    def get_document_chunks(
        db: Session,
        document_id: UUID,
        current_user: User
    ) -> List[DocumentChunk]:
        """Fetch chunks belonging to a document after permission check."""
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu.")

        if not permission_service.can_user_access_document(db, current_user, doc, action="VIEW"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền xem nội dung tài liệu này."
            )

        return db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).order_by(DocumentChunk.chunk_index.asc()).all()

    @staticmethod
    def get_document_permissions(
        db: Session,
        document_id: UUID,
        current_user: User
    ) -> List[DocumentPermission]:
        """Retrieve explicit permissions granted for document."""
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu.")

        if not permission_service.can_user_access_document(db, current_user, doc, action="VIEW"):
            raise HTTPException(status_code=403, detail="Bạn không có quyền xem phân quyền của tài liệu.")

        return db.query(DocumentPermission).filter(
            DocumentPermission.document_id == document_id
        ).order_by(DocumentPermission.created_at.desc()).all()

    @staticmethod
    def add_document_permission(
        db: Session,
        document_id: UUID,
        current_user: User,
        perm_in: DocumentPermissionCreate,
        ip_address: Optional[str] = None
    ) -> DocumentPermission:
        """Add granular permission override for user or role."""
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu.")

        if not permission_service.can_user_access_document(db, current_user, doc, action="MANAGE"):
            raise HTTPException(status_code=403, detail="Bạn không có quyền quản lý phân quyền cho tài liệu này.")

        perm = DocumentPermission(
            document_id=doc.id,
            user_id=perm_in.user_id,
            role_id=perm_in.role_id,
            permission_type=perm_in.permission_type.upper(),
            created_by=current_user.id
        )
        db.add(perm)
        db.commit()
        db.refresh(perm)

        audit_service.log_event(
            db=db,
            action="PERMISSION_CHANGE",
            resource="DOCUMENTS",
            user_id=current_user.id,
            ip_address=ip_address,
            details={
                "document_id": str(doc.id),
                "user_id": str(perm_in.user_id) if perm_in.user_id else None,
                "role_id": perm_in.role_id,
                "permission_type": perm_in.permission_type
            }
        )
        return perm

    @staticmethod
    def delete_document_permission(
        db: Session,
        document_id: UUID,
        permission_id: UUID,
        current_user: User,
        ip_address: Optional[str] = None
    ) -> None:
        """Revoke a granular permission from document."""
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu.")

        if not permission_service.can_user_access_document(db, current_user, doc, action="MANAGE"):
            raise HTTPException(status_code=403, detail="Bạn không có quyền quản lý phân quyền cho tài liệu này.")

        perm = db.query(DocumentPermission).filter(
            DocumentPermission.id == permission_id,
            DocumentPermission.document_id == document_id
        ).first()
        if not perm:
            raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi phân quyền.")

        db.delete(perm)
        db.commit()

        audit_service.log_event(
            db=db,
            action="PERMISSION_CHANGE",
            resource="DOCUMENTS",
            user_id=current_user.id,
            ip_address=ip_address,
            details={"document_id": str(doc.id), "revoked_permission_id": str(permission_id)}
        )

    @staticmethod
    def get_document_versions(
        db: Session,
        document_id: UUID,
        current_user: User
    ) -> List[DocumentVersion]:
        """Fetch version history for document."""
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu.")

        if not permission_service.can_user_access_document(db, current_user, doc, action="VIEW"):
            raise HTTPException(status_code=403, detail="Bạn không có quyền xem tài liệu này.")

        return db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id
        ).order_by(DocumentVersion.created_at.desc()).all()


document_service = DocumentService()
