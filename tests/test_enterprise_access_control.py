"""Automated Test Suite for Enterprise Document Access Control (EDAC)."""

import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.db.base import Base
from app.db.session import get_db
import app.models  # noqa: F401
from app.models.role import Role
from app.models.department import Department
from app.models.user import User
from app.models.document import Document
from app.models.document_permission import DocumentPermission
from app.models.audit_log import AuditLog
from app.core.security import get_password_hash, create_access_token
from app.main import app
from app.rag.vectorstore import vector_store
from app.rag.embeddings import embeddings_client
from app.rag.pipeline import rag_pipeline

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()

    # Seed standard roles
    roles = {
        "SUPER_ADMIN": Role(code="SUPER_ADMIN", name="Super Admin"),
        "ADMIN": Role(code="ADMIN", name="Admin"),
        "MANAGER": Role(code="MANAGER", name="Manager"),
        "DEPARTMENT_MANAGER": Role(code="DEPARTMENT_MANAGER", name="Dept Manager"),
        "EMPLOYEE": Role(code="EMPLOYEE", name="Employee"),
        "VIEWER": Role(code="VIEWER", name="Viewer"),
        "IT_ADMIN": Role(code="IT_ADMIN", name="IT Admin"),
    }
    for r in roles.values():
        db.add(r)
    db.flush()

    # Seed departments
    depts = {
        "IT": Department(code="IT", name="Phòng CNTT"),
        "ACCOUNTING": Department(code="ACCOUNTING", name="Phòng Kế toán"),
        "HR": Department(code="HR", name="Phòng Nhân sự"),
        "LEGAL": Department(code="LEGAL", name="Phòng Pháp chế"),
        "MANAGEMENT": Department(code="MANAGEMENT", name="Ban Lãnh đạo"),
    }
    for d in depts.values():
        db.add(d)
    db.flush()

    # Seed users
    pwd_hash = get_password_hash("Test@123456")
    users = {
        "superadmin": User(username="superadmin", email="super@enterprise.local", full_name="Super Admin", hashed_password=pwd_hash, role_id=roles["SUPER_ADMIN"].id, department_id=depts["IT"].id),
        "admin": User(username="admin", email="admin@enterprise.local", full_name="Admin", hashed_password=pwd_hash, role_id=roles["ADMIN"].id, department_id=depts["MANAGEMENT"].id),
        "manager": User(username="manager", email="mgr@enterprise.local", full_name="Manager", hashed_password=pwd_hash, role_id=roles["MANAGER"].id, department_id=depts["MANAGEMENT"].id),
        "it_manager": User(username="it_manager", email="itmgr@enterprise.local", full_name="IT Manager", hashed_password=pwd_hash, role_id=roles["DEPARTMENT_MANAGER"].id, department_id=depts["IT"].id),
        "it_emp": User(username="it_emp", email="itemp@enterprise.local", full_name="IT Employee", hashed_password=pwd_hash, role_id=roles["EMPLOYEE"].id, department_id=depts["IT"].id),
        "acc_emp": User(username="acc_emp", email="accemp@enterprise.local", full_name="Acc Employee", hashed_password=pwd_hash, role_id=roles["EMPLOYEE"].id, department_id=depts["ACCOUNTING"].id),
        "hr_emp": User(username="hr_emp", email="hremp@enterprise.local", full_name="HR Employee", hashed_password=pwd_hash, role_id=roles["EMPLOYEE"].id, department_id=depts["HR"].id),
        "viewer": User(username="viewer", email="viewer@enterprise.local", full_name="Viewer", hashed_password=pwd_hash, role_id=roles["VIEWER"].id, department_id=depts["IT"].id),
    }
    for u in users.values():
        db.add(u)
    db.flush()

    # Seed documents
    docs = {
        "doc_it": Document(
            title="Quy trình Vận hành IT",
            file_name="it_sop.txt",
            stored_file_name="it_sop_uuid.txt",
            file_path="./uploads/it_sop.txt",
            file_type="TXT",
            file_size=1024,
            department_id=depts["IT"].id,
            document_type="SOP",
            category="IT",
            owner_id=users["it_manager"].id,
            uploaded_by=users["it_manager"].id,
            security_level="DEPARTMENT",
            status="INDEXED",
            rag_status="READY",
            version="1.0",
        ),
        "doc_acc": Document(
            title="Quy chế Chi tiêu và Thanh toán Kế toán",
            file_name="acc_policy.txt",
            stored_file_name="acc_policy_uuid.txt",
            file_path="./uploads/acc_policy.txt",
            file_type="TXT",
            file_size=2048,
            department_id=depts["ACCOUNTING"].id,
            document_type="POLICY",
            category="Accounting",
            owner_id=users["acc_emp"].id,
            uploaded_by=users["acc_emp"].id,
            security_level="DEPARTMENT",
            status="INDEXED",
            rag_status="READY",
            version="1.0",
        ),
        "doc_hr": Document(
            title="Sổ tay Nhân sự và Phúc lợi",
            file_name="hr_handbook.txt",
            stored_file_name="hr_handbook_uuid.txt",
            file_path="./uploads/hr_handbook.txt",
            file_type="TXT",
            file_size=3072,
            department_id=depts["HR"].id,
            document_type="GUIDE",
            category="HR",
            owner_id=users["hr_emp"].id,
            uploaded_by=users["hr_emp"].id,
            security_level="DEPARTMENT",
            status="INDEXED",
            rag_status="READY",
            version="1.0",
        ),
        "doc_public": Document(
            title="Văn hóa Doanh nghiệp và Bộ Quy tắc Ứng xử",
            file_name="public_code.txt",
            stored_file_name="public_code_uuid.txt",
            file_path="./uploads/public_code.txt",
            file_type="TXT",
            file_size=4096,
            department_id=None,
            document_type="GUIDE",
            category="Chung",
            owner_id=users["admin"].id,
            uploaded_by=users["admin"].id,
            security_level="PUBLIC",
            status="INDEXED",
            rag_status="READY",
            version="1.0",
        ),
        "doc_confidential": Document(
            title="Báo cáo M&A Tuyệt Mật 2026",
            file_name="m_and_a_confidential.txt",
            stored_file_name="m_and_a_uuid.txt",
            file_path="./uploads/m_and_a.txt",
            file_type="TXT",
            file_size=5120,
            department_id=depts["MANAGEMENT"].id,
            document_type="REPORT",
            category="Chiến lược",
            owner_id=users["admin"].id,
            uploaded_by=users["admin"].id,
            security_level="CONFIDENTIAL",
            status="INDEXED",
            rag_status="READY",
            version="1.0",
        ),
    }
    for d in docs.values():
        db.add(d)

    db.commit()
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


