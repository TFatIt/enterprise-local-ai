"""ChromaDB Vector Store management for embedding storage and similarity search."""

import os
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import settings

logger = logging.getLogger(__name__)


class ChromaVectorStore:
    """Manages persistent ChromaDB vector collections for enterprise document chunks."""

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None
    ):
        self.persist_directory = os.path.abspath(persist_directory or settings.CHROMA_PERSIST_DIRECTORY)
        self.collection_name = collection_name or settings.CHROMA_COLLECTION_NAME
        os.makedirs(self.persist_directory, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}  # Cosine distance metric
        )

    def add_chunks(
        self,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]]
    ) -> None:
        """Insert or update chunks with vector embeddings into ChromaDB."""
        if not chunks or not embeddings:
            return

        ids = [c["chroma_id"] for c in chunks]
        documents = [c["content"] for c in chunks]
        metadatas = []

        for c in chunks:
            raw_meta = c.get("metadata", {})
            # Chroma requires metadata values to be str, int, float, or bool
            safe_meta = {}
            for k, v in raw_meta.items():
                if v is None:
                    continue
                if isinstance(v, (str, int, float, bool)):
                    safe_meta[k] = v
                else:
                    safe_meta[k] = str(v)
            metadatas.append(safe_meta)

        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        logger.info(f"Upserted {len(ids)} chunks into Chroma collection '{self.collection_name}'")

    def delete_document(self, document_id: str) -> None:
        """Remove all chunks associated with a document from Chroma collection."""
        try:
            self.collection.delete(where={"document_id": str(document_id)})
            logger.info(f"Deleted vector chunks for document {document_id}")
        except Exception as e:
            logger.warning(f"Error deleting Chroma chunks for document {document_id}: {e}")

    def is_chunk_accessible(self, meta: Dict[str, Any], user: Optional[Any], user_dept_id: Optional[int] = None) -> bool:
        """Check if retrieved chunk is strictly accessible by user according to Enterprise ACL."""
        if user is None:
            # Fallback for callers passing department_id directly
            if user_dept_id is not None and user_dept_id > 0:
                chunk_dept = int(meta.get("department_id", 0))
                sec = str(meta.get("security_level", "DEPARTMENT")).upper()
                if sec == "PUBLIC":
                    return True
                if sec == "CONFIDENTIAL":
                    return False
                return chunk_dept == 0 or chunk_dept == user_dept_id
            return True

        role_code = getattr(user.role, "code", "EMPLOYEE") if hasattr(user, "role") and user.role else "EMPLOYEE"
        if role_code in ("SUPER_ADMIN", "ADMIN", "IT_ADMIN"):
            return True

        sec = str(meta.get("security_level", "DEPARTMENT")).upper()
        chunk_dept = int(meta.get("department_id", 0))
        allowed_users = str(meta.get("allowed_users", "")).split(",")
        allowed_roles = str(meta.get("allowed_roles", "")).split(",")

        # Check explicit permissions
        user_id_str = str(getattr(user, "id", ""))
        if user_id_str and user_id_str in allowed_users:
            return True
        if role_code in allowed_roles:
            return True

        # Confidential chunks require explicit grant
        if sec == "CONFIDENTIAL":
            return False

        if sec == "PUBLIC":
            return True

        if sec == "INTERNAL":
            return role_code != "VIEWER"

        if sec == "DEPARTMENT":
            if role_code == "MANAGER":
                return True
            curr_dept = getattr(user, "department_id", None)
            return bool(curr_dept and curr_dept == chunk_dept)

        return False

    def similarity_search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        department_id: Optional[int] = None,
        user: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        """Perform Cosine similarity search with Enterprise Permission & Department ACL."""
        count = self.collection.count()
        if count == 0:
            return []

        actual_k = min(top_k, count)
        # Fetch generous candidate pool to allow strict ACL filtering and deduplication
        query_k = min(max(actual_k * 10, 100), count)

        try:
            results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=query_k,
                include=["documents", "metadatas", "distances"]
            )
        except Exception as e:
            logger.warning(f"Chroma query failed: {e}")
            return []

        matched_chunks = []
        seen_texts = set()
        doc_counts = {}
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for doc_text, meta, dist in zip(docs, metas, distances):
            # Enforce Enterprise Access Control
            if not self.is_chunk_accessible(meta, user=user, user_dept_id=department_id):
                continue

            # If department_id was explicitly requested (e.g. via UI filter), filter by it
            if department_id is not None and department_id > 0:
                chunk_dept = int(meta.get("department_id", 0))
                if chunk_dept != 0 and chunk_dept != department_id:
                    continue

            # Deduplication
            normalized_key = doc_text.strip()
            if normalized_key in seen_texts:
                continue
            seen_texts.add(normalized_key)

            # Document diversity: Allow up to 4 chunks (or top_k // 2) from the same document in top_k
            max_per_doc = max(4, top_k // 2)
            doc_key = str(meta.get("document_id") or meta.get("title", ""))
            if doc_key and doc_counts.get(doc_key, 0) >= max_per_doc:
                continue
            doc_counts[doc_key] = doc_counts.get(doc_key, 0) + 1

            # Cosine distance: similarity = 1 - distance
            similarity = max(0.0, min(1.0, 1.0 - dist))
            matched_chunks.append({
                "content": doc_text,
                "metadata": meta,
                "similarity_score": similarity,
                "distance": dist,
            })
            if len(matched_chunks) >= top_k:
                break

        return matched_chunks


vector_store = ChromaVectorStore()
