"""Core RAG Pipeline Orchestrator with Two-Tier Grounding Verification."""

import time
import logging
from typing import List, Dict, Any, Optional

from app.core.config import settings
from app.rag.embeddings import embeddings_client
from app.rag.llm import llm_client
from app.rag.vectorstore import vector_store
from app.rag.bm25 import BM25Index, reciprocal_rank_fusion
from app.rag.reranker import reranker
from app.rag.pii_masker import pii_masker

logger = logging.getLogger(__name__)


class RAGPipeline:
    """Orchestrates query vectorization, similarity search, prompt construction, and LLM generation."""

    SYSTEM_PROMPT = (
        "Bạn là Trợ lý AI Nội bộ Doanh nghiệp (Enterprise Local AI Assistant), "
        "hỗ trợ nhân viên tra cứu quy trình và giải quyết sự cố kỹ thuật CNTT.\n\n"
        "NGUYÊN TẮC BẮT BUỘC:\n"
        "1. Trả lời câu hỏi CHỈ DỰA TRÊN ngữ cảnh (CONTEXT) tài liệu nội bộ được cung cấp bên dưới.\n"
        "2. Tuyệt đối KHÔNG tự sáng tạo thông tin ngoài tài liệu nội bộ.\n"
        "3. Trình bày rõ ràng, súc tích bằng Markdown, có các bước hướng dẫn cụ thể (1, 2, 3...).\n"
        "4. Nếu trong tài liệu không có thông tin giải quyết hoặc câu hỏi không liên quan đến tài liệu, "
        "bạn PHẢI trả lời chính xác: 'Không tìm thấy thông tin đầy đủ trong tài liệu nội bộ của doanh nghiệp.'\n"
        "5. Cuối câu trả lời, hãy liệt kê rõ các nguồn trích dẫn [1], [2] bạn đã tham khảo."
    )

    FALLBACK_RESPONSE = (
        "Không tìm thấy thông tin trong phạm vi tài liệu bạn được phép truy cập. "
        "Bạn vui lòng kiểm tra lại từ khóa hoặc bấm nút **Tạo IT Support Ticket** bên dưới "
        "để gửi yêu cầu cho bộ phận chuyên trách hỗ trợ trực tiếp."
    )

    NEGATIVE_INDICATORS = [
        "không có thông tin",
        "không tìm thấy thông tin",
        "không có nội dung",
        "không đề cập",
        "chưa có thông tin",
        "không chứa thông tin",
        "không liên quan",
        "không thể trả lời",
        "không có quyền",
    ]

    @classmethod
    def ask(
        cls,
        question: str,
        department_id: Optional[int] = None,
        top_k: int = 3,
        user: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Execute end-to-end RAG workflow for a user question with permission awareness."""
        start_time = time.time()

        # 1. Embed user query
        query_vector = embeddings_client.embed_query(question)

        # 2. Similarity search in ChromaDB with Enterprise ACL Filtering
        retrieved_chunks = vector_store.similarity_search(
            query_vector=query_vector,
            top_k=max(top_k * 4, 12),
            department_id=department_id,
            user=user
        )

        # 2b. Sparse Keyword Search (BM25) & Reciprocal Rank Fusion (RRF)
        if retrieved_chunks:
            try:
                bm25 = BM25Index()
                bm25.fit(retrieved_chunks)
                sparse_hits = [doc for doc, _ in bm25.search(question, top_k=top_k * 2)]
                if sparse_hits:
                    retrieved_chunks = reciprocal_rank_fusion(
                        dense_results=retrieved_chunks,
                        sparse_results=sparse_hits,
                        k=60
                    )
            except Exception as e:
                logger.warning(f"BM25 hybrid fusion warning: {e}")

        # 3. Tier 1 Gate: Filter by similarity threshold
        candidate_chunks = [
            c for c in retrieved_chunks
            if c.get("similarity_score", 0.0) >= settings.RAG_SIMILARITY_THRESHOLD
        ]

        # Handle Vector-Level Out-Of-Context Fallback
        if not candidate_chunks:
            duration_ms = int((time.time() - start_time) * 1000)
            return {
                "answer": cls.FALLBACK_RESPONSE,
                "sources": [],
                "suggest_ticket": True,
                "response_time_ms": duration_ms,
            }

        # 3.5 Tier 1.5 Gate: Local Cross-Encoder Re-ranking
        relevant_chunks = reranker.rerank(query=question, chunks=candidate_chunks, top_n=top_k)

        # 4. Build Context Prompt
        context_parts = []
        sources = []

        for idx, chunk in enumerate(relevant_chunks, start=1):
            meta = chunk.get("metadata", {})
            title = meta.get("title", meta.get("file_name", "Tài liệu nội bộ"))
            page = meta.get("page_number", 1)
            content = chunk.get("content", "")

            context_parts.append(
                f"[{idx}] Tài liệu: {title} (Trang {page})\n"
                f"Nội dung: {content}"
            )

            sources.append({
                "source_index": idx,
                "document_id": meta.get("document_id"),
                "document_title": title,
                "file_name": meta.get("file_name", ""),
                "page_number": page,
                "similarity_score": round(chunk.get("similarity_score", 0.0), 3),
                "rerank_score": chunk.get("rerank_score"),
                "snippet": content[:500] + ("..." if len(content) > 500 else "")
            })

        context_str = "\n\n---\n\n".join(context_parts)
        sanitized_question = pii_masker.mask_pii(question)
        user_prompt = (
            f"NGỮ CẢNH TÀI LIỆU NỘI BỘ (CONTEXT):\n"
            f"---\n{context_str}\n---\n\n"
            f"CÂU HỎI CỦA NHÂN VIÊN:\n{sanitized_question}\n\n"
            f"CÂU TRẢ LỜI:"
        )

        # 5. Generate answer via Qwen Local LLM
        llm_result = llm_client.generate(
            prompt=user_prompt,
            system_prompt=cls.SYSTEM_PROMPT
        )
        answer_text = llm_result.get("response", "").strip()
        duration_ms = int((time.time() - start_time) * 1000)

        # 6. Tier 2 Gate: Detect if LLM truthfully rejected the context
        ans_lower = answer_text.lower()
        if any(ind in ans_lower for ind in cls.NEGATIVE_INDICATORS):
            logger.info("LLM determined context does not contain answer. Triggering IT Ticket suggestion.")
            return {
                "answer": cls.FALLBACK_RESPONSE,
                "sources": [],
                "suggest_ticket": True,
                "response_time_ms": duration_ms,
            }

        return {
            "answer": answer_text,
            "sources": sources,
            "suggest_ticket": False,
            "response_time_ms": duration_ms,
        }

    @classmethod
    def ask_stream(
        cls,
        question: str,
        department_id: Optional[int] = None,
        top_k: int = 3,
        user: Optional[Any] = None
    ):
        """Execute end-to-end RAG workflow yielding SSE chunks with Enterprise Access Control."""
        import json
        start_time = time.time()

        # 1. Embed user query
        query_vector = embeddings_client.embed_query(question)

        # 2. Similarity search in ChromaDB with Enterprise ACL Filtering
        retrieved_chunks = vector_store.similarity_search(
            query_vector=query_vector,
            top_k=max(top_k * 4, 12),
            department_id=department_id,
            user=user
        )

        # 2b. Sparse Keyword Search (BM25) & Reciprocal Rank Fusion (RRF)
        if retrieved_chunks:
            try:
                bm25 = BM25Index()
                bm25.fit(retrieved_chunks)
                sparse_hits = [doc for doc, _ in bm25.search(question, top_k=top_k * 2)]
                if sparse_hits:
                    retrieved_chunks = reciprocal_rank_fusion(
                        dense_results=retrieved_chunks,
                        sparse_results=sparse_hits,
                        k=60
                    )
            except Exception as e:
                logger.warning(f"BM25 hybrid fusion warning: {e}")

        # 3. Tier 1 Gate: Filter by similarity threshold
        candidate_chunks = [
            c for c in retrieved_chunks
            if c.get("similarity_score", 0.0) >= settings.RAG_SIMILARITY_THRESHOLD
        ]

        if not candidate_chunks:
            duration_ms = int((time.time() - start_time) * 1000)
            yield f"data: {json.dumps({'type': 'metadata', 'sources': [], 'suggest_ticket': True})}\n\n"
            yield f"data: {json.dumps({'type': 'token', 'token': cls.FALLBACK_RESPONSE})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'response_time_ms': duration_ms, 'full_answer': cls.FALLBACK_RESPONSE, 'sources': [], 'suggest_ticket': True})}\n\n"
            return

        # 3.5 Tier 1.5 Gate: Local Cross-Encoder Re-ranking
        relevant_chunks = reranker.rerank(query=question, chunks=candidate_chunks, top_n=top_k)

        # 4. Build Context Prompt
        context_parts = []
        sources = []

        for idx, chunk in enumerate(relevant_chunks, start=1):
            meta = chunk.get("metadata", {})
            title = meta.get("title", meta.get("file_name", "Tài liệu nội bộ"))
            page = meta.get("page_number", 1)
            content = chunk.get("content", "")

            context_parts.append(
                f"[{idx}] Tài liệu: {title} (Trang {page})\n"
                f"Nội dung: {content}"
            )

            sources.append({
                "source_index": idx,
                "document_id": meta.get("document_id"),
                "document_title": title,
                "file_name": meta.get("file_name", ""),
                "page_number": page,
                "similarity_score": round(chunk.get("similarity_score", 0.0), 3),
                "rerank_score": chunk.get("rerank_score"),
                "snippet": content[:500] + ("..." if len(content) > 500 else "")
            })

        context_str = "\n\n---\n\n".join(context_parts)
        sanitized_question = pii_masker.mask_pii(question)
        user_prompt = (
            f"NGỮ CẢNH TÀI LIỆU NỘI BỘ (CONTEXT):\n"
            f"---\n{context_str}\n---\n\n"
            f"CÂU HỎI CỦA NHÂN VIÊN:\n{sanitized_question}\n\n"
            f"CÂU TRẢ LỜI:"
        )

        yield f"data: {json.dumps({'type': 'metadata', 'sources': sources, 'suggest_ticket': False})}\n\n"

        full_answer_acc = []
        try:
            for token in llm_client.generate_stream(prompt=user_prompt, system_prompt=cls.SYSTEM_PROMPT):
                full_answer_acc.append(token)
                yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"
        except Exception as e:
            logger.error(f"Error during LLM stream generation: {e}")
            fallback_err = "\n\n[Hệ thống: Mô hình LLM nội bộ phản hồi quá lâu hoặc đang quá tải. Bạn có thể nhấn 'Tạo IT Ticket' để được hỗ trợ trực tiếp.]"
            full_answer_acc.append(fallback_err)
            yield f"data: {json.dumps({'type': 'token', 'token': fallback_err})}\n\n"

        full_answer = "".join(full_answer_acc).strip()
        duration_ms = int((time.time() - start_time) * 1000)

        ans_lower = full_answer.lower()
        suggest_ticket = any(ind in ans_lower for ind in cls.NEGATIVE_INDICATORS)

        yield f"data: {json.dumps({'type': 'done', 'response_time_ms': duration_ms, 'full_answer': full_answer, 'sources': sources, 'suggest_ticket': suggest_ticket})}\n\n"


rag_pipeline = RAGPipeline()
