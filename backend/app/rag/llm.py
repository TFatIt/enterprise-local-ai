"""Local LLM Client for Ollama Qwen inference."""

import logging
from typing import Optional, Dict, Any
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class OllamaLLM:
    """Interfaces with local Ollama runtime to generate contextual completions."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.1,
        top_p: float = 0.9,
        num_ctx: int = 4096,
        timeout: float = 120.0
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model_name = model_name or settings.OLLAMA_LLM_MODEL
        self.temperature = temperature
        self.top_p = top_p
        self.num_ctx = num_ctx
        self.timeout = timeout

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate response from local Qwen model."""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "system": system_prompt or "",
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "top_p": self.top_p,
                "num_ctx": self.num_ctx,
            }
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                return {
                    "response": data.get("response", "").strip(),
                    "total_duration_ms": int(data.get("total_duration", 0) / 1_000_000),
                    "eval_count": data.get("eval_count", 0),
                    "eval_duration_ms": int(data.get("eval_duration", 0) / 1_000_000),
                }
        except Exception as e:
            logger.error(f"Error during Ollama LLM inference: {str(e)}")
            raise e

    def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ):
        """Generate response token-by-token from local Qwen model via stream."""
        import json
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "system": system_prompt or "",
            "stream": True,
            "options": {
                "temperature": self.temperature,
                "top_p": self.top_p,
                "num_ctx": self.num_ctx,
            }
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if line:
                            data = json.loads(line)
                            token = data.get("response", "")
                            yield token
                            if data.get("done", False):
                                break
        except Exception as e:
            logger.error(f"Error during Ollama LLM stream inference: {str(e)}")
            raise e


llm_client = OllamaLLM()
