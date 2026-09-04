"""Document storage, parsing orchestration, and chunk lifecycle service."""

import os
import uuid
import shutil
from typing import List, Optional
from uuid import UUID
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.user import User
from app.core.config import settings
from app.rag.parser import parser
from app.rag.chunker import chunker


class DocumentService:
    """Service handling document upload, storage, parsing, and chunk generation."""

    ALLOWED_EXTENSIONS = {".pdf": "PDF", ".docx": "DOCX", ".txt": "TXT"}

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
        current_user: User
    ) -> Document:
        """Validate, store on disk, and register new document in database."""
        # 1. Validate file extension
        _, ext = os.path.splitext(file.filename or "")
        ext_lower = ext.lower()
        if ext_lower not in cls.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Định dạng tệp '{ext}' không được hỗ trợ. Chỉ chấp nhận: .pdf, .docx, .txt"
            )

        file_type = cls.ALLOWED_EXTENSIONS[ext_lower]

        # 2. Prepare file destination
        upload_dir = cls._ensure_upload_dir()
        unique_file_id = uuid.uuid4()
        stored_file_name = f"{unique_file_id}{ext_lower}"
        target_path = os.path.join(upload_dir, stored_file_name)

        # 3. Stream content to disk and check file size
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        file_size = 0

        try:
            with open(target_path, "wb") as buffer:
                while chunk := file.file.read(1024 * 1024):  # 1MB chunks
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

        # 4. Insert Document record
        doc = Document(
            id=unique_file_id,
            title=title.strip() if title else file.filename,
            file_name=file.filename or "unknown",
            stored_file_name=stored_file_name,
            file_path=target_path,
            file_type=file_type,
            file_size=file_size,
            department_id=department_id,
            uploaded_by=current_user.id,
            status="UPLOADED",
            total_chunks=0,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # 5. Automatically trigger parsing and chunking
        try:
            cls.process_and_chunk_document(db, doc.id)
        except Exception as e:
            doc.status = "FAILED"
            doc.error_message = str(e)
            db.commit()

        return doc

    @classmethod
    def process_and_chunk_document(cls, db: Session, document_id: UUID) -> Document:
        """Extract text and generate chunks for a document."""
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu.")

        doc.status = "PROCESSING"
        db.commit()

        try:
            # Parse raw text
            pages = parser.parse_file(doc.file_path, doc.file_type)
            if not pages:
                doc.status = "INDEXED"
                doc.total_chunks = 0
                db.commit()
                return doc

            # Chunk document
            doc_meta = {
                "document_id": str(doc.id),
                "title": doc.title,
                "file_name": doc.file_name,
                "department_id": doc.department_id if doc.department_id is not None else 0,
            }
            chunks_data = chunker.chunk_document(pages, doc_meta)

            # Save chunks to DB
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

            # Generate Vector Embeddings & Index into ChromaDB (Phase 7)
            try:
                from app.rag.embeddings import embeddings_client
                from app.rag.vectorstore import vector_store

                texts = [c["content"] for c in chunks_data]
                if texts:
                    embeddings = embeddings_client.embed_documents(texts)
                    chroma_items = []
                    for c in chunks_data:
                        chroma_items.append({
                            "chroma_id": f"doc_{doc.id}_chunk_{c['chunk_index']}",
                            "content": c["content"],
                            "metadata": c["metadata"]
                        })
                    vector_store.add_chunks(chroma_items, embeddings)
                doc.status = "INDEXED"
            except Exception as vec_err:
                # If Ollama service is temporarily unreachable, document remains PROCESSED
                doc.status = "PROCESSED"
                doc.error_message = f"Vector indexing deferred: {str(vec_err)}"

            db.commit()
            db.refresh(doc)
            return doc

        except Exception as e:
            doc.status = "FAILED"
            doc.error_message = f"Lỗi xử lý tài liệu: {str(e)}"
            db.commit()
            raise e

    @staticmethod
    def list_documents(
        db: Session,
        department_id: Optional[int] = None,
        status_filter: Optional[str] = None
    ) -> List[Document]:
        """Query document catalog with optional department and status filters."""
        query = db.query(Document)
        if department_id:
            query = query.filter(Document.department_id == department_id)
        if status_filter:
            query = query.filter(Document.status == status_filter)
        return query.order_by(Document.created_at.desc()).all()

    @staticmethod
    def get_document_by_id(db: Session, document_id: UUID) -> Optional[Document]:
        """Fetch document by primary key."""
        return db.query(Document).filter(Document.id == document_id).first()

    @staticmethod
    def get_document_chunks(db: Session, document_id: UUID) -> List[DocumentChunk]:
        """Fetch all chunks belonging to a document."""
        return db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).order_by(DocumentChunk.chunk_index.asc()).all()

    @staticmethod
    def delete_document(db: Session, document_id: UUID) -> None:
        """Delete document file from disk and cascade delete from database."""
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu.")

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


document_service = DocumentService()
