"""Test cases for API health check endpoint."""

import sys
import os

# Add backend directory to sys.path so app can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Verify root endpoint returns HTTP 200 and docs link."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Enterprise Local AI Assistant" in data["message"]


def test_health_check_endpoint():
    """Verify healthcheck endpoint returns healthy status and local AI config."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "healthy"
    assert "local_ai" in data
    assert data["local_ai"]["runtime"] == "Ollama"
    assert "qwen" in data["local_ai"]["llm_model"]
