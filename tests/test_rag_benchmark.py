"""Phase 13: End-to-End RAG Benchmark and Ground-Truth Evaluation Suite.

Evaluates against enterprise IT policy (sample_it_policy.txt):
1. VPN Connection Guidance (OpenVPN/WireGuard, vpn.enterprise.local)
2. Password Security Policy (8 chars, 90 days rotation)
3. Active Directory Domain Join & DNS Server (192.168.1.10)
4. Office Printer Setup (HP LaserJet, 192.168.1.50)
5. Out-of-Domain Hallucination Prevention (Strict refusal & IT Ticket suggestion)
"""

import sys
import os
import time
import pytest

# Add backend to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.rag.embeddings import embeddings_client
from app.rag.vectorstore import vector_store
from app.rag.chunker import RecursiveCharacterChunker
from app.rag.pipeline import rag_pipeline


@pytest.fixture(scope="module", autouse=True)
def seed_benchmark_knowledge_base():
    """Index sample enterprise IT policy into ChromaDB for benchmark evaluation."""
    sample_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "documents", "sample_it_policy.txt"))
    with open(sample_file, "r", encoding="utf-8") as f:
        text = f.read()

    chunker = RecursiveCharacterChunker(chunk_size=700, chunk_overlap=120)
    doc_id = "benchmark-doc-policy-2026"

    raw_chunks = chunker.chunk_document(
        pages=[{"page": 1, "text": text}],
        document_metadata={
            "document_id": doc_id,
            "title": "Chính sách và Hướng dẫn CNTT Nội bộ Doanh nghiệp 2026",
            "file_name": "sample_it_policy.txt",
            "department_id": 1,
        }
    )

    vector_store.delete_document(doc_id)

    formatted_chunks = []
    for i, c in enumerate(raw_chunks):
        formatted_chunks.append({
            "chroma_id": f"{doc_id}_chunk_{i}",
            "content": c["content"],
            "metadata": c["metadata"]
        })

    texts = [c["content"] for c in formatted_chunks]
    embeddings = embeddings_client.embed_documents(texts)
    vector_store.add_chunks(formatted_chunks, embeddings)

    yield

    vector_store.delete_document(doc_id)


def test_benchmark_vpn_retrieval_and_answer():
    """Benchmark Query 1: Remote VPN Setup (Chapter 3)."""
    question = "Làm thế nào để kết nối mạng VPN làm việc từ xa của công ty?"
    start = time.time()
    result = rag_pipeline.ask(question)
    latency_ms = int((time.time() - start) * 1000)

    answer = result["answer"].lower()
    sources = result["sources"]

    # Retrieval accuracy
    assert len(sources) > 0, "Retrieval Hit Rate failure: No relevant chunks found"
    assert sources[0]["similarity_score"] >= 0.55

    # Factuality check: must contain OpenVPN/WireGuard and gateway
    assert "openvpn" in answer or "wireguard" in answer or "vpn" in answer
    assert "vpn.enterprise.local" in answer

    # No hallucination
    assert result["suggest_ticket"] is False


def test_benchmark_password_policy_retrieval_and_answer():
    """Benchmark Query 2: Enterprise Password Security Policy (Chapter 1)."""
    question = "Mật khẩu máy tính doanh nghiệp quy định tối thiểu bao nhiêu ký tự và bao lâu phải đổi một lần?"
    result = rag_pipeline.ask(question)
    answer = result["answer"].lower()
    sources = result["sources"]

    # Retrieval accuracy
    assert len(sources) > 0
    # Must retrieve 8 characters and 90 days from Chapter 1
    assert "8" in answer, "LLM failed to retrieve 8 characters minimum rule"
    assert "90" in answer, "LLM failed to retrieve 90 days rotation rule"
    assert result["suggest_ticket"] is False


def test_benchmark_active_directory_domain_dns():
    """Benchmark Query 3: Active Directory Domain & DNS Server (Chapter 2)."""
    question = "Để máy tính gia nhập miền Active Directory enterprise.local thì DNS Server phải trỏ về địa chỉ IP nào?"
    result = rag_pipeline.ask(question)
    answer = result["answer"].lower()
    sources = result["sources"]

    assert len(sources) > 0
    assert "192.168.1.10" in answer or "domain controller" in answer
    assert result["suggest_ticket"] is False


def test_benchmark_printer_setup():
    """Benchmark Query 4: Office Printer Setup (Chapter 4)."""
    question = "Địa chỉ IP và dòng máy in văn phòng đặt tại Tầng 3 là gì?"
    result = rag_pipeline.ask(question)
    answer = result["answer"].lower()
    sources = result["sources"]

    assert len(sources) > 0
    assert "192.168.1.50" in answer
    assert "hp" in answer or "laserjet" in answer
    assert result["suggest_ticket"] is False


def test_benchmark_out_of_domain_hallucination_prevention():
    """Benchmark Query 5: Out-of-Domain Query should be strictly refused."""
    question = "Hướng dẫn chi tiết công thức làm bánh pizza hải sản phô mai ngon nhất tại nhà?"
    result = rag_pipeline.ask(question)

    # Must refuse to answer and suggest ticket
    assert result["suggest_ticket"] is True
    assert len(result["sources"]) == 0
    assert "không tìm thấy thông tin" in result["answer"].lower()