def auth_header(username: str) -> dict:
    """Generate Authorization header for a user."""
    db = TestingSessionLocal()
    user = db.query(User).filter(User.username == username).first()
    token = create_access_token(subject=str(user.id), role=user.role.code, department_id=user.department_id)
    db.close()
    return {"Authorization": f"Bearer {token}"}


# ==============================================================================
# 1. DEPARTMENT ISOLATION TESTS
# ==============================================================================

def test_it_employee_document_access():
    """IT Employee: Can access IT and PUBLIC docs; CANNOT access Accounting or HR docs."""
    resp = client.get("/api/v1/documents", headers=auth_header("it_emp"))
    assert resp.status_code == 200
    docs = resp.json()
    titles = [d["title"] for d in docs]

    assert "Quy trình Vận hành IT" in titles, "IT employee must see IT document"
    assert "Văn hóa Doanh nghiệp và Bộ Quy tắc Ứng xử" in titles, "IT employee must see PUBLIC document"
    assert "Quy chế Chi tiêu và Thanh toán Kế toán" not in titles, "IT employee must NOT see Accounting document"
    assert "Sổ tay Nhân sự và Phúc lợi" not in titles, "IT employee must NOT see HR document"
    assert "Báo cáo M&A Tuyệt Mật 2026" not in titles, "IT employee must NOT see CONFIDENTIAL document"


