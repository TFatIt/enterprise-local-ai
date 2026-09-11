"""API endpoints for Auto-Import Document Watcher management."""

import os
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_active_user, require_role
from app.core.config import settings
from app.models.user import User
from app.models.document import Document

router = APIRouter()

WATCH_DIR = Path(settings.AUTO_IMPORT_DIRECTORY)
MANIFEST_FILE = WATCH_DIR / ".imported_manifest.json"


def _load_manifest() -> dict:
    """Load the imported files manifest."""
    if MANIFEST_FILE.exists():
        try:
            with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"imported_files": {}}
    return {"imported_files": {}}


@router.get(
    "/status",
    summary="Trạng thái hệ thống Auto-Import",
    description="Kiểm tra trạng thái thư mục giám sát, số file đã nạp, và thông tin manifest.",
)
def get_auto_import_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN", "ADMIN", "IT_ADMIN"])),
):
    """Get auto-import system status."""
    manifest = _load_manifest()
    imported = manifest.get("imported_files", {})
    last_scan = manifest.get("last_scan", None)

    # Count files in watch directory
    pending_files = 0
    total_files = 0
    if WATCH_DIR.exists():
        for root, dirs, files in os.walk(str(WATCH_DIR)):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for fname in files:
                if fname.startswith(".") or fname == "README.txt":
                    continue
                total_files += 1
                fpath = Path(root) / fname
                try:
                    rel_key = str(fpath.relative_to(WATCH_DIR))
                except ValueError:
                    continue
                if rel_key not in imported:
                    pending_files += 1

    # Count documents in DB from auto-import
    auto_imported_docs = (
        db.query(Document)
        .filter(Document.document_type == "KNOWLEDGE_BASE")
        .count()
    )

    # Check vision model
    vision_available = False
    try:
        from app.services.multimodal_service import multimodal_service
        vision_available = multimodal_service.check_vision_model()
    except Exception:
        pass

    return {
        "success": True,
        "watch_directory": str(WATCH_DIR),
        "watch_directory_exists": WATCH_DIR.exists(),
        "total_files_in_folder": total_files,
        "pending_import": pending_files,
        "already_imported": len(imported),
        "auto_imported_documents_in_db": auto_imported_docs,
        "last_scan": last_scan,
        "vision_model_available": vision_available,
        "supported_formats": {
            "documents": [".pdf", ".docx", ".txt", ".md", ".xlsx", ".csv", ".json", ".yaml", ".bat", ".ps1", ".sh", ".sql", ".log", ".ini"],
            "images": [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tiff"],
            "videos": [".mp4", ".mkv", ".avi", ".mov", ".webm"],
        },
    }


@router.post(
    "/scan",
    summary="Quét và nạp tài liệu mới",
    description="Quét thư mục auto_import_documents và nạp tất cả tài liệu mới/thay đổi vào Knowledge Base.",
)
def trigger_scan(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN", "ADMIN", "IT_ADMIN"])),
):
    """Manually trigger a scan of the auto-import directory."""
    if not WATCH_DIR.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thư mục giám sát không tồn tại: {WATCH_DIR}",
        )

    # Import the watcher module functions
    try:
        sys.path.insert(0, str(Path(settings.AUTO_IMPORT_DIRECTORY).parent / "scripts"))
        # We need to do the import inline to use the project's own watcher logic
        from scripts_import_helper import scan_and_import_api
        results = scan_and_import_api(db, current_user)
    except ImportError:
        # Fallback: run inline scan
        results = _inline_scan(db, current_user)

    return {
        "success": True,
        "message": "Quét hoàn tất.",
        "results": results,
    }


