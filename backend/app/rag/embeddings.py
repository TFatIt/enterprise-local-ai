"""Embedding generator module using local Ollama nomic-embed-text."""

import logging
from typing import List, Optional
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class OllamaEmbeddings:
    """Generates 768-dimensional dense vector embeddings via local Ollama."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: float = 30.0
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model_name = model_name or settings.OLLAMA_EMBED_MODEL
        self.timeout = timeout

    def embed_text(self, text: str) -> List[float]:
        """Generate vector embedding for a single text chunk."""
        if not text or not text.strip():
            return [0.0] * 768

        url = f"{self.base_url}/api/embeddings"
        payload = {
            "model": self.model_name,
            "prompt": text.strip()
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                embedding = data.get("embedding", [])
                if not embedding:
                    raise ValueError(f"Ollama returned empty embedding for model {self.model_name}")
                return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding for text ({e})")
            raise e

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Batch generate embeddings for multiple chunks."""
        embeddings = []
        for text in texts:
            vec = self.embed_text(text)
            embeddings.append(vec)
        return embeddings

    def embed_query(self, query: str) -> List[float]:
        """Generate embedding vector for a user query."""
        return self.embed_text(query)


embeddings_client = OllamaEmbeddings()
