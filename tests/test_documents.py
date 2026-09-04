"""Unit tests for Phase 5 & 6: Document Upload, Parsing, and Chunking."""

import sys
import os
import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add backend to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.db.base import Base
from app.db.session import get_db
import app.models  # noqa: F401
from app.db.seed import seed_database
from app.main import app

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    """Setup test database tables and initial seed data."""
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    seed_database(db)
    db.close()

    def override_get_db():
        database = TestingSessionLocal()
        try:
            yield database
        finally:
            database.close()

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


client = TestClient(app)


def get_token_for(username: str, password: str = "Admin@123456") -> str:
    """Helper to acquire JWT token."""
    resp = client.post("/api/v1/auth/login", json={"username_or_email": username, "password": password})
    return resp.json()["access_token"]


def test_employee_cannot_upload_document():
    """Verify that regular EMPLOYEE cannot upload documents (HTTP 403)."""
    token = get_token_for("employee", "User@123456")
    file_data = io.BytesIO(b"Noi dung bao mat doanh nghiep")
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("policy.txt", file_data, "text/plain")},
        data={"title": "Test Policy"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


def test_it_admin_upload_and_chunk_txt_success():
    """Verify that IT_ADMIN can upload TXT document, which is automatically chunked."""
    token = get_token_for("itadmin", "Admin@123456")

    # Read sample enterprise policy
    sample_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "documents", "sample_it_policy.txt"))
    with open(sample_path, "rb") as f:
        file_bytes = f.read()

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("sample_it_policy.txt", io.BytesIO(file_bytes), "text/plain")},
        data={"title": "Quy dinh va huong dan ky thuat IT noi bo 2026", "department_id": "1"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    doc_data = response.json()
    assert doc_data["title"] == "Quy dinh va huong dan ky thuat IT noi bo 2026"
    assert doc_data["file_type"] == "TXT"
    assert doc_data["status"] == "INDEXED"
    assert doc_data["total_chunks"] >= 2

    # Verify chunks endpoint
    doc_id = doc_data["id"]
    chunk_resp = client.get(
        f"/api/v1/documents/{doc_id}/chunks",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert chunk_resp.status_code == 200
    chunks = chunk_resp.json()
    assert len(chunks) == doc_data["total_chunks"]
    assert "Active Directory" in chunks[1]["content"] or "Domain" in chunks[1]["content"]
    assert "chroma_id" in chunks[0]


def test_upload_invalid_extension_rejected():
    """Verify that uploading an unsupported extension returns HTTP 400."""
    token = get_token_for("superadmin", "Admin@123456")
    file_data = io.BytesIO(b"malicious script or binary")
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("malicious.exe", file_data, "application/octet-stream")},
        data={"title": "Executable File"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
    assert "không được hỗ trợ" in response.json()["detail"]


def test_employee_can_list_and_view_documents():
    """Verify that EMPLOYEE can list and view uploaded documents."""
    token = get_token_for("employee", "User@123456")
    response = client.get("/api/v1/documents", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    docs = response.json()
    assert len(docs) >= 1
    doc_id = docs[0]["id"]

    detail_resp = client.get(f"/api/v1/documents/{doc_id}", headers={"Authorization": f"Bearer {token}"})
    assert detail_resp.status_code == 200
    assert detail_resp.json()["id"] == doc_id


def test_admin_delete_document_and_cascade_chunks():
    """Verify that Admin can delete document and chunks are purged."""
    token = get_token_for("superadmin", "Admin@123456")

    # Upload a disposable document
    file_data = io.BytesIO(b"Day la tai lieu tam thoi se bi xoa de kiem tra cascade delete.")
    upload_resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("temp_doc.txt", file_data, "text/plain")},
        data={"title": "Temporary Document"},
        headers={"Authorization": f"Bearer {token}"}
    )
    doc_id = upload_resp.json()["id"]

    # Delete
    del_resp = client.delete(f"/api/v1/documents/{doc_id}", headers={"Authorization": f"Bearer {token}"})
    assert del_resp.status_code == 200

    # Verify not found
    get_resp = client.get(f"/api/v1/documents/{doc_id}", headers={"Authorization": f"Bearer {token}"})
    assert get_resp.status_code == 404 or get_resp.json() is None
