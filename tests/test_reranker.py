"""Unit tests for Phase 3: Local Cross-Encoder Reranker (FlashRank)."""

import os
import sys
import pytest

# Add backend to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.rag.reranker import reranker, LocalReranker


def test_reranker_initialization_and_metadata():
    """Verify that LocalReranker initializes successfully with local ONNX model."""
    assert reranker is not None
    assert reranker.model_name == "ms-marco-TinyBERT-L-2-v2"


def test_reranker_ordering_accuracy():
    """Verify that Cross-Encoder accurately promotes semantic match over keyword noise."""
    query = "Hướng dẫn cài đặt và địa chỉ IP máy in tầng 3 là gì?"

    chunks = [
        {
            "content": "Chính sách quản lý mật khẩu nhân viên: tối thiểu 8 ký tự và thay đổi mỗi 90 ngày.",
            "similarity_score": 0.65,
            "metadata": {"title": "Chính sách mật khẩu", "file_name": "password.txt", "page_number": 1}
        },
        {
            "content": "Cài đặt máy in: Văn phòng tầng 3 sử dụng máy in HP LaserJet Pro, địa chỉ IP 192.168.1.50. Cổng kết nối TCP 9100.",
            "similarity_score": 0.62,
            "metadata": {"title": "Hướng dẫn máy in", "file_name": "printer.txt", "page_number": 1}
        },
        {
            "content": "Quy trình xin nghỉ phép năm và chế độ thai sản, bảo hiểm xã hội dành cho người lao động.",
            "similarity_score": 0.58,
            "metadata": {"title": "Quy chế nhân sự", "file_name": "hr_policy.txt", "page_number": 1}
        }
    ]

    results = reranker.rerank(query=query, chunks=chunks, top_n=2)
    assert len(results) == 2

    # Top result must be the printer chunk!
    top_hit = results[0]
    assert "máy in" in top_hit["content"].lower()
    assert "192.168.1.50" in top_hit["content"]
    assert "rerank_score" in top_hit
    assert isinstance(top_hit["rerank_score"], float)


def test_reranker_empty_and_single_edge_cases():
    """Verify graceful handling for empty, single-item or malformed inputs."""
    assert reranker.rerank("bất kỳ câu hỏi nào", []) == []

    single = [{"content": "Chỉ có một đoạn duy nhất", "similarity_score": 0.7}]
    res = reranker.rerank("câu hỏi", single, top_n=5)
    assert len(res) == 1
    assert res[0]["content"] == "Chỉ có một đoạn duy nhất"