def _inline_scan(db: Session, current_user: User) -> dict:
    """Inline scan implementation for the API endpoint."""
    import hashlib
    import shutil
    import uuid
    from datetime import datetime, timezone

    from app.models.document import Document
    from app.models.document_chunk import DocumentChunk
    from app.models.document_version import DocumentVersion
    from app.rag.parser import parser
    from app.rag.chunker import chunker

    SKIP_NAMES = {"README.txt", ".imported_manifest.json", ".gitkeep", "desktop.ini", "thumbs.db"}

    # Extension map
    from app.services.document_service import DocumentService
    ext_map = DocumentService.ALLOWED_EXTENSIONS

    manifest = _load_manifest()
    imported = manifest.get("imported_files", {})
    results = {"new": 0, "updated": 0, "skipped": 0, "deleted": 0, "failed": 0, "details": []}

    from app.rag.vectorstore import vector_store

    # -----------------------------------------------------------------------
    # Step 1: Two-Way Synchronization - Detect and Purge Deleted Files
    # -----------------------------------------------------------------------
    # Check all manifest entries
    deleted_manifest_keys = []
    for rel_key in list(imported.keys()):
        fpath = WATCH_DIR / rel_key
        if not fpath.exists():
            deleted_manifest_keys.append(rel_key)

    # Check all KNOWLEDGE_BASE documents in database
    kb_docs = db.query(Document).filter(Document.document_type == "KNOWLEDGE_BASE").all()
    for doc in kb_docs:
        # Check if file exists anywhere in WATCH_DIR
        file_still_exists = False
        for root, dirs, files in os.walk(str(WATCH_DIR)):
            if doc.file_name in files:
                file_still_exists = True
                break
        if not file_still_exists:
            # Document was deleted from watch folder -> purge from ChromaDB and DB
            try:
                vector_store.delete_document(str(doc.id))
            except Exception:
                pass
            db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).delete()
            db.query(DocumentVersion).filter(DocumentVersion.document_id == doc.id).delete()
            if doc.file_path and os.path.exists(doc.file_path):
                try:
                    os.remove(doc.file_path)
                except OSError:
                    pass
            db.delete(doc)
            results["deleted"] += 1
            results["details"].append(f"🗑️ Đã xóa sạch CSDL & ChromaDB: {doc.file_name}")

    # Remove stale manifest keys
    for rel_key in deleted_manifest_keys:
        if rel_key in imported:
            del imported[rel_key]

    db.commit()

    # -----------------------------------------------------------------------
    # Step 2: Scan and Import New / Modified Files
    # -----------------------------------------------------------------------
    for root, dirs, files in os.walk(str(WATCH_DIR)):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fname in files:
            fpath = Path(root) / fname
            name_lower = fname.lower()

            if name_lower in {n.lower() for n in SKIP_NAMES}:
                continue
            if name_lower.startswith(("~$", ".", "__")) or name_lower.endswith((".tmp", ".crdownload", ".part")):
                continue

            ext = fpath.suffix.lower()
            if ext not in ext_map:
                results["skipped"] += 1
                continue

            try:
                rel_key = str(fpath.relative_to(WATCH_DIR))
            except ValueError:
                continue

            # Compute hash
            sha256 = hashlib.sha256()
            with open(str(fpath), "rb") as hf:
                for block in iter(lambda: hf.read(65536), b""):
                    sha256.update(block)
            current_hash = sha256.hexdigest()

            if rel_key in imported and imported[rel_key].get("hash") == current_hash:
                results["skipped"] += 1
                continue

            is_update = rel_key in imported
            file_type = ext_map[ext]

            try:
                unique_id = uuid.uuid4()
                upload_dir = os.path.abspath(settings.UPLOAD_DIRECTORY)
                os.makedirs(upload_dir, exist_ok=True)
                stored_name = f"{unique_id}{ext}"
                target_path = os.path.join(upload_dir, stored_name)
                shutil.copy2(str(fpath), target_path)

                title = fpath.stem.replace("_", " ").replace("-", " ").strip() or fname
                file_size = os.path.getsize(str(fpath))

                # Determine category
                relative = fpath.relative_to(WATCH_DIR)
                parts = relative.parts
                from app.services.multimodal_service import IMAGE_EXTENSIONS, VIDEO_EXTENSIONS
                if len(parts) > 1:
                    category = parts[0].capitalize()
                elif ext in IMAGE_EXTENSIONS:
                    category = "Hình ảnh"
                elif ext in VIDEO_EXTENSIONS:
                    category = "Video"
                else:
                    category = "Chung"

                doc = Document(
                    id=unique_id,
                    title=title,
                    file_name=fname,
                    stored_file_name=stored_name,
                    file_path=target_path,
                    file_type=file_type,
                    file_size=file_size,
                    department_id=None,
                    document_type="KNOWLEDGE_BASE",
                    category=category,
                    owner_id=current_user.id,
                    uploaded_by=current_user.id,
                    security_level="PUBLIC",
                    visibility=True,
                    version="1.0",
                    status="PROCESSING",
                    rag_status="PROCESSING",
                    total_chunks=0,
                )
                db.add(doc)

                ver = DocumentVersion(
                    document_id=doc.id,
                    version_number="1.0",
                    file_name=fname,
                    stored_file_name=stored_name,
                    file_size=file_size,
                    change_notes="Tự động nạp từ thư mục auto_import_documents.",
                    created_by=current_user.id,
                )
                db.add(ver)
                db.commit()
                db.refresh(doc)

                # Parse
                pages = parser.parse_file(target_path, file_type)
                if pages:
                    doc_meta = {
                        "document_id": str(doc.id),
                        "title": doc.title,
                        "file_name": doc.file_name,
                        "department_id": 0,
                        "department_code": "GENERAL",
                        "document_type": "KNOWLEDGE_BASE",
                        "category": category,
                        "security_level": "PUBLIC",
                        "visibility": 1,
                        "version": "1.0",
                        "status": "PROCESSING",
                        "owner_id": str(current_user.id),
                        "allowed_roles": "",
                        "allowed_users": "",
                    }
                    chunks_data = chunker.chunk_document(pages, doc_meta)
                    texts = [c["content"] for c in chunks_data]

                    if texts:
                        from app.rag.embeddings import embeddings_client
                        embeddings = embeddings_client.embed_documents(texts)
                        chroma_items = []
                        for c in chunks_data:
                            chroma_items.append({
                                "chroma_id": f"doc_{doc.id}_chunk_{c['chunk_index']}",
                                "content": c["content"],
                                "metadata": c["metadata"],
                            })

                        chunk_records = []
                        for c in chunks_data:
                            chunk_records.append(DocumentChunk(
                                document_id=doc.id,
                                chunk_index=c["chunk_index"],
                                content=c["content"],
                                metadata_json=c["metadata"],
                                chroma_id=f"doc_{doc.id}_chunk_{c['chunk_index']}",
                            ))
                        db.add_all(chunk_records)
                        doc.total_chunks = len(chunk_records)

                        if chroma_items and embeddings:
                            from app.rag.vectorstore import vector_store
                            vector_store.add_chunks(chroma_items, embeddings)

                doc.status = "INDEXED"
                doc.rag_status = "READY"
                doc.error_message = None
                db.commit()

                imported[rel_key] = {
                    "hash": current_hash,
                    "imported_at": datetime.now(timezone.utc).isoformat(),
                    "file_size": file_size,
                    "file_type": ext,
                }

                if is_update:
                    results["updated"] += 1
                else:
                    results["new"] += 1
                results["details"].append(f"✓ {rel_key}")

            except Exception as e:
                results["failed"] += 1
                results["details"].append(f"✗ {rel_key}: {str(e)[:200]}")
                try:
                    doc.status = "FAILED"
                    doc.rag_status = "FAILED"
                    doc.error_message = str(e)[:500]
                    db.commit()
                except Exception:
                    db.rollback()

    manifest["imported_files"] = imported
    manifest["last_scan"] = datetime.now(timezone.utc).isoformat()
    _save_manifest(manifest)

    return results


