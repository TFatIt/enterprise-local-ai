"""Unit tests for Phase 11: IT Support Ticket System."""

import sys
import os
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


def test_employee_create_ticket_standalone():
    """Verify that employee can create an IT ticket."""
    emp_token = get_token_for("employee", "User@123456")
    headers = {"Authorization": f"Bearer {emp_token}"}

    resp = client.post(
        "/api/v1/tickets",
        json={
            "title": "Màn hình Dell không lên nguồn",
            "description": "Sau khi khởi động sáng nay, màn hình nhấp nháy đèn vàng rồi tắt hẳn.",
            "category": "HARDWARE",
            "priority": "HIGH"
        },
        headers=headers
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["ticket_code"].startswith("TK-")
    assert data["title"] == "Màn hình Dell không lên nguồn"
    assert data["status"] == "OPEN"
    assert data["category"] == "HARDWARE"
    assert data["priority"] == "HIGH"


def test_employee_create_ticket_from_chat():
    """Verify creating a ticket linked to a chat session."""
    emp_token = get_token_for("employee", "User@123456")
    headers = {"Authorization": f"Bearer {emp_token}"}

    # 1. Create chat session
    sess_resp = client.post("/api/v1/chat/sessions", json={"title": "Hỏi lỗi mạng VPN"}, headers=headers)
    session_id = sess_resp.json()["id"]

    # 2. Escalate to ticket
    resp = client.post(
        "/api/v1/tickets",
        json={
            "title": "Cần hỗ trợ reset cấu hình VPN",
            "description": "AI không tìm thấy tài liệu giải quyết lỗi VPN code 800.",
            "category": "NETWORK",
            "priority": "URGENT",
            "chat_session_id": session_id
        },
        headers=headers
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["chat_session_id"] == session_id


def test_ticket_isolation_and_rbac():
    """Verify employees only see their own tickets while IT Admin sees all."""
    emp_token = get_token_for("employee", "User@123456")
    it_token = get_token_for("itadmin", "Admin@123456")

    # Employee lists tickets
    emp_list = client.get("/api/v1/tickets", headers={"Authorization": f"Bearer {emp_token}"}).json()
    assert len(emp_list) >= 2

    # IT Admin creates a separate ticket
    client.post(
        "/api/v1/tickets",
        json={
            "title": "Bảo trì máy chủ DC-01",
            "description": "Cần nâng cấp RAM cho Active Directory Domain Controller.",
            "category": "HARDWARE",
            "priority": "MEDIUM"
        },
        headers={"Authorization": f"Bearer {it_token}"}
    )

    # IT Admin should see more tickets than employee
    it_list = client.get("/api/v1/tickets", headers={"Authorization": f"Bearer {it_token}"}).json()
    emp_list_again = client.get("/api/v1/tickets", headers={"Authorization": f"Bearer {emp_token}"}).json()

    assert len(it_list) > len(emp_list_again)


def test_it_admin_assignment_and_lifecycle():
    """Verify IT Admin can assign, change status to IN_PROGRESS and RESOLVED with resolution notes."""
    emp_token = get_token_for("employee", "User@123456")
    it_token = get_token_for("itadmin", "Admin@123456")

    # Get IT Admin User ID
    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {it_token}"}).json()
    itadmin_id = me_resp["id"]

    # Create ticket by employee
    ticket_resp = client.post(
        "/api/v1/tickets",
        json={
            "title": "Bàn phím bị liệt phím Space",
            "description": "Bàn phím cơ văn phòng bị kẹt phím Space.",
            "category": "HARDWARE",
            "priority": "LOW"
        },
        headers={"Authorization": f"Bearer {emp_token}"}
    )
    ticket_id = ticket_resp.json()["id"]

    # 1. Employee cannot assign ticket (403 Forbidden)
    emp_assign = client.patch(
        f"/api/v1/tickets/{ticket_id}/assign",
        json={"assigned_to": itadmin_id},
        headers={"Authorization": f"Bearer {emp_token}"}
    )
    assert emp_assign.status_code == 403

    # 2. IT Admin assigns ticket
    it_assign = client.patch(
        f"/api/v1/tickets/{ticket_id}/assign",
        json={"assigned_to": itadmin_id},
        headers={"Authorization": f"Bearer {it_token}"}
    )
    assert it_assign.status_code == 200
    assert it_assign.json()["assigned_to"] == itadmin_id
    assert it_assign.json()["status"] == "IN_PROGRESS"

    # 3. IT Admin resolves ticket
    resolve_resp = client.patch(
        f"/api/v1/tickets/{ticket_id}/status",
        json={
            "status": "RESOLVED",
            "resolution_notes": "Đã vệ sinh switch và thay thế keycap mới cho nhân viên."
        },
        headers={"Authorization": f"Bearer {it_token}"}
    )
    assert resolve_resp.status_code == 200
    resolved_data = resolve_resp.json()
    assert resolved_data["status"] == "RESOLVED"
    assert "Đã vệ sinh switch" in resolved_data["resolution_notes"]


def test_ticket_comments_and_internal_notes():
    """Verify commenting and ensure internal notes are hidden from regular employees."""
    emp_token = get_token_for("employee", "User@123456")
    it_token = get_token_for("itadmin", "Admin@123456")

    ticket_resp = client.post(
        "/api/v1/tickets",
        json={
            "title": "Yêu cầu cấp quyền thư mục Kế toán",
            "description": "Nhân viên mới cần truy cập thư mục Shared/KeToan.",
            "category": "ACCOUNT",
            "priority": "HIGH"
        },
        headers={"Authorization": f"Bearer {emp_token}"}
    )
    ticket_id = ticket_resp.json()["id"]

    # 1. Employee adds a public comment
    c1 = client.post(
        f"/api/v1/tickets/{ticket_id}/comments",
        json={"content": "Em đã gửi form xác nhận từ Trưởng phòng qua email ạ.", "is_internal": False},
        headers={"Authorization": f"Bearer {emp_token}"}
    )
    assert c1.status_code == 201

    # 2. Employee cannot create internal comment (403 Forbidden)
    c2 = client.post(
        f"/api/v1/tickets/{ticket_id}/comments",
        json={"content": "Ghi chú nội bộ hack", "is_internal": True},
        headers={"Authorization": f"Bearer {emp_token}"}
    )
    assert c2.status_code == 403

    # 3. IT Admin adds internal note
    c3 = client.post(
        f"/api/v1/tickets/{ticket_id}/comments",
        json={"content": "Đã kiểm tra Active Directory group GG-KeToan-ReadWrite, đang chờ replicate.", "is_internal": True},
        headers={"Authorization": f"Bearer {it_token}"}
    )
    assert c3.status_code == 201

    # 4. Check visibility: Employee only sees public comment
    emp_view = client.get(f"/api/v1/tickets/{ticket_id}", headers={"Authorization": f"Bearer {emp_token}"}).json()
    assert len(emp_view["comments"]) == 1
    assert "Trưởng phòng" in emp_view["comments"][0]["content"]

    # 5. Check visibility: IT Admin sees both comments
    it_view = client.get(f"/api/v1/tickets/{ticket_id}", headers={"Authorization": f"Bearer {it_token}"}).json()
    assert len(it_view["comments"]) == 2
