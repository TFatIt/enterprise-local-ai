"""Native Python implementation of BM25Okapi and Reciprocal Rank Fusion (RRF).

Provides sparse keyword search to complement dense vector embeddings in Hybrid RAG.
Optimized for technical keywords, error codes, IP addresses, ports, and Vietnamese terms.
"""

import re
import math
from typing import List, Dict, Any, Tuple


class BM25Index:
    """In-memory BM25Okapi index for technical keyword retrieval."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus: List[Dict[str, Any]] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_len: float = 0.0
        self.doc_freqs: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.term_freqs: List[Dict[str, int]] = []

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """Tokenize text into lowercase alphanumeric words, IPs, and technical terms."""
        raw_tokens = re.findall(r"[a-zA-Z0-9_\.\-]+", text.lower())
        cleaned = []
        for t in raw_tokens:
            stripped = t.strip(".,_-")
            if stripped:
                cleaned.append(stripped)
        return cleaned

    def fit(self, documents: List[Dict[str, Any]]) -> None:
        """Fit index with document chunks."""
        self.corpus = documents
        N = len(documents)
        if N == 0:
            return

        self.doc_lengths = []
        self.term_freqs = []
        self.doc_freqs = {}

        total_len = 0
        for doc in documents:
            text = doc.get("content", "")
            tokens = self.tokenize(text)
            doc_len = len(tokens)
            self.doc_lengths.append(doc_len)
            total_len += doc_len

            tf: Dict[str, int] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            self.term_freqs.append(tf)

            for t in tf.keys():
                self.doc_freqs[t] = self.doc_freqs.get(t, 0) + 1

        self.avg_doc_len = total_len / N if N > 0 else 0.0

        # Precompute IDF
        self.idf = {}
        for term, freq in self.doc_freqs.items():
            # BM25 standard IDF with smoothing
            self.idf[term] = math.log((N - freq + 0.5) / (freq + 0.5) + 1.0)

    def search(self, query: str, top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        """Search the indexed corpus using BM25 scoring."""
        N = len(self.corpus)
        if N == 0:
            return []

        query_tokens = self.tokenize(query)
        if not query_tokens:
            return []

        scores: List[float] = [0.0] * N

        for q in query_tokens:
            if q not in self.idf:
                continue
            q_idf = self.idf[q]

            for doc_idx, tf in enumerate(self.term_freqs):
                doc_tf = tf.get(q, 0)
                if doc_tf == 0:
                    continue

                dl = self.doc_lengths[doc_idx]
                denom = doc_tf + self.k1 * (1.0 - self.b + self.b * (dl / (self.avg_doc_len or 1.0)))
                scores[doc_idx] += q_idf * (doc_tf * (self.k1 + 1.0)) / denom

        ranked_indices = sorted(range(N), key=lambda i: scores[i], reverse=True)
        results = []
        for idx in ranked_indices[:top_k]:
            if scores[idx] > 0.0:
                results.append((self.corpus[idx], scores[idx]))

        return results


def reciprocal_rank_fusion(
    dense_results: List[Dict[str, Any]],
    sparse_results: List[Dict[str, Any]],
    k: int = 60
) -> List[Dict[str, Any]]:
    """Fuse dense vector results and sparse BM25 results using Reciprocal Rank Fusion (RRF).

    RRF_score(d) = 1 / (k + rank_dense(d)) + 1 / (k + rank_sparse(d))
    """
    scores: Dict[str, float] = {}
    doc_lookup: Dict[str, Dict[str, Any]] = {}

    # 1. Score dense results
    for rank, doc in enumerate(dense_results, start=1):
        doc_id = doc.get("chroma_id") or doc.get("content", "")[:100]
        doc_lookup[doc_id] = doc
        scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (k + rank))

    # 2. Score sparse results
    for rank, doc in enumerate(sparse_results, start=1):
        doc_id = doc.get("chroma_id") or doc.get("content", "")[:100]
        if doc_id not in doc_lookup:
            doc_lookup[doc_id] = doc
        scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (k + rank))

    # 3. Sort by fused RRF score descending
    sorted_ids = sorted(scores.keys(), key=lambda did: scores[did], reverse=True)

    fused_results = []
    for did in sorted_ids:
        item = dict(doc_lookup[did])
        item["rrf_score"] = round(scores[did], 5)
        fused_results.append(item)

    return fused_results
