"""Multi-turn Conversation Memory & Context Reformulation for Enterprise Assistant.

Maintains sliding window of chat turns and reformulates follow-up queries
for standalone vector retrieval while preserving natural multi-turn context.
"""

import logging
import re
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Patterns indicating contextual follow-up query requiring previous turn references
FOLLOW_UP_PATTERNS = [
    r"^(còn|thế còn|vậy còn)\b",
    r"\b(nó|cái đó|vấn đề này|lỗi này|trên|ở đâu|như thế nào)\b",
    r"^(làm sao|cách nào|hướng dẫn tiếp|bước tiếp theo)\b",
    r"^(cho tôi hỏi thêm|chi tiết hơn|giải thích thêm)\b",
    r"^(tại sao|sao lại thế|nguyên nhân là gì)\b",
]

FOLLOW_UP_REGEX = re.compile("|".join(FOLLOW_UP_PATTERNS), re.IGNORECASE)


class ConversationMemory:
    """Manages short-term multi-turn conversation window and query contextualization."""

    @staticmethod
    def get_recent_history(
        messages: List[Any],
        max_messages: int = 6
    ) -> List[Dict[str, str]]:
        """Extract the last N valid conversation turns formatted as role/content dicts.
        
        Args:
            messages: List of ChatMessage DB or schema objects.
            max_messages: Maximum individual messages to include (e.g. 6 = 3 turns).
            
        Returns:
            List of {"role": "user"|"assistant", "content": str}
        """
        if not messages:
            return []

        # Sort or slice to get the most recent messages
        recent = messages[-max_messages:]
        formatted_history = []

        for msg in recent:
            role = "user" if getattr(msg, "sender_type", "").upper() == "USER" else "assistant"
            content = getattr(msg, "content", "").strip()
            if content:
                formatted_history.append({"role": role, "content": content})

        return formatted_history

    @staticmethod
    def format_history_for_prompt(
        history: List[Dict[str, str]],
        max_turns: int = 4
    ) -> str:
        """Format history list into a clean text block for inclusion in system/user prompts.
        
        Args:
            history: List of {"role": str, "content": str}
            max_turns: Max turns to include in prompt
            
        Returns:
            Formatted string representation of history
        """
        if not history:
            return ""

        sliced = history[-max_turns * 2:]
        lines = []
        for item in sliced:
            prefix = "Nhân viên" if item["role"] == "user" else "Trợ lý AI"
            # Truncate very long previous responses to keep context window clean
            content = item["content"]
            if len(content) > 400:
                content = content[:397] + "..."
            lines.append(f"{prefix}: {content}")

        return "\n".join(lines)

    @classmethod
    def is_follow_up(cls, query: str) -> bool:
        """Check if query is likely a follow-up referencing prior conversation turns."""
        cleaned = query.strip()
        if len(cleaned.split()) <= 4:
            return True
        return bool(FOLLOW_UP_REGEX.search(cleaned))

    @classmethod
    def reformulate_query(
        cls,
        current_query: str,
        history: List[Dict[str, str]],
        llm_client: Optional[Any] = None
    ) -> str:
        """Reformulate a follow-up question into a standalone search query.
        
        If no history or not a follow-up, returns original query immediately.
        If history exists and query is ambiguous, combines context to optimize vector retrieval.
        """
        cleaned = current_query.strip()
        if not history or not cls.is_follow_up(cleaned):
            return cleaned

        # Find the last user question to capture subject context
        last_user_msg = ""
        for item in reversed(history):
            if item["role"] == "user":
                last_user_msg = item["content"]
                break

        if not last_user_msg:
            return cleaned

        # Fast heuristic combining when LLM reformulation is unnecessary
        # Example: "còn trên macos?" after "cách cấu hình vpn fortinet" -> "cách cấu hình vpn fortinet trên macos"
        if re.search(r"^(còn|thế còn|vậy còn)\b", cleaned, re.IGNORECASE):
            sub_query = re.sub(r"^(còn|thế còn|vậy còn)\s*", "", cleaned, flags=re.IGNORECASE)
            # Remove greeting from previous if any
            clean_prev = re.sub(r"^(xin chào|chào bạn|cho tôi hỏi)\s*", "", last_user_msg, flags=re.IGNORECASE).strip()
            return f"{clean_prev} {sub_query}".strip()

        # If question is extremely brief like "ở đâu?", "như thế nào?", append previous topic
        if len(cleaned.split()) <= 4 and last_user_msg:
            return f"{last_user_msg} {cleaned}".strip()

        return cleaned


conversation_memory = ConversationMemory()
