"""Tests for AI Auto-Triage endpoint and classification logic."""

import os
import sys
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


def test_ai_auto_triage_network_issue():
    token = get_token("employee@enterprise.local", "Employee@123456")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post(
        "/api/v1/tickets/auto-triage",
        json={
            "title": "Mất kết nối mạng Internet toàn bộ phòng kế toán",
            "description": "Không thể truy cập vào mạng LAN, không ping được default gateway, router báo đèn đỏ."
        },
        headers=headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["suggested_category"] == "NETWORK"
    assert data["suggested_priority"] in ["HIGH", "URGENT", "MEDIUM"]
    assert len(data["reasoning"]) > 5
    assert isinstance(data["suggested_initial_actions"], list)


def test_ai_auto_triage_hardware_issue():
    token = get_token("employee@enterprise.local", "Employee@123456")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post(
        "/api/v1/tickets/auto-triage",
        json={
            "title": "Máy in HP LaserJet tầng 3 bị kẹt giấy",
            "description": "Máy in báo lỗi Paper Jam liên tục, đã mở khay lấy giấy nhưng vẫn báo đèn đỏ."
        },
        headers=headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["suggested_category"] == "HARDWARE"


def test_ai_auto_triage_account_issue():
    token = get_token("employee@enterprise.local", "Employee@123456")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post(
        "/api/v1/tickets/auto-triage",
        json={
            "title": "Bị khóa tài khoản do nhập sai mật khẩu",
            "description": "Tôi bị quên mật khẩu đăng nhập máy tính nội bộ và tài khoản đã bị khóa sau 5 lần nhập sai."
        },
        headers=headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["suggested_category"] == "ACCOUNT"
