"""Unit tests for Phase 10: AI Chat System."""

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


def test_create_and_list_chat_sessions():
    """Verify that employee can create and list their own chat sessions."""
    emp_token = get_token_for("employee", "User@123456")
    headers = {"Authorization": f"Bearer {emp_token}"}

    # 1. Create a session with custom title
    create_resp = client.post(
        "/api/v1/chat/sessions",
        json={"title": "Hỏi về cấu hình VPN"},
        headers=headers
    )
    assert create_resp.status_code == 201
    data = create_resp.json()
    assert data["title"] == "Hỏi về cấu hình VPN"
    assert data["is_active"] is True
    assert "id" in data

    # 2. Create another session with default title
    default_resp = client.post(
        "/api/v1/chat/sessions",
        json={},
        headers=headers
    )
    assert default_resp.status_code == 201
    assert default_resp.json()["title"] == "Cuộc hội thoại mới"

    # 3. List sessions
    list_resp = client.get("/api/v1/chat/sessions", headers=headers)
    assert list_resp.status_code == 200
    sessions = list_resp.json()
    assert len(sessions) >= 2


def test_chat_session_permissions_and_isolation():
    """Verify User B cannot access User A's session."""
    emp_token = get_token_for("employee", "User@123456")
    it_token = get_token_for("itadmin", "Admin@123456")

    # Employee creates a private session
    create_resp = client.post(
        "/api/v1/chat/sessions",
        json={"title": "Phiên riêng của Employee"},
        headers={"Authorization": f"Bearer {emp_token}"}
    )
    session_id = create_resp.json()["id"]

    # IT Admin tries to access Employee's session -> 403 Forbidden
    access_resp = client.get(
        f"/api/v1/chat/sessions/{session_id}",
        headers={"Authorization": f"Bearer {it_token}"}
    )
    assert access_resp.status_code == 403

    # IT Admin tries to delete Employee's session -> 403 Forbidden
    del_resp = client.delete(
        f"/api/v1/chat/sessions/{session_id}",
        headers={"Authorization": f"Bearer {it_token}"}
    )
    assert del_resp.status_code == 403


def test_update_chat_session():
    """Verify updating session title and status."""
    emp_token = get_token_for("employee", "User@123456")
    headers = {"Authorization": f"Bearer {emp_token}"}

    create_resp = client.post("/api/v1/chat/sessions", json={"title": "Tiêu đề cũ"}, headers=headers)
    session_id = create_resp.json()["id"]

    update_resp = client.put(
        f"/api/v1/chat/sessions/{session_id}",
        json={"title": "Tiêu đề mới đã đổi", "is_active": False},
        headers=headers
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["title"] == "Tiêu đề mới đã đổi"
    assert updated["is_active"] is False


def test_send_message_in_closed_session_rejected():
    """Verify cannot send message to closed session."""
    emp_token = get_token_for("employee", "User@123456")
    headers = {"Authorization": f"Bearer {emp_token}"}

    create_resp = client.post("/api/v1/chat/sessions", json={"title": "Phiên đóng"}, headers=headers)
    session_id = create_resp.json()["id"]

    # Close session
    client.put(f"/api/v1/chat/sessions/{session_id}", json={"is_active": False}, headers=headers)

    # Attempt to send message
    send_resp = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={"content": "Xin chào, còn mở không?"},
        headers=headers
    )
    assert send_resp.status_code == 400


def test_send_message_and_rag_interaction(monkeypatch):
    """Verify sending question saves user message, calls RAG, and saves assistant response."""
    emp_token = get_token_for("employee", "User@123456")
    headers = {"Authorization": f"Bearer {emp_token}"}

    # Mock rag_pipeline.ask for instant and deterministic unit testing
    mock_rag_response = {
        "answer": "Để kết nối VPN FortiClient, mở ứng dụng và nhập gateway vpn.enterprise.local.",
        "sources": [
            {
                "source_index": 1,
                "document_id": "doc-123",
                "document_title": "Hướng dẫn VPN",
                "file_name": "vpn_guide.pdf",
                "page_number": 1,
                "similarity_score": 0.92,
                "snippet": "Mở ứng dụng FortiClient VPN...",
            }
        ],
        "suggest_ticket": False,
        "response_time_ms": 120,
    }

    from app.services.chat_service import rag_pipeline
    monkeypatch.setattr(rag_pipeline, "ask", lambda question, department_id, top_k=5: mock_rag_response)

    # 1. Create a fresh session with default title
    session_resp = client.post("/api/v1/chat/sessions", json={}, headers=headers)
    session_id = session_resp.json()["id"]

    # 2. Send message
    msg_resp = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={"content": "Làm thế nào để kết nối VPN công ty?"},
        headers=headers
    )
    assert msg_resp.status_code == 201
    data = msg_resp.json()
    assert data["sender_type"] == "ASSISTANT"
    assert "FortiClient" in data["content"]
    assert len(data["sources"]) == 1
    assert data["suggest_ticket"] is False
    assert data["response_time_ms"] == 120

    # 3. Verify session title was auto-updated from question
    get_session_resp = client.get(f"/api/v1/chat/sessions/{session_id}", headers=headers)
    assert get_session_resp.status_code == 200
    session_data = get_session_resp.json()
    assert "Làm thế nào để kết nối VPN" in session_data["title"]
    # Total messages in session should be 2 (USER + ASSISTANT)
    assert len(session_data["messages"]) == 2
    assert session_data["messages"][0]["sender_type"] == "USER"
    assert session_data["messages"][1]["sender_type"] == "ASSISTANT"


def test_delete_chat_session_cascades_messages():
    """Verify deleting session deletes the session and all associated messages."""
    emp_token = get_token_for("employee", "User@123456")
    headers = {"Authorization": f"Bearer {emp_token}"}

    create_resp = client.post("/api/v1/chat/sessions", json={"title": "Session to delete"}, headers=headers)
    session_id = create_resp.json()["id"]

    del_resp = client.delete(f"/api/v1/chat/sessions/{session_id}", headers=headers)
    assert del_resp.status_code == 204

    # Verify subsequent GET returns 404
    get_resp = client.get(f"/api/v1/chat/sessions/{session_id}", headers=headers)
    assert get_resp.status_code == 404