def test_accounting_employee_document_access():
    """Accounting Employee: Can access Accounting and PUBLIC docs; CANNOT access IT docs."""
    resp = client.get("/api/v1/documents", headers=auth_header("acc_emp"))
    assert resp.status_code == 200
    docs = resp.json()
    titles = [d["title"] for d in docs]

    assert "Quy chế Chi tiêu và Thanh toán Kế toán" in titles, "Accounting employee must see Accounting document"
    assert "Văn hóa Doanh nghiệp và Bộ Quy tắc Ứng xử" in titles, "Accounting employee must see PUBLIC document"
    assert "Quy trình Vận hành IT" not in titles, "Accounting employee must NOT see IT document"
    assert "Sổ tay Nhân sự và Phúc lợi" not in titles, "Accounting employee must NOT see HR document"


def test_hr_employee_document_access():
    """HR Employee: Can access HR and PUBLIC docs; CANNOT access IT or Accounting docs."""
    resp = client.get("/api/v1/documents", headers=auth_header("hr_emp"))
    assert resp.status_code == 200
    docs = resp.json()
    titles = [d["title"] for d in docs]

    assert "Sổ tay Nhân sự và Phúc lợi" in titles, "HR employee must see HR document"
    assert "Văn hóa Doanh nghiệp và Bộ Quy tắc Ứng xử" in titles, "HR employee must see PUBLIC document"
    assert "Quy trình Vận hành IT" not in titles, "HR employee must NOT see IT document"
    assert "Quy chế Chi tiêu và Thanh toán Kế toán" not in titles, "HR employee must NOT see Accounting document"


def test_admin_and_super_admin_full_access():
    """Super Admin & Admin: Can access all documents across all departments."""
    resp_admin = client.get("/api/v1/documents", headers=auth_header("admin"))
    assert resp_admin.status_code == 200
    admin_titles = [d["title"] for d in resp_admin.json()]

    assert "Quy trình Vận hành IT" in admin_titles
    assert "Quy chế Chi tiêu và Thanh toán Kế toán" in admin_titles
    assert "Sổ tay Nhân sự và Phúc lợi" in admin_titles
    assert "Báo cáo M&A Tuyệt Mật 2026" in admin_titles


# ==============================================================================
# 2. FILTER & SEARCH ACCESS CONTROL
# ==============================================================================

def test_it_employee_search_and_filter_cannot_leak_accounting():
    """When IT Employee queries Accounting department explicitly, Backend returns 0 results."""
    db = TestingSessionLocal()
    acc_dept = db.query(Department).filter(Department.code == "ACCOUNTING").first()
    db.close()

    resp = client.get(f"/api/v1/documents?department_id={acc_dept.id}", headers=auth_header("it_emp"))
    assert resp.status_code == 200
    assert len(resp.json()) == 0, "IT employee querying Accounting department must return 0 results"


def test_get_document_by_id_permission_enforcement():
    """Directly accessing /documents/{id} for unauthorized document returns HTTP 403 Forbidden."""
    db = TestingSessionLocal()
    acc_doc = db.query(Document).filter(Document.title == "Quy chế Chi tiêu và Thanh toán Kế toán").first()
    db.close()

    # IT Employee tries to view Accounting document directly
    resp = client.get(f"/api/v1/documents/{acc_doc.id}", headers=auth_header("it_emp"))
    assert resp.status_code == 403, "Direct access to unauthorized department document must return 403 Forbidden"


# ==============================================================================
# 3. GRANULAR DOCUMENT PERMISSIONS & CONFIDENTIAL ACCESS
# ==============================================================================

