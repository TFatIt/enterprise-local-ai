"""Unit tests for Phase 12: Admin Dashboard & Analytics."""

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


def test_employee_forbidden_from_dashboard():
    """Verify that EMPLOYEE is restricted from viewing Admin Dashboard (403 Forbidden)."""
    emp_token = get_token_for("employee", "User@123456")
    resp = client.get("/api/v1/dashboard/stats", headers={"Authorization": f"Bearer {emp_token}"})
    assert resp.status_code == 403


def test_super_admin_can_access_dashboard():
    """Verify that SUPER_ADMIN receives complete aggregated analytics."""
    admin_token = get_token_for("superadmin", "Admin@123456")
    resp = client.get("/api/v1/dashboard/stats", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    data = resp.json()

    assert "summary" in data
    summary = data["summary"]
    assert summary["total_users"] >= 3
    assert summary["total_departments"] >= 3
    assert "total_documents" in summary
    assert "total_chunks" in summary
    assert "total_questions" in summary
    assert "total_tickets" in summary
    assert "ai_resolution_rate" in summary
    assert isinstance(summary["ai_resolution_rate"], (int, float))

    assert "tickets_by_category" in data
    assert "tickets_by_status" in data
    assert "tickets_by_priority" in data
    assert "recent_activities" in data
    assert isinstance(data["recent_activities"], list)


def test_it_admin_can_access_dashboard():
    """Verify that IT_ADMIN also has permission to monitor Dashboard."""
    it_token = get_token_for("itadmin", "Admin@123456")
    resp = client.get("/api/v1/dashboard/stats", headers={"Authorization": f"Bearer {it_token}"})
    assert resp.status_code == 200
    assert "summary" in resp.json()


def test_dashboard_metrics_aggregation_accuracy():
    """Verify metrics increment accurately when new tickets and users are created."""
    admin_token = get_token_for("superadmin", "Admin@123456")
    headers = {"Authorization": f"Bearer {admin_token}"}

    initial_stats = client.get("/api/v1/dashboard/stats", headers=headers).json()
    initial_tickets = initial_stats["summary"]["total_tickets"]

    # Create a new ticket
    client.post(
        "/api/v1/tickets",
        json={
            "title": "Mất mạng Switch tầng 3",
            "description": "Toàn bộ phòng kinh doanh tầng 3 bị rớt mạng dây.",
            "category": "NETWORK",
            "priority": "HIGH"
        },
        headers=headers
    )

    updated_stats = client.get("/api/v1/dashboard/stats", headers=headers).json()
    assert updated_stats["summary"]["total_tickets"] == initial_tickets + 1
