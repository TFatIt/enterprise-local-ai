"""PII Data Masking & Sensitive Entity Redaction Module.

Complies with Enterprise Data Protection standards & Vietnam Personal Data Protection Decree (Nghị định 13/2023/NĐ-CP).
Redacts or anonymizes:
1. CCCD / CMND (Vietnamese National Identification Numbers - 12 digits or 9 digits)
2. Bank / Credit Card Numbers (16 digits, with optional spaces or dashes)
3. Vietnamese Personal Phone Numbers (10 digits starting with 03, 05, 07, 08, 09 or +84)
4. Internal Passwords, Secrets, API Keys, and Tokens in configuration context
"""

import re
from typing import Dict, Any, List


# 1. Bank / Credit Cards (16 digits grouped in 4s or contiguous)
CARD_PATTERN = re.compile(r"\b(?:\d{4}[-\s]){3}\d{4}\b|\b(?:4\d{15}|5[1-5]\d{14}|6011\d{12})\b")

# 2. Vietnamese Citizen ID (CCCD - 12 digits, often starting with 0) or legacy CMND (9 digits with context)
CCCD_PATTERN = re.compile(r"\b0\d{11}\b|\b\d{12}\b")
CMND_CONTEXT_PATTERN = re.compile(r"(?i)\b(?:cmnd|cccd|căn\s*cước|chứng\s*minh)\s*[:#\s]?\s*(\d{9,12})\b")

# 3. Vietnamese Mobile Phone Numbers (10 digits starting with 03, 05, 07, 08, 09 or +84)
PHONE_PATTERN = re.compile(r"(?:\+84|0)(?:3[2-9]|5[2|6|8|9]|7[0|6-9]|8[1-9]|9[0-9])\d{7}\b")

# 4. Passwords, Secrets, and API Keys
SECRET_PATTERN = re.compile(
    r"(?i)\b(mật\s*khẩu|password|passwd|pwd|secret_key|api_key|access_token|bearer)\b(?:\s*[:=]\s*(?:password|passwd|pwd)\b)?\s*[:=]\s*['\"]?([^\s'\",;]{3,})['\"]?",
)


class PIIMasker:
    """Enterprise PII Sanitization Engine with context-aware redaction."""

    @classmethod
    def mask_card(cls, text: str) -> str:
        """Mask bank card numbers, preserving only the last 4 digits."""
        def _replace_card(match: re.Match) -> str:
            raw = match.group(0)
            digits = re.sub(r"\D", "", raw)
            last4 = digits[-4:] if len(digits) >= 4 else "XXXX"
            return f"[THẺ: ****-****-****-{last4}]"
        return CARD_PATTERN.sub(_replace_card, text)

    @classmethod
    def mask_cccd(cls, text: str) -> str:
        """Mask CCCD 12-digit IDs, preserving the last 3 digits."""
        def _replace_cccd(match: re.Match) -> str:
            raw = match.group(0)
            digits = re.sub(r"\D", "", raw)
            if len(digits) == 12:
                last3 = digits[-3:]
                return f"[CCCD: *********{last3}]"
            return raw
        
        # First handle explicit context (CMND / CCCD: 123456789)
        def _replace_cmnd_context(match: re.Match) -> str:
            prefix = match.group(0).split(match.group(1))[0]
            digits = match.group(1)
            last3 = digits[-3:] if len(digits) >= 3 else "XXX"
            if len(digits) == 12:
                return f"{prefix}[CCCD: *********{last3}]"
            return f"{prefix}[CMND: ******{last3}]"

        text = CMND_CONTEXT_PATTERN.sub(_replace_cmnd_context, text)
        return CCCD_PATTERN.sub(_replace_cccd, text)

    @classmethod
    def mask_phone(cls, text: str) -> str:
        """Mask Vietnamese phone numbers, preserving the last 3 digits."""
        def _replace_phone(match: re.Match) -> str:
            raw = match.group(0)
            digits = re.sub(r"\D", "", raw)
            last3 = digits[-3:] if len(digits) >= 3 else "XXX"
            return f"[SĐT: *******{last3}]"
        return PHONE_PATTERN.sub(_replace_phone, text)

    @classmethod
    def mask_secrets(cls, text: str) -> str:
        """Redact password values and API keys."""
        def _replace_secret(match: re.Match) -> str:
            key_name = match.group(1)
            return f"{key_name} = [BẢO MẬT: ĐÃ ẨN SECRET]"
        return SECRET_PATTERN.sub(_replace_secret, text)

    @classmethod
    def mask_pii(
        cls,
        text: str,
        mask_cards: bool = True,
        mask_cccd: bool = True,
        mask_phone: bool = True,
        mask_secrets: bool = True
    ) -> str:
        """Run full PII redaction pipeline over text."""
        if not text:
            return ""

        sanitized = text

        if mask_secrets:
            sanitized = cls.mask_secrets(sanitized)

        if mask_cards:
            sanitized = cls.mask_card(sanitized)

        if mask_cccd:
            sanitized = cls.mask_cccd(sanitized)

        if mask_phone:
            sanitized = cls.mask_phone(sanitized)

        return sanitized

    @classmethod
    def audit_pii(cls, text: str) -> Dict[str, Any]:
        """Audit text for PII occurrences and return summary counts without revealing raw PII."""
        if not text:
            return {"total": 0, "details": {}}

        card_matches = len(CARD_PATTERN.findall(text))
        cccd_matches = len(CCCD_PATTERN.findall(text))
        phone_matches = len(PHONE_PATTERN.findall(text))
        secret_matches = len(SECRET_PATTERN.findall(text))

        total = card_matches + cccd_matches + phone_matches + secret_matches

        return {
            "total": total,
            "has_pii": total > 0,
            "details": {
                "bank_cards": card_matches,
                "cccd_identities": cccd_matches,
                "phone_numbers": phone_matches,
                "secrets_or_passwords": secret_matches,
            }
        }

    @classmethod
    def contains_pii(cls, text: str) -> bool:
        """Quick boolean check if text contains any sensitive PII."""
        return cls.audit_pii(text)["has_pii"]


pii_masker = PIIMasker()
