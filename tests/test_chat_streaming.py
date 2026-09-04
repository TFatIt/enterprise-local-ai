"""Tests for Chat Server-Sent Events (SSE) streaming endpoint."""

import os
import sys
import json
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


def get_token(username_or_email: str, password: str = "Admin@123456") -> str:
    res = client.post(
        "/api/v1/auth/login",
        json={"username_or_email": username_or_email, "password": password}
    )
    return res.json()["access_token"]


def test_chat_message_stream_flow():
    token = get_token("employee@enterprise.local", "Employee@123456")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create a session
    sess_res = client.post("/api/v1/chat/sessions", json={"title": "Test Stream Session"}, headers=headers)
    assert sess_res.status_code == 201
    session_id = sess_res.json()["id"]

    # 2. Call stream endpoint
    with client.stream(
        "POST",
        f"/api/v1/chat/sessions/{session_id}/messages/stream",
        json={"content": "Làm thế nào để kết nối VPN công ty?"},
        headers=headers,
    ) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

        events = []
        for line in response.iter_lines():
            if line.startswith("data: "):
                event_data = json.loads(line[6:])
                events.append(event_data)

        # Check events structure
        types = [e.get("type") for e in events]
        assert "metadata" in types
        assert "token" in types or "done" in types
        assert "done" in types

    # 3. Verify messages were saved in DB
    msg_res = client.get(f"/api/v1/chat/sessions/{session_id}/messages", headers=headers)
    assert msg_res.status_code == 200
    messages = msg_res.json()
    assert len(messages) >= 2
    assert messages[0]["sender_type"] == "USER"
    assert messages[1]["sender_type"] == "ASSISTANT"
