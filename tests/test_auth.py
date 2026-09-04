"""Comprehensive unit tests for Authentication API endpoints and JWT tokens."""

import sys
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.db.base import Base
from app.db.session import get_db
import app.models  # noqa: F401
from app.db.seed import seed_database
from app.main import app

from sqlalchemy.pool import StaticPool

# Create in-memory test database with StaticPool so all sessions share the same memory database
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


def test_login_success_email():
    """Test successful login using email address."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username_or_email": "admin@enterprise.local", "password": "Admin@123456"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "admin@enterprise.local"
    assert data["user"]["role"] == "SUPER_ADMIN"


def test_login_success_username():
    """Test successful login using username."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username_or_email": "itadmin", "password": "Admin@123456"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["username"] == "itadmin"
    assert data["user"]["role"] == "IT_ADMIN"


def test_login_wrong_password():
    """Test that incorrect password returns HTTP 401."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username_or_email": "admin@enterprise.local", "password": "WrongPassword999!"}
    )
    assert response.status_code == 401
    assert "không chính xác" in response.json()["detail"]


def test_login_nonexistent_user():
    """Test that non-existent user returns HTTP 401."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username_or_email": "unknown@enterprise.local", "password": "AnyPassword123!"}
    )
    assert response.status_code == 401


def test_get_me_success():
    """Test retrieving current user profile with valid Bearer token."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"username_or_email": "employee@enterprise.local", "password": "User@123456"}
    )
    token = login_resp.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["email"] == "employee@enterprise.local"
    assert user_data["role"] == "EMPLOYEE"
    assert user_data["is_active"] is True


def test_get_me_unauthorized():
    """Test that calling /me without authorization header returns HTTP 401."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_refresh_token_success():
    """Test exchanging a valid refresh token for a new token pair."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"username_or_email": "admin@enterprise.local", "password": "Admin@123456"}
    )
    refresh_token = login_resp.json()["refresh_token"]

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "admin@enterprise.local"


def test_refresh_token_invalid():
    """Test that an invalid or forged refresh token returns HTTP 401."""
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "forged_invalid_refresh_token_string"}
    )
    assert response.status_code == 401


def test_logout():
    """Test calling logout endpoint with valid token."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"username_or_email": "admin@enterprise.local", "password": "Admin@123456"}
    )
    token = login_resp.json()["access_token"]

    response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
