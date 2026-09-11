"""
Auto Document Watcher - Tự động phát hiện và nạp tài liệu mới vào Knowledge Base.

Script này giám sát thư mục `auto_import_documents/` và tự động:
1. Phát hiện file mới hoặc file thay đổi nội dung
2. Phân loại loại file (văn bản / hình ảnh / video)
3. Trích xuất toàn bộ kiến thức (bao gồm OCR cho ảnh, keyframe cho video)
4. Vector hóa và nạp vào ChromaDB
5. Đăng ký vào cơ sở dữ liệu

Cách chạy:
    python scripts/auto_document_watcher.py
    hoặc:
    python scripts/auto_document_watcher.py --scan-once
"""

import os
import sys
import json
import time
import uuid
import hashlib
import logging
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Set

# Ensure project root is in path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("auto_watcher")


# --- Constants ---
WATCH_DIR = PROJECT_ROOT / "auto_import_documents"
MANIFEST_FILE = WATCH_DIR / ".imported_manifest.json"

# Files and patterns to always skip
SKIP_PATTERNS = {
    "README.txt", ".imported_manifest.json", ".gitkeep",
    "desktop.ini", "thumbs.db", ".ds_store",
}
SKIP_PREFIXES = ("~$", ".", "__")
SKIP_SUFFIXES = (".tmp", ".crdownload", ".part", ".downloading")

# All supported extensions (must match document_service.py ALLOWED_EXTENSIONS)
DOCUMENT_EXTENSIONS = {
    ".pdf", ".docx", ".txt", ".xlsx", ".csv", ".md",
    ".bat", ".ps1", ".sh", ".sql", ".json", ".log", ".ini", ".yaml", ".yml",
}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tiff", ".tif"}
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".webm"}
ALL_EXTENSIONS = DOCUMENT_EXTENSIONS | IMAGE_EXTENSIONS | VIDEO_EXTENSIONS

# Extension to file_type mapping (must match document_service.py)
EXT_TO_TYPE = {
    ".pdf": "PDF", ".docx": "DOCX", ".txt": "TXT", ".xlsx": "XLSX", ".csv": "CSV",
    ".md": "TXT", ".bat": "TXT", ".ps1": "TXT", ".sh": "TXT", ".sql": "TXT",
    ".json": "TXT", ".log": "TXT", ".ini": "TXT", ".yaml": "TXT", ".yml": "TXT",
}
for ext in IMAGE_EXTENSIONS:
    EXT_TO_TYPE[ext] = "IMAGE"
for ext in VIDEO_EXTENSIONS:
    EXT_TO_TYPE[ext] = "VIDEO"