def _save_manifest(manifest: dict):
    """Save manifest file."""
    MANIFEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


@router.get(
    "/manifest",
    summary="Xem danh sách file đã nạp",
    description="Lấy danh sách tất cả file đã được nạp tự động kèm hash và thời gian.",
)
def get_manifest(
    current_user: User = Depends(require_role(["SUPER_ADMIN", "ADMIN", "IT_ADMIN"])),
):
    """Get the import manifest."""
    manifest = _load_manifest()
    imported = manifest.get("imported_files", {})
    return {
        "success": True,
        "total_imported": len(imported),
        "last_scan": manifest.get("last_scan"),
        "files": imported,
    }


@router.delete(
    "/manifest",
    summary="Xóa manifest để nạp lại từ đầu",
    description="Xóa file manifest để hệ thống coi tất cả file như mới và nạp lại toàn bộ.",
)
def reset_manifest(
    current_user: User = Depends(require_role(["SUPER_ADMIN", "ADMIN"])),
):
    """Reset the import manifest so all files will be re-imported on next scan."""
    if MANIFEST_FILE.exists():
        os.remove(str(MANIFEST_FILE))
    return {
        "success": True,
        "message": "Đã xóa manifest. Lần quét tiếp theo sẽ nạp lại toàn bộ tài liệu.",
    }


