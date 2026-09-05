"""Local Cross-Encoder Reranker Module using FlashRank (ONNX Runtime).

Provides sub-25ms zero-cloud cross-attention re-ranking over candidate chunks
retrieved via ChromaDB vector similarity and BM25 hybrid search.
"""

import time
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class LocalReranker:
    """Zero-cloud local cross-encoder re-ranking engine powered by FlashRank."""

    def __init__(self, model_name: str = "ms-marco-TinyBERT-L-2-v2"):
        self.model_name = model_name
        self._ranker = None
        self._initialized = False

    def _ensure_initialized(self) -> bool:
        """Lazy initialization of the FlashRank ONNX model."""
        if self._initialized:
            return self._ranker is not None

        try:
            from flashrank import Ranker
            logger.info(f"Initializing local FlashRank reranker model: '{self.model_name}'...")
            start_t = time.time()
            self._ranker = Ranker(model_name=self.model_name, cache_dir="./models_cache")
            duration_ms = int((time.time() - start_t) * 1000)
            logger.info(f"FlashRank reranker loaded successfully in {duration_ms}ms.")
            self._initialized = True
            return True
        except Exception as e:
            logger.warning(f"Failed to initialize FlashRank reranker: {e}. Falling back to Bi-Encoder vector scores.")
            self._initialized = True
            self._ranker = None
            return False

    def rerank(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """Rerank retrieved candidate chunks using deep cross-attention matching.

        Args:
            query: The user search question.
            chunks: Candidate chunks retrieved from VectorStore/BM25 (must already be ACL filtered).
            top_n: Number of top scoring chunks to return.

        Returns:
            List of chunks ordered by rerank relevance score.
        """
        if not chunks:
            return []

        # If only 1 chunk or fewer than top_n, return directly
        if len(chunks) <= 1:
            return chunks[:top_n]

        if not self._ensure_initialized() or self._ranker is None:
            # Graceful fallback: return top_n by existing similarity_score
            return sorted(chunks, key=lambda c: c.get("similarity_score", 0.0), reverse=True)[:top_n]

        try:
            from flashrank import RerankRequest

            start_t = time.time()
            passages = [
                {
                    "id": idx,
                    "text": chunk.get("content", ""),
                    "meta": chunk
                }
                for idx, chunk in enumerate(chunks)
            ]

            request = RerankRequest(query=query, passages=passages)
            results = self._ranker.rerank(request)
            duration_ms = int((time.time() - start_t) * 1000)

            reranked_chunks = []
            for item in results:
                original_chunk = item["meta"]
                score = float(item["score"])
                # Attach rerank score and keep original vector score
                chunk_copy = dict(original_chunk)
                chunk_copy["rerank_score"] = round(score, 4)
                reranked_chunks.append(chunk_copy)

            logger.info(
                f"FlashRank reranked {len(chunks)} candidate chunks down to {min(top_n, len(reranked_chunks))} "
                f"in {duration_ms}ms."
            )
            return reranked_chunks[:top_n]

        except Exception as e:
            logger.warning(f"Error during FlashRank rerank: {e}. Falling back to vector score ranking.")
            return sorted(chunks, key=lambda c: c.get("similarity_score", 0.0), reverse=True)[:top_n]


# Singleton instance
reranker = LocalReranker()
