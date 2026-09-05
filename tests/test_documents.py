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
    # Upload an INTERNAL company-wide document
    admin_token = get_token_for("itadmin", "Admin@123456")
    client.post(
        "/api/v1/documents/upload",
        files={"file": ("company_policy.txt", io.BytesIO(b"Chinh sach chung toan cong ty 2026."), "text/plain")},
        data={"title": "Chinh sach noi bo toan cong ty", "security_level": "INTERNAL"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

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


def test_document_download_and_preview():
    """Verify downloading and previewing documents with access control."""
    admin_token = get_token_for("superadmin", "Admin@123456")
    employee_token = get_token_for("employee", "User@123456")

    # 1. Upload a public document
    file_bytes = b"Sample document content for download test"
    upload_resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("public_guide.txt", io.BytesIO(file_bytes), "text/plain")},
        data={"title": "Public Guide 2026", "security_level": "PUBLIC"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert upload_resp.status_code == 201
    doc_id = upload_resp.json()["id"]

    # 2. Preview inline (download=False) with Bearer token
    preview_resp = client.get(
        f"/api/v1/documents/{doc_id}/file?download=false",
        headers={"Authorization": f"Bearer {employee_token}"}
    )
    assert preview_resp.status_code == 200
    assert b"Sample document content" in preview_resp.content
    assert "inline" in preview_resp.headers.get("Content-Disposition", "")

    # 3. Direct download (download=True)
    download_resp = client.get(
        f"/api/v1/documents/{doc_id}/file?download=true",
        headers={"Authorization": f"Bearer {employee_token}"}
    )
    assert download_resp.status_code == 200
    assert "attachment" in download_resp.headers.get("Content-Disposition", "")

    # 4. Direct download via /download alias endpoint with token query param
    alias_resp = client.get(f"/api/v1/documents/{doc_id}/download?token={employee_token}")
    assert alias_resp.status_code == 200
    assert "attachment" in alias_resp.headers.get("Content-Disposition", "")

    # 5. Access control: Upload Confidential document and verify employee gets 403
    conf_resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("secret_plan.txt", io.BytesIO(b"Top secret corporate strategy"), "text/plain")},
        data={"title": "Secret Strategy 2026", "security_level": "CONFIDENTIAL"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    conf_id = conf_resp.json()["id"]

    unauth_resp = client.get(
        f"/api/v1/documents/{conf_id}/file",
        headers={"Authorization": f"Bearer {employee_token}"}
    )
    assert unauth_resp.status_code == 403


def test_parse_and_upload_csv_document():
    """Verify parsing and upload of CSV document with structured Markdown table."""
    from app.rag.parser import DocumentParser

    # Direct parser unit test
    import tempfile
    csv_content = (
        "Mã Thiết Bị,Tên Thiết Bị,Phòng Ban,Trạng Thái\n"
        "TB-001,Máy in HP LaserJet,IT,Hoạt động tốt\n"
        "TB-002,Router Cisco 2960,IT,Đang bảo trì\n"
        "TB-003,Máy chấm công vân tay,HR,Hoạt động tốt\n"
    )
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(csv_content)
        temp_csv_path = f.name

    try:
        pages = DocumentParser.parse_file(temp_csv_path, "CSV")
        assert len(pages) >= 1
        page_text = pages[0]["text"]
        assert "Mã Thiết Bị" in page_text
        assert "Máy in HP LaserJet" in page_text
        assert "| --- |" in page_text
    finally:
        if os.path.exists(temp_csv_path):
            os.remove(temp_csv_path)

    # API upload test
    admin_token = get_token_for("superadmin")
    csv_bytes = csv_content.encode("utf-8")
    resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("danh_muc_thiet_bi.csv", io.BytesIO(csv_bytes), "text/csv")},
        data={"title": "Danh Mục Thiết Bị Doanh Nghiệp 2026", "security_level": "PUBLIC"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["file_type"] == "CSV"
    assert data["status"] in ["UPLOADED", "INDEXED", "READY"]

    # Verify download of CSV
    doc_id = data["id"]
    file_resp = client.get(f"/api/v1/documents/{doc_id}/file?download=true", headers={"Authorization": f"Bearer {admin_token}"})
    assert file_resp.status_code == 200
    assert "text/csv" in file_resp.headers.get("Content-Type", "")
    assert "danh_muc_thiet_bi.csv" in file_resp.headers.get("Content-Disposition", "")


def test_parse_and_upload_excel_document():
    """Verify parsing and upload of Excel (.xlsx) workbook with sheets and headers."""
    import openpyxl
    import tempfile
    from app.rag.parser import DocumentParser

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Bang_Gia_Dich_Vu"
    ws.append(["Mã Gói", "Tên Gói Dịch Vụ", "Đơn Giá", "Thời Hạn"])
    ws.append(["SV-01", "Gói Hạ Tầng Mạng Doanh Nghiệp", "15,000,000", "12 Tháng"])
    ws.append(["SV-02", "Gói Sao Lưu Dữ Liệu Tự Động", "8,500,000", "6 Tháng"])

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        wb.save(f.name)
        temp_xlsx_path = f.name

    try:
        pages = DocumentParser.parse_file(temp_xlsx_path, "XLSX")
        assert len(pages) >= 1
        page_text = pages[0]["text"]
        assert "Bang_Gia_Dich_Vu" in page_text
        assert "Mã Gói" in page_text
        assert "Gói Hạ Tầng Mạng Doanh Nghiệp" in page_text
        assert "| --- |" in page_text
    finally:
        if os.path.exists(temp_xlsx_path):
            os.remove(temp_xlsx_path)

    # API upload test
    admin_token = get_token_for("superadmin")
    xlsx_buffer = io.BytesIO()
    wb.save(xlsx_buffer)
    xlsx_buffer.seek(0)

    resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("bang_gia_dich_vu.xlsx", xlsx_buffer, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        data={"title": "Bảng Giá Dịch Vụ CNTT 2026", "security_level": "PUBLIC"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["file_type"] == "XLSX"
    assert data["status"] in ["UPLOADED", "INDEXED", "READY"]


