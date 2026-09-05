"""Integration tests for Phase 7, 8, & 9: Embeddings, ChromaDB, and Core RAG Pipeline."""

import sys
import os
import pytest

# Add backend to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.rag.embeddings import embeddings_client
from app.rag.vectorstore import vector_store
from app.rag.llm import llm_client
from app.rag.pipeline import rag_pipeline


def test_ollama_embeddings_generation():
    """Verify that nomic-embed-text generates 768-dimensional dense vector."""
    vec = embeddings_client.embed_query("Hướng dẫn kết nối mạng nội bộ và Active Directory")
    assert isinstance(vec, list)
    assert len(vec) == 768
    assert all(isinstance(x, float) for x in vec[:10])


def test_chroma_vectorstore_lifecycle():
    """Verify adding vectors to ChromaDB and similarity searching."""
    doc_id = "test_doc_sample_123"

    sample_chunks = [
        {
            "chroma_id": "test_chunk_1",
            "content": "Máy tính không gia nhập được domain do DNS Server chưa trỏ về Domain Controller 192.168.1.10.",
            "metadata": {
                "document_id": doc_id,
                "title": "Huong dan Active Directory",
                "page_number": 2,
                "department_id": 1
            }
        },
        {
            "chroma_id": "test_chunk_2",
            "content": "Máy in văn phòng tầng 3 là dòng HP LaserJet Pro IP 192.168.1.50 khay nạp giấy 2.",
            "metadata": {
                "document_id": doc_id,
                "title": "Huong dan May in",
                "page_number": 4,
                "department_id": 1
            }
        }
    ]

    # Generate embeddings
    embeddings = embeddings_client.embed_documents([c["content"] for c in sample_chunks])
    assert len(embeddings) == 2

    # Add to Chroma
    vector_store.add_chunks(sample_chunks, embeddings)

    # Search for Domain question
    query_vec = embeddings_client.embed_query("Domain Controller IP va DNS")
    results = vector_store.similarity_search(query_vec, top_k=2)

    assert len(results) >= 1
    top_hit = results[0]
    assert "Domain" in top_hit["content"]
    assert top_hit["similarity_score"] > 0.60

    # Cleanup
    vector_store.delete_document(doc_id)


def test_local_llm_inference():
    """Verify local Qwen LLM can generate completions."""
    result = llm_client.generate(
        prompt="Trả lời ngắn gọn trong 1 câu: DNS là viết tắt của từ gì?",
        system_prompt="Bạn là trợ lý kỹ thuật."
    )
    assert "Domain Name System" in result["response"] or "hệ thống phân giải" in result["response"].lower()
    assert result["eval_count"] > 0


def test_rag_pipeline_relevant_question():
    """Verify end-to-end RAG question answering with citation sources."""
    # Seed a known chunk into Chroma for testing
    doc_id = "rag_test_doc_ad"
    chunks = [
        {
            "chroma_id": "rag_chunk_dns_ad",
            "content": "Để máy tính gia nhập miền enterprise.local, DNS Server bắt buộc phải trỏ về IP 192.168.1.10. Giờ hệ thống không được lệch quá 5 phút.",
            "metadata": {
                "document_id": doc_id,
                "title": "Quy định Active Directory",
                "file_name": "ad_policy.txt",
                "page_number": 1,
                "department_id": 1
            }
        }
    ]
    embeddings = embeddings_client.embed_documents([c["content"] for c in chunks])
    vector_store.add_chunks(chunks, embeddings)

    # Ask relevant question
    res = rag_pipeline.ask(
        question="Tại sao máy tính không join domain được và cần cấu hình DNS thế nào?",
        top_k=2
    )

    assert res["suggest_ticket"] is False
    assert len(res["sources"]) >= 1
    assert any("192.168.1.10" in s["snippet"] or "domain" in s["snippet"].lower() for s in res["sources"])
    assert len(res["answer"]) > 10

    # Clean up
    vector_store.delete_document(doc_id)


def test_rag_pipeline_out_of_context_fallback():
    """Verify that asking completely unrelated question triggers fallback and suggest_ticket."""
    res = rag_pipeline.ask(
        question="Hướng dẫn công thức làm bánh pizza phô mai truyền thống của Ý?",
        top_k=2
    )

    # Must detect low similarity and suggest IT ticket
    assert res["suggest_ticket"] is True
    assert "Không tìm thấy thông tin" in res["answer"]
    assert len(res["sources"]) == 0
