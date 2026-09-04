"""Tests for Department-Level Document Access Control (ACL) in Vector RAG."""

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
from app.rag.vectorstore import vector_store
from app.rag.embeddings import embeddings_client

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


def test_department_vector_store_isolation():
    # 1. Seed two dummy chunks into ChromaDB:
    # Chunk 1: Company-wide (dept=0)
    # Chunk 2: IT Department only (dept=1)
    chunk_general = {
        "chroma_id": "test_acl_general_chunk_1",
        "content": "Chính sách nghỉ phép năm chung cho toàn bộ nhân viên công ty áp dụng 12 ngày.",
        "metadata": {
            "title": "Chính sách Lao động Chung",
            "department_id": 0,
        }
    }
    chunk_it_confidential = {
        "chroma_id": "test_acl_it_chunk_1",
        "content": "Thông số đăng nhập máy chủ cơ sở dữ liệu nội bộ phòng IT: user root, port 5432.",
        "metadata": {
            "title": "Bảo mật Máy chủ IT",
            "department_id": 1,
        }
    }

    embed_gen = embeddings_client.embed_documents([chunk_general["content"]])[0]
    embed_it = embeddings_client.embed_documents([chunk_it_confidential["content"]])[0]

    vector_store.add_chunks([chunk_general], [embed_gen])
    vector_store.add_chunks([chunk_it_confidential], [embed_it])

    query_it = embeddings_client.embed_query("Mật khẩu máy chủ phòng IT?")

    # Case A: HR Employee (department_id=2) searches for IT confidential info
    hr_results = vector_store.similarity_search(query_it, top_k=5, department_id=2)
    hr_titles = [c.get("metadata", {}).get("title") for c in hr_results]
    assert "Bảo mật Máy chủ IT" not in hr_titles, "HR employee should NOT see IT confidential document"

    # Case B: IT Admin / Super Admin (department_id=None) searches for IT info
    admin_results = vector_store.similarity_search(query_it, top_k=5, department_id=None)
    admin_titles = [c.get("metadata", {}).get("title") for c in admin_results]
    assert "Bảo mật Máy chủ IT" in admin_titles, "IT/Super Admin should see IT confidential document"
