"""Unit tests for Phase 4: User Management and Role-Based Access Control (RBAC)."""

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
    """Helper to acquire JWT token for a given user."""
    resp = client.post("/api/v1/auth/login", json={"username_or_email": username, "password": password})
    return resp.json()["access_token"]


def test_employee_cannot_access_users_endpoint():
    """Verify that EMPLOYEE is blocked with HTTP 403 from listing users."""
    token = get_token_for("employee", "User@123456")
    response = client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    assert "không có quyền" in response.json()["detail"]


def test_it_admin_cannot_access_users_endpoint():
    """Verify that IT_ADMIN is also blocked from user management (Super Admin exclusive)."""
    token = get_token_for("itadmin", "Admin@123456")
    response = client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_super_admin_can_list_users():
    """Verify that SUPER_ADMIN can retrieve user accounts."""
    token = get_token_for("superadmin", "Admin@123456")
    response = client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    users = response.json()
    assert len(users) >= 3
    emails = [u["email"] for u in users]
    assert "admin@enterprise.local" in emails


def test_super_admin_create_user_success():
    """Verify that SUPER_ADMIN can create a new employee account."""
    token = get_token_for("superadmin", "Admin@123456")
    payload = {
        "email": "new.developer@enterprise.local",
        "username": "newdev",
        "full_name": "Nguyen Van A",
        "password": "SecurePassword123!",
        "role_code": "EMPLOYEE",
        "department_id": 1
    }
    response = client.post("/api/v1/users", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201
    created_user = response.json()
    assert created_user["email"] == "new.developer@enterprise.local"
    assert created_user["role"] == "EMPLOYEE"


def test_create_user_duplicate_email_rejected():
    """Verify that creating a user with an existing email returns HTTP 400."""
    token = get_token_for("superadmin", "Admin@123456")
    payload = {
        "email": "admin@enterprise.local",
        "username": "superadmin2",
        "full_name": "Another Admin",
        "password": "SecurePassword123!",
        "role_code": "SUPER_ADMIN"
    }
    response = client.post("/api/v1/users", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 400
    assert "đã tồn tại" in response.json()["detail"]


def test_super_admin_update_and_deactivate_user():
    """Verify updating and deactivating user accounts."""
    token = get_token_for("superadmin", "Admin@123456")

    # Find created user
    list_resp = client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})
    user_id = next(u["id"] for u in list_resp.json() if u["username"] == "newdev")

    # Update full_name
    update_resp = client.put(
        f"/api/v1/users/{user_id}",
        json={"full_name": "Nguyen Van A Updated"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["full_name"] == "Nguyen Van A Updated"

    # Deactivate
    del_resp = client.delete(f"/api/v1/users/{user_id}", headers={"Authorization": f"Bearer {token}"})
    assert del_resp.status_code == 200

    # Verify is_active == False
    check_resp = client.get(f"/api/v1/users/{user_id}", headers={"Authorization": f"Bearer {token}"})
    assert check_resp.json()["is_active"] is False


def test_department_and_roles_endpoints():
    """Verify department listing and creation permissions."""
    emp_token = get_token_for("employee", "User@123456")
    admin_token = get_token_for("superadmin", "Admin@123456")

    # Employee can list departments
    dept_resp = client.get("/api/v1/departments", headers={"Authorization": f"Bearer {emp_token}"})
    assert dept_resp.status_code == 200
    assert len(dept_resp.json()) >= 3

    # Employee cannot create department (HTTP 403)
    post_resp = client.post(
        "/api/v1/departments",
        json={"code": "MARKETING", "name": "Phong Marketing"},
        headers={"Authorization": f"Bearer {emp_token}"}
    )
    assert post_resp.status_code == 403

    # Super Admin can create department (HTTP 201)
    admin_post_resp = client.post(
        "/api/v1/departments",
        json={"code": "MARKETING", "name": "Phong Marketing"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert admin_post_resp.status_code == 201
    assert admin_post_resp.json()["code"] == "MARKETING"
