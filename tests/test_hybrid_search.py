"""Tests for BM25 Keyword Search and Hybrid Search (Dense + Sparse RRF)."""

import os
import sys
import pytest

# Add backend to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.rag.bm25 import BM25Index, reciprocal_rank_fusion


def test_bm25_exact_technical_keyword_matching():
    documents = [
        {
            "chroma_id": "doc_1",
            "content": "Chính sách bảo mật mật khẩu yêu cầu tối thiểu 8 ký tự và đổi định kỳ mỗi 90 ngày.",
            "metadata": {"title": "Chính sách Mật khẩu"}
        },
        {
            "chroma_id": "doc_2",
            "content": "Để cấu hình mạng VPN, sử dụng OpenVPN hoặc WireGuard tới địa chỉ vpn.enterprise.local cổng 1194 UDP.",
            "metadata": {"title": "Hướng dẫn VPN"}
        },
        {
            "chroma_id": "doc_3",
            "content": "Địa chỉ IP máy chủ Active Directory DNS Controller là 192.168.1.10.",
            "metadata": {"title": "Cấu hình DNS"}
        },
        {
            "chroma_id": "doc_4",
            "content": "Máy in phòng ban tầng 3 là HP LaserJet Pro, địa chỉ IP tĩnh là 192.168.1.50.",
            "metadata": {"title": "Cài đặt Máy in"}
        },
    ]

    index = BM25Index()
    index.fit(documents)

    # 1. Test searching by exact IP
    results = index.search("192.168.1.50", top_k=2)
    assert len(results) > 0
    top_doc, top_score = results[0]
    assert top_doc["chroma_id"] == "doc_4"
    assert "192.168.1.50" in top_doc["content"]

    # 2. Test searching by port number
    results_port = index.search("1194 UDP", top_k=2)
    assert len(results_port) > 0
    assert results_port[0][0]["chroma_id"] == "doc_2"


def test_reciprocal_rank_fusion_scoring():
    dense_results = [
        {"chroma_id": "doc_A", "content": "Tài liệu A", "similarity_score": 0.85},
        {"chroma_id": "doc_B", "content": "Tài liệu B", "similarity_score": 0.70},
    ]
    sparse_results = [
        {"chroma_id": "doc_B", "content": "Tài liệu B", "bm25_score": 4.5},
        {"chroma_id": "doc_C", "content": "Tài liệu C", "bm25_score": 2.1},
    ]

    fused = reciprocal_rank_fusion(dense_results, sparse_results, k=60)
    assert len(fused) == 3
    # Doc B appeared in both Dense (rank 2) and Sparse (rank 1), so it should have highest fused score!
    # Score B = 1/(60+2) + 1/(60+1) = 0.0161 + 0.01639 = 0.0325
    # Score A = 1/(60+1) = 0.01639
    assert fused[0]["chroma_id"] == "doc_B"
    assert fused[0]["rrf_score"] > fused[1]["rrf_score"]