def compute_file_hash(file_path: str) -> str:
    """Compute SHA-256 hash of a file for change detection."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            sha256.update(block)
    return sha256.hexdigest()


def load_manifest() -> Dict:
    """Load the imported files manifest from disk."""
    if MANIFEST_FILE.exists():
        try:
            with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"imported_files": {}}
    return {"imported_files": {}}


def save_manifest(manifest: Dict):
    """Save the imported files manifest to disk."""
    MANIFEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


def should_skip_file(file_path: Path) -> bool:
    """Check if file should be skipped based on naming patterns."""
    name = file_path.name.lower()
    if name in SKIP_PATTERNS:
        return True
    if any(name.startswith(p) for p in SKIP_PREFIXES):
        return True
    if any(name.endswith(s) for s in SKIP_SUFFIXES):
        return True
    return False


def is_file_ready(file_path: str, wait_secs: int = 3) -> bool:
    """Check if file has finished writing by comparing size after a delay."""
    try:
        size1 = os.path.getsize(file_path)
        time.sleep(wait_secs)
        size2 = os.path.getsize(file_path)
        return size1 == size2 and size2 > 0
    except OSError:
        return False


def get_auto_import_user_id(db) -> Optional[str]:
    """Get the system admin user ID for auto-import attribution."""
    from app.models.user import User
    admin = db.query(User).filter(User.username == "admin").first()
    if admin:
        return admin.id
    # Fallback: get any SUPER_ADMIN
    from app.models.permission import Role
    admin_role = db.query(Role).filter(Role.code == "SUPER_ADMIN").first()
    if admin_role:
        any_admin = db.query(User).filter(User.role_id == admin_role.id, User.is_active == True).first()
        if any_admin:
            return any_admin.id
    return None


def import_single_file(file_path: Path, db, admin_user) -> bool:
    """Import a single file into the RAG knowledge base.

    Returns True on success, False on failure.
    """
    from app.models.document import Document
    from app.models.document_chunk import DocumentChunk
    from app.models.document_version import DocumentVersion
    from app.rag.parser import parser
    from app.rag.chunker import chunker

    ext = file_path.suffix.lower()
    file_type = EXT_TO_TYPE.get(ext, "TXT")
    file_name = file_path.name
    file_size = os.path.getsize(str(file_path))
    abs_path = str(file_path.resolve())

    # Generate title from filename
    title = file_path.stem.replace("_", " ").replace("-", " ").strip()
    if not title:
        title = file_name

    unique_id = uuid.uuid4()

    # Copy file to uploads directory
    from app.core.config import settings
    upload_dir = os.path.abspath(settings.UPLOAD_DIRECTORY)
    os.makedirs(upload_dir, exist_ok=True)
    stored_name = f"{unique_id}{ext}"
    target_path = os.path.join(upload_dir, stored_name)

    import shutil
    shutil.copy2(abs_path, target_path)

    # Determine category based on subdirectory
    relative = file_path.relative_to(WATCH_DIR)
    parts = relative.parts
    if len(parts) > 1:
        subfolder = parts[0].lower()
        if subfolder == "images":
            category = "Hình ảnh"
        elif subfolder == "videos":
            category = "Video"
        elif subfolder == "docs":
            category = "Tài liệu"
        else:
            category = subfolder.capitalize()
    else:
        if ext in IMAGE_EXTENSIONS:
            category = "Hình ảnh"
        elif ext in VIDEO_EXTENSIONS:
            category = "Video"
        else:
            category = "Chung"

    # Create Document record
    doc = Document(
        id=unique_id,
        title=title,
        file_name=file_name,
        stored_file_name=stored_name,
        file_path=target_path,
        file_type=file_type,
        file_size=file_size,
        department_id=None,  # Auto-import goes to general
        document_type="KNOWLEDGE_BASE",
        category=category,
        owner_id=admin_user.id,
        uploaded_by=admin_user.id,
        security_level="PUBLIC",
        visibility=True,
        version="1.0",
        status="UPLOADED",
        rag_status="READY",
        total_chunks=0,
    )
    db.add(doc)

    # Version record
    ver = DocumentVersion(
        document_id=doc.id,
        version_number="1.0",
        file_name=file_name,
        stored_file_name=stored_name,
        file_size=file_size,
        change_notes="Tự động nạp từ thư mục auto_import_documents.",
        created_by=admin_user.id,
    )
    db.add(ver)
    db.commit()
    db.refresh(doc)

    # Parse and chunk
    doc.status = "PROCESSING"
    doc.rag_status = "PROCESSING"
    db.commit()

    try:
        pages = parser.parse_file(target_path, file_type)
        if not pages:
            doc.status = "INDEXED"
            doc.rag_status = "READY"
            doc.total_chunks = 0
            db.commit()
            return True

        doc_meta = {
            "document_id": str(doc.id),
            "title": doc.title,
            "file_name": doc.file_name,
            "department_id": 0,
            "department_code": "GENERAL",
            "document_type": doc.document_type,
            "category": doc.category,
            "security_level": "PUBLIC",
            "visibility": 1,
            "version": "1.0",
            "status": "PROCESSING",
            "owner_id": str(admin_user.id),
            "allowed_roles": "",
            "allowed_users": "",
        }

        chunks_data = chunker.chunk_document(pages, doc_meta)

        # Embed
        texts = [c["content"] for c in chunks_data]
        embeddings = []
        chroma_items = []

        if texts:
            from app.rag.embeddings import embeddings_client
            embeddings = embeddings_client.embed_documents(texts)
            for c in chunks_data:
                chroma_items.append({
                    "chroma_id": f"doc_{doc.id}_chunk_{c['chunk_index']}",
                    "content": c["content"],
                    "metadata": c["metadata"],
                })

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

        # Insert into ChromaDB
        if chroma_items and embeddings:
            from app.rag.vectorstore import vector_store
            vector_store.add_chunks(chroma_items, embeddings)
            doc.status = "INDEXED"
            doc.rag_status = "READY"
        else:
            doc.status = "INDEXED"
            doc.rag_status = "READY"

        doc.error_message = None
        db.commit()
        return True

    except Exception as e:
        doc.status = "FAILED"
        doc.rag_status = "FAILED"
        doc.error_message = str(e)[:500]
        db.commit()
        logger.error(f"  ✗ Processing failed: {e}")
        return False


def scan_and_import(db, admin_user) -> Dict:
    """Scan the auto_import directory and import new/changed files."""
    manifest = load_manifest()
    imported = manifest.get("imported_files", {})

    results = {"new": 0, "updated": 0, "skipped": 0, "failed": 0, "details": []}

    # Walk all files in WATCH_DIR recursively
    for root, dirs, files in os.walk(str(WATCH_DIR)):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith(".")]

        for fname in files:
            fpath = Path(root) / fname

            if should_skip_file(fpath):
                continue

            ext = fpath.suffix.lower()
            if ext not in ALL_EXTENSIONS:
                results["skipped"] += 1
                continue

            # Get relative path as key
            try:
                rel_key = str(fpath.relative_to(WATCH_DIR))
            except ValueError:
                rel_key = str(fpath)

            # Check if file is ready (not still being written)
            if not is_file_ready(str(fpath), wait_secs=2):
                logger.info(f"  ⏳ Đang chờ file ghi xong: {rel_key}")
                results["skipped"] += 1
                continue

            # Compute hash for change detection
            try:
                current_hash = compute_file_hash(str(fpath))
            except Exception:
                results["skipped"] += 1
                continue

            # Check if already imported with same hash
            if rel_key in imported and imported[rel_key].get("hash") == current_hash:
                results["skipped"] += 1
                continue

            is_update = rel_key in imported
            action = "cập nhật" if is_update else "nạp mới"
            logger.info(f"  📄 {action}: {rel_key}")

            try:
                success = import_single_file(fpath, db, admin_user)
                if success:
                    imported[rel_key] = {
                        "hash": current_hash,
                        "imported_at": datetime.now(timezone.utc).isoformat(),
                        "file_size": os.path.getsize(str(fpath)),
                        "file_type": ext,
                    }
                    if is_update:
                        results["updated"] += 1
                    else:
                        results["new"] += 1
                    results["details"].append(f"✓ {rel_key}")
                    logger.info(f"  ✓ Thành công: {rel_key}")
                else:
                    results["failed"] += 1
                    results["details"].append(f"✗ {rel_key}")
            except Exception as e:
                results["failed"] += 1
                results["details"].append(f"✗ {rel_key}: {str(e)[:100]}")
                logger.error(f"  ✗ Lỗi: {rel_key} - {e}")

    # Save manifest
    manifest["imported_files"] = imported
    manifest["last_scan"] = datetime.now(timezone.utc).isoformat()
    save_manifest(manifest)

    return results


def run_watcher(interval: int = 15):
    """Run continuous file watcher loop."""
    from app.db.session import SessionLocal

    logger.info("=" * 60)
    logger.info("  🤖 AUTO DOCUMENT WATCHER - Local AI Nội bộ doanh nghiệp")
    logger.info("=" * 60)
    logger.info(f"  📁 Thư mục giám sát: {WATCH_DIR}")
    logger.info(f"  ⏱️  Chu kỳ quét: mỗi {interval} giây")
    logger.info(f"  📋 Manifest: {MANIFEST_FILE}")
    logger.info("")
    logger.info("  Hỗ trợ: Văn bản | Hình ảnh (Vision AI) | Video (Keyframe)")
    logger.info("  Nhấn Ctrl+C để dừng.")
    logger.info("=" * 60)

    # Initial scan
    db = SessionLocal()
    try:
        admin_user = get_auto_import_user(db)
        if not admin_user:
            logger.error("Không tìm thấy tài khoản admin để gán quyền sở hữu tài liệu!")
            return

        logger.info(f"  👤 Tài khoản nạp: {admin_user.full_name} ({admin_user.username})")
        logger.info("")

        # First scan
        logger.info("🔍 Quét lần đầu...")
        results = scan_and_import(db, admin_user)
        _print_results(results)
    finally:
        db.close()

    # Watch loop using watchfiles (if available) or simple polling
    try:
        import watchfiles

        logger.info(f"\n👀 Bắt đầu giám sát thời gian thực (watchfiles)...")

        for changes in watchfiles.watch(
            str(WATCH_DIR),
            recursive=True,
            step=interval * 1000,
            rust_timeout=interval * 1000,
        ):
            # Filter relevant changes
            relevant = False
            for change_type, change_path in changes:
                p = Path(change_path)
                if p.is_file() and p.suffix.lower() in ALL_EXTENSIONS and not should_skip_file(p):
                    relevant = True
                    break

            if relevant:
                logger.info("\n📢 Phát hiện thay đổi, đang quét...")
                db = SessionLocal()
                try:
                    admin_user = get_auto_import_user(db)
                    if admin_user:
                        results = scan_and_import(db, admin_user)
                        _print_results(results)
                finally:
                    db.close()

    except ImportError:
        # Fallback to simple polling
        logger.info(f"\n👀 Bắt đầu giám sát (polling mỗi {interval}s)...")

        while True:
            time.sleep(interval)
            db = SessionLocal()
            try:
                admin_user = get_auto_import_user(db)
                if admin_user:
                    results = scan_and_import(db, admin_user)
                    if results["new"] + results["updated"] + results["failed"] > 0:
                        _print_results(results)
            except Exception as e:
                logger.error(f"Lỗi trong chu kỳ quét: {e}")
            finally:
                db.close()


def get_auto_import_user(db):
    """Get admin user for auto-import ownership."""
    from app.models.user import User
    from app.models.permission import Role

    admin = db.query(User).filter(User.username == "admin", User.is_active == True).first()
    if admin:
        return admin

    admin_role = db.query(Role).filter(Role.code == "SUPER_ADMIN").first()
    if admin_role:
        return db.query(User).filter(
            User.role_id == admin_role.id,
            User.is_active == True,
        ).first()
    return None


def _print_results(results: Dict):
    """Pretty-print scan results."""
    total = results["new"] + results["updated"] + results["failed"]
    if total == 0:
        logger.info("  ✅ Không có tài liệu mới cần nạp.")
        return

    logger.info(f"  📊 Kết quả: Mới={results['new']} | Cập nhật={results['updated']} | Lỗi={results['failed']}")
    for detail in results["details"]:
        logger.info(f"     {detail}")
    logger.info("")


def main():
    parser_args = argparse.ArgumentParser(description="Auto Document Watcher")
    parser_args.add_argument("--scan-once", action="store_true", help="Quét một lần rồi thoát")
    parser_args.add_argument("--interval", type=int, default=15, help="Chu kỳ quét (giây)")
    args = parser_args.parse_args()

    # Ensure watch directory exists
    WATCH_DIR.mkdir(parents=True, exist_ok=True)

    if args.scan_once:
        from app.db.session import SessionLocal
        db = SessionLocal()
        try:
            admin_user = get_auto_import_user(db)
            if not admin_user:
                logger.error("Không tìm thấy tài khoản admin!")
                return

            logger.info("🔍 Quét một lần...")
            results = scan_and_import(db, admin_user)
            _print_results(results)
        finally:
            db.close()
    else:
        try:
            run_watcher(interval=args.interval)
        except KeyboardInterrupt:
            logger.info("\n👋 Đã dừng Auto Document Watcher.")


if __name__ == "__main__":
    main()