@router.get(
    "/vision-check",
    summary="Kiểm tra khả năng đọc hình ảnh",
    description="Kiểm tra model Vision AI (minicpm-v) đã sẵn sàng để đọc và phân tích hình ảnh chưa.",
)
def check_vision_capability(
    current_user: User = Depends(require_role(["SUPER_ADMIN", "ADMIN", "IT_ADMIN"])),
):
    """Check if Vision AI model is available for image analysis."""
    try:
        from app.services.multimodal_service import multimodal_service, VISION_MODEL
        available = multimodal_service.check_vision_model()
        return {
            "success": True,
            "vision_model": VISION_MODEL,
            "available": available,
            "instruction": (
                f"Chạy lệnh: ollama pull {VISION_MODEL}"
                if not available
                else "Model Vision AI đã sẵn sàng để phân tích hình ảnh."
            ),
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def _format_size(size_bytes: int) -> str:
    """Format bytes into human readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


@router.get(
    "/files",
    summary="Danh sách tệp trong thư mục auto_import_documents",
    description="Xem danh sách chi tiết các file trong thư mục giám sát kèm trạng thái đã nạp hay chưa.",
)
def list_auto_import_files(
    subfolder: Optional[str] = Query(None, description="Lọc theo thư mục con (docs, images, videos)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN", "ADMIN", "IT_ADMIN"])),
):
    """List all files in the auto_import_documents directory with metadata."""
    if not WATCH_DIR.exists():
        return {"success": True, "files": [], "total": 0}

    manifest = _load_manifest()
    imported = manifest.get("imported_files", {})

    from app.models.document_chunk import DocumentChunk
    from app.services.document_service import DocumentService
    ext_map = DocumentService.ALLOWED_EXTENSIONS

    files_list = []
    target_dir = WATCH_DIR / subfolder if subfolder else WATCH_DIR

    if not target_dir.exists():
        return {"success": True, "files": [], "total": 0}

    for root, dirs, files in os.walk(str(target_dir)):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fname in sorted(files):
            if fname.startswith((".", "~$", "__")) or fname in {"README.txt", ".imported_manifest.json", ".gitkeep", "desktop.ini"}:
                continue

            fpath = Path(root) / fname
            try:
                rel_path = str(fpath.relative_to(WATCH_DIR))
            except ValueError:
                continue

            ext = fpath.suffix.lower()
            file_size = fpath.stat().st_size
            mtime = datetime.fromtimestamp(fpath.stat().st_mtime, tz=timezone.utc).isoformat()

            is_imported = rel_path in imported
            import_info = imported.get(rel_path, {})
            imported_at = import_info.get("imported_at")

            # Determine category / subfolder
            parts = Path(rel_path).parts
            category = parts[0] if len(parts) > 1 else "Root"

            # Check DB Document & chunk count
            doc = db.query(Document).filter(Document.file_name == fname).first()
            chunks_count = 0
            doc_id = None
            doc_status = "PENDING"
            if doc:
                doc_id = str(doc.id)
                chunks_count = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).count()
                doc_status = doc.status or "INDEXED"

            files_list.append({
                "file_name": fname,
                "relative_path": rel_path,
                "category": category,
                "extension": ext,
                "is_supported": ext in ext_map,
                "size_bytes": file_size,
                "size_human": _format_size(file_size),
                "modified_at": mtime,
                "is_imported": is_imported,
                "imported_at": imported_at,
                "document_id": doc_id,
                "chunks_count": chunks_count,
                "status": doc_status if is_imported else "PENDING",
            })

    return {
        "success": True,
        "total": len(files_list),
        "files": files_list,
    }


@router.post(
    "/upload",
    summary="Tải tài liệu trực tiếp vào thư mục auto_import_documents",
    description="Tải tệp lên thư mục giám sát và tùy chọn nạp ngay lập tức vào Knowledge Base.",
)
async def upload_to_auto_import(
    file: UploadFile = File(...),
    subfolder: str = Form("docs", description="Thư mục đích: docs, images, videos"),
    auto_index: bool = Form(True, description="Tự động phân tích và nạp vào RAG ngay lập tức"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN", "ADMIN", "IT_ADMIN"])),
):
    """Upload a file directly to auto_import_documents."""
    # Sanitize subfolder
    subfolder_clean = "".join(c for c in subfolder if c.isalnum() or c in ("-", "_")).strip() or "docs"
    target_subfolder = WATCH_DIR / subfolder_clean
    target_subfolder.mkdir(parents=True, exist_ok=True)

    # Sanitize filename
    safe_name = os.path.basename(file.filename or "upload.bin")
    safe_name = "".join(c for c in safe_name if c.isalnum() or c in (".", "-", "_", " ", "(", ")")).strip()
    if not safe_name:
        raise HTTPException(status_code=400, detail="Tên tệp không hợp lệ.")

    target_path = target_subfolder / safe_name

    # Save to disk
    contents = await file.read()
    with open(target_path, "wb") as f:
        f.write(contents)

    rel_key = str(target_path.relative_to(WATCH_DIR))
    res_msg = f"Đã lưu tệp vào {rel_key}"
    index_result = None

    if auto_index:
        # Trigger inline indexing for this specific file
        from app.services.document_service import DocumentService
        ext_map = DocumentService.ALLOWED_EXTENSIONS
        manifest = _load_manifest()
        index_result = _index_single_file(target_path, db, current_user, manifest, ext_map)
        res_msg = f"Đã lưu và nạp thành công tệp {safe_name} vào Knowledge Base."

    return {
        "success": True,
        "message": res_msg,
        "file_name": safe_name,
        "relative_path": rel_key,
        "size_bytes": len(contents),
        "size_human": _format_size(len(contents)),
        "indexed": auto_index,
        "index_result": index_result,
    }


@router.post(
    "/reindex-file",
    summary="Lập chỉ mục lại một tệp cụ thể",
    description="Buộc hệ thống đọc lại và cập nhật vector embeddings cho một tài liệu cụ thể.",
)
def reindex_specific_file(
    relative_path: str = Query(..., description="Đường dẫn tương đối của tệp (vd: docs/file.pdf)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN", "ADMIN", "IT_ADMIN"])),
):
    """Force re-indexing of a single file in the auto-import directory."""
    fpath = WATCH_DIR / relative_path
    if not fpath.exists() or not fpath.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy tệp: {relative_path}",
        )

    from app.services.document_service import DocumentService
    ext_map = DocumentService.ALLOWED_EXTENSIONS
    manifest = _load_manifest()

    result = _index_single_file(fpath, db, current_user, manifest, ext_map, force=True)
    return {
        "success": True,
        "message": f"Đã lập chỉ mục lại tệp {relative_path}",
        "result": result,
    }


@router.delete(
    "/files",
    summary="Xóa tệp khỏi auto_import_documents và Knowledge Base",
    description="Xóa tệp trên đĩa đồng thời xóa sạch dữ liệu chunks và embeddings liên quan trong ChromaDB.",
)
def delete_auto_import_file(
    relative_path: str = Query(..., description="Đường dẫn tương đối của tệp cần xóa"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN", "ADMIN"])),
):
    """Delete a file from auto_import_documents and cascade cleanup from ChromaDB and DB."""
    # Prevent directory traversal
    try:
        fpath = (WATCH_DIR / relative_path).resolve()
        if not str(fpath).startswith(str(WATCH_DIR.resolve())):
            raise HTTPException(status_code=400, detail="Đường dẫn không hợp lệ.")
    except Exception:
        raise HTTPException(status_code=400, detail="Đường dẫn không hợp lệ.")

    fname = fpath.name
    deleted_from_disk = False

    if fpath.exists() and fpath.is_file():
        os.remove(str(fpath))
        deleted_from_disk = True

    # Cleanup DB records and ChromaDB
    from app.models.document_chunk import DocumentChunk
    from app.models.document_version import DocumentVersion
    from app.rag.vectorstore import vector_store

    docs = db.query(Document).filter(Document.file_name == fname).all()
    deleted_chunks = 0
    for doc in docs:
        try:
            vector_store.delete_document(str(doc.id))
        except Exception:
            pass
        chunks_count = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).delete()
        deleted_chunks += chunks_count
        db.query(DocumentVersion).filter(DocumentVersion.document_id == doc.id).delete()
        db.delete(doc)

    db.commit()

    # Update manifest
    manifest = _load_manifest()
    rel_key = str(relative_path).replace("/", "\\")
    rel_key_alt = str(relative_path).replace("\\", "/")
    imported = manifest.get("imported_files", {})
    if rel_key in imported:
        del imported[rel_key]
    elif rel_key_alt in imported:
        del imported[rel_key_alt]
    manifest["imported_files"] = imported
    _save_manifest(manifest)

    return {
        "success": True,
        "message": f"Đã xóa tệp {fname} và toàn bộ {deleted_chunks} vector chunks liên quan.",
        "deleted_from_disk": deleted_from_disk,
        "deleted_chunks": deleted_chunks,
        "deleted_documents": len(docs),
    }


def _index_single_file(
    fpath: Path,
    db: Session,
    current_user: User,
    manifest: dict,
    ext_map: dict,
    force: bool = False,
) -> dict:
    """Index or re-index a single file from auto_import_documents."""
    import hashlib
    import shutil
    import uuid

    from app.models.document import Document
    from app.models.document_chunk import DocumentChunk
    from app.models.document_version import DocumentVersion
    from app.rag.parser import parser
    from app.rag.chunker import chunker
    from app.rag.embeddings import embeddings_client
    from app.rag.vectorstore import vector_store

    fname = fpath.name
    ext = fpath.suffix.lower()
    if ext not in ext_map:
        return {"status": "SKIPPED", "reason": f"Unsupported extension {ext}"}

    rel_key = str(fpath.relative_to(WATCH_DIR))

    # Compute hash
    sha256 = hashlib.sha256()
    with open(str(fpath), "rb") as hf:
        for block in iter(lambda: hf.read(65536), b""):
            sha256.update(block)
    current_hash = sha256.hexdigest()

    file_size = os.path.getsize(str(fpath))
    file_type = ext_map[ext]

    # Check existing document in DB
    existing_doc = db.query(Document).filter(Document.file_name == fname).first()
    if existing_doc:
        doc = existing_doc
        # Clean old chunks
        vector_store.delete_document(str(doc.id))
        db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).delete()
        db.commit()
    else:
        unique_id = uuid.uuid4()
        upload_dir = os.path.abspath(settings.UPLOAD_DIRECTORY)
        os.makedirs(upload_dir, exist_ok=True)
        stored_name = f"{unique_id}{ext}"
        target_path = os.path.join(upload_dir, stored_name)
        shutil.copy2(str(fpath), target_path)

        # Determine category
        parts = fpath.relative_to(WATCH_DIR).parts
        category = parts[0].capitalize() if len(parts) > 1 else "Chung"
        title = fpath.stem.replace("_", " ").replace("-", " ").strip() or fname

        doc = Document(
            id=unique_id,
            title=title,
            file_name=fname,
            stored_file_name=stored_name,
            file_path=target_path,
            file_type=file_type,
            file_size=file_size,
            department_id=None,
            document_type="KNOWLEDGE_BASE",
            category=category,
            owner_id=current_user.id,
            uploaded_by=current_user.id,
            security_level="PUBLIC",
            visibility=True,
            version="1.0",
            status="PROCESSING",
            rag_status="PROCESSING",
            total_chunks=0,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

    # Parse and chunk
    pages = parser.parse_file(doc.file_path, file_type)
    chunks_created = 0
    if pages:
        doc_meta = {
            "document_id": str(doc.id),
            "title": doc.title,
            "file_name": doc.file_name,
            "department_id": 0,
            "department_code": "GENERAL",
            "document_type": "KNOWLEDGE_BASE",
            "category": doc.category or "Chung",
            "security_level": "PUBLIC",
            "visibility": 1,
            "version": "1.0",
            "status": "PROCESSING",
            "owner_id": str(current_user.id),
            "allowed_roles": "",
            "allowed_users": "",
        }
        chunks_data = chunker.chunk_document(pages, doc_meta)
        texts = [c["content"] for c in chunks_data]
        if texts:
            embeddings = embeddings_client.embed_documents(texts)
            chroma_items = []
            chunk_records = []
            for c in chunks_data:
                cid = f"doc_{doc.id}_chunk_{c['chunk_index']}"
                chroma_items.append({
                    "chroma_id": cid,
                    "content": c["content"],
                    "metadata": c["metadata"],
                })
                chunk_records.append(DocumentChunk(
                    document_id=doc.id,
                    chunk_index=c["chunk_index"],
                    content=c["content"],
                    metadata_json=c["metadata"],
                    chroma_id=cid,
                ))
            db.add_all(chunk_records)
            doc.total_chunks = len(chunk_records)
            chunks_created = len(chunk_records)

            if chroma_items and embeddings:
                vector_store.add_chunks(chroma_items, embeddings)

    doc.status = "INDEXED"
    doc.rag_status = "READY"
    doc.error_message = None
    db.commit()

    # Update manifest
    imported = manifest.get("imported_files", {})
    imported[rel_key] = {
        "hash": current_hash,
        "imported_at": datetime.now(timezone.utc).isoformat(),
        "file_size": file_size,
        "file_type": ext,
    }
    manifest["imported_files"] = imported
    _save_manifest(manifest)

    return {
        "status": "INDEXED",
        "document_id": str(doc.id),
        "chunks_count": chunks_created,
        "file_name": fname,
        "relative_path": rel_key,
    }