def test_confidential_document_explicit_grant():
    """Test granting explicit permission to an employee for a CONFIDENTIAL document."""
    db = TestingSessionLocal()
    conf_doc = db.query(Document).filter(Document.title == "Báo cáo M&A Tuyệt Mật 2026").first()
    it_user = db.query(User).filter(User.username == "it_emp").first()
    db.close()

    # 1. IT Employee cannot see confidential document initially
    resp = client.get(f"/api/v1/documents/{conf_doc.id}", headers=auth_header("it_emp"))
    assert resp.status_code == 403

    # 2. Admin grants VIEW permission to IT Employee
    resp_grant = client.post(
        f"/api/v1/documents/{conf_doc.id}/permissions",
        json={"user_id": str(it_user.id), "permission_type": "VIEW"},
        headers=auth_header("admin")
    )
    assert resp_grant.status_code == 201
    perm_id = resp_grant.json()["id"]

    # 3. IT Employee can now view the confidential document
    resp_view = client.get(f"/api/v1/documents/{conf_doc.id}", headers=auth_header("it_emp"))
    assert resp_view.status_code == 200
    assert resp_view.json()["title"] == "Báo cáo M&A Tuyệt Mật 2026"

    # 4. Admin revokes the permission
    resp_revoke = client.delete(
        f"/api/v1/documents/{conf_doc.id}/permissions/{perm_id}",
        headers=auth_header("admin")
    )
    assert resp_revoke.status_code == 200

    # 5. IT Employee is blocked again
    resp_blocked = client.get(f"/api/v1/documents/{conf_doc.id}", headers=auth_header("it_emp"))
    assert resp_blocked.status_code == 403


# ==============================================================================
# 4. RAG VECTOR STORE SECURITY
# ==============================================================================

def test_rag_vector_store_security_isolation():
    """Verify ChromaVectorStore.is_chunk_accessible enforces department and confidentiality."""
    db = TestingSessionLocal()
    it_user = db.query(User).filter(User.username == "it_emp").first()
    acc_user = db.query(User).filter(User.username == "acc_emp").first()
    admin_user = db.query(User).filter(User.username == "admin").first()
    db.close()

    meta_it = {"department_id": it_user.department_id, "security_level": "DEPARTMENT", "title": "IT Guide"}
    meta_acc = {"department_id": acc_user.department_id, "security_level": "DEPARTMENT", "title": "Acc Policy"}
    meta_conf = {"department_id": 999, "security_level": "CONFIDENTIAL", "title": "Confidential Report", "allowed_users": str(it_user.id)}

    # IT User
    assert vector_store.is_chunk_accessible(meta_it, it_user) is True
    assert vector_store.is_chunk_accessible(meta_acc, it_user) is False, "IT user must not access Accounting chunk"
    assert vector_store.is_chunk_accessible(meta_conf, it_user) is True, "IT user has explicit access in allowed_users"

    # Accounting User
    assert vector_store.is_chunk_accessible(meta_it, acc_user) is False
    assert vector_store.is_chunk_accessible(meta_acc, acc_user) is True
    assert vector_store.is_chunk_accessible(meta_conf, acc_user) is False

    # Admin User
    assert vector_store.is_chunk_accessible(meta_it, admin_user) is True
    assert vector_store.is_chunk_accessible(meta_acc, admin_user) is True
    assert vector_store.is_chunk_accessible(meta_conf, admin_user) is True


# ==============================================================================
# 5. AUDIT LOGGING VERIFICATION
# ==============================================================================

def test_audit_logs_recorded():
    """Verify VIEW, SEARCH, and PERMISSION_CHANGE actions are recorded in AuditLog."""
    db = TestingSessionLocal()
    it_doc = db.query(Document).filter(Document.title == "Quy trình Vận hành IT").first()
    db.close()

    # 1. Trigger SEARCH
    client.get("/api/v1/documents?search=Vận+hành", headers=auth_header("it_emp"))

    # 2. Trigger VIEW
    client.get(f"/api/v1/documents/{it_doc.id}", headers=auth_header("it_emp"))

    db = TestingSessionLocal()
    logs = db.query(AuditLog).filter(AuditLog.resource == "DOCUMENTS").all()
    actions = [l.action for l in logs]
    db.close()

    assert "SEARCH" in actions, "SEARCH action must be recorded in AuditLog"
    assert "VIEW" in actions, "VIEW action must be recorded in AuditLog"
    assert "PERMISSION_CHANGE" in actions, "PERMISSION_CHANGE action must be recorded in AuditLog"
