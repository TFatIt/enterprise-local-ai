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

    def similarity_search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        department_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Perform Cosine similarity search and compute similarity scores."""
        count = self.collection.count()
        if count == 0:
            return []

        actual_k = min(top_k, count)
        where_filter = None
        if department_id is not None and department_id > 0:
            where_filter = {
                "$or": [
                    {"department_id": 0},
                    {"department_id": department_id}
                ]
            }

        # Query more candidates to allow deduplication of identical text chunks
        query_k = min(actual_k * 3, count)

        try:
            results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=query_k,
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )
        except Exception as e:
            logger.warning(f"Chroma query with filter failed, retrying without filter: {e}")
            results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=query_k,
                include=["documents", "metadatas", "distances"]
            )

        matched_chunks = []
        seen_texts = set()
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for doc_text, meta, dist in zip(docs, metas, distances):
            # Enforce department ACL: if department_id specified, exclude other department chunks
            chunk_dept = meta.get("department_id", 0)
            if department_id is not None and department_id > 0:
                if chunk_dept != 0 and chunk_dept != department_id:
                    continue

            # Normalize text for deduplication
            normalized_key = doc_text.strip()
            if normalized_key in seen_texts:
                continue
            seen_texts.add(normalized_key)

            # For cosine distance: distance = 1 - similarity => similarity = 1 - distance
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
