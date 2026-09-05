"""Unit tests for PII Data Masker & Enterprise Redaction Module."""

import sys
import os
import pytest

# Add backend to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.rag.pii_masker import pii_masker


def test_mask_cccd_12_digits():
    """Verify Vietnamese CCCD (12 digits) is masked while preserving last 3 digits."""
    text = "Nhân viên Nguyễn Văn A có số CCCD là 001201012345 công tác tại phòng IT."
    masked = pii_masker.mask_cccd(text)
    assert "001201012345" not in masked
    assert "[CCCD: *********345]" in masked
    assert "Nguyễn Văn A" in masked


def test_mask_bank_card_16_digits():
    """Verify 16-digit credit/ATM card numbers with spaces or dashes are masked."""
    text1 = "Số tài khoản thẻ Visa: 4111-2222-3333-4444 vui lòng thanh toán."
    masked1 = pii_masker.mask_card(text1)
    assert "4111-2222-3333-4444" not in masked1
    assert "[THẺ: ****-****-****-4444]" in masked1

    text2 = "Thẻ ngân hàng: 9704 1234 5678 9012"
    masked2 = pii_masker.mask_card(text2)
    assert "9704 1234 5678 9012" not in masked2
    assert "[THẺ: ****-****-****-9012]" in masked2


def test_mask_vietnamese_phone_number():
    """Verify Vietnamese mobile phone numbers (10 digits) are masked."""
    text = "Liên hệ quản trị viên qua số điện thoại 0987654321 hoặc 0398765432 để hỗ trợ."
    masked = pii_masker.mask_phone(text)
    assert "0987654321" not in masked
    assert "0398765432" not in masked
    assert "[SĐT: *******321]" in masked
    assert "[SĐT: *******432]" in masked


def test_mask_internal_secrets_and_passwords():
    """Verify configuration passwords and secret tokens are redacted."""
    text = 'Cấu hình database: password = "DatabaseMasterPass2026!" và api_key: "sk-live-abcdef123456"'
    masked = pii_masker.mask_secrets(text)
    assert "DatabaseMasterPass2026!" not in masked
    assert "sk-live-abcdef123456" not in masked
    assert "[BẢO MẬT: ĐÃ ẨN SECRET]" in masked


def test_full_pipeline_mask_and_audit():
    """Verify full mask_pii and audit_pii functions."""
    combined = (
        "Hồ sơ nhân viên: Nguyễn Thị B, SĐT: 0912345678, CCCD: 079198001234, "
        "Số thẻ: 4242-4242-4242-1234, Mật khẩu: password = SecretPassWord999"
    )
    audit = pii_masker.audit_pii(combined)
    assert audit["has_pii"] is True
    assert audit["total"] >= 4
    assert audit["details"]["bank_cards"] >= 1
    assert audit["details"]["cccd_identities"] >= 1
    assert audit["details"]["phone_numbers"] >= 1
    assert audit["details"]["secrets_or_passwords"] >= 1

    clean_text = pii_masker.mask_pii(combined)
    assert "0912345678" not in clean_text
    assert "079198001234" not in clean_text
    assert "4242-4242-4242-1234" not in clean_text
    assert "SecretPassWord999" not in clean_text
    assert "[SĐT: *******678]" in clean_text
    assert "[CCCD: *********234]" in clean_text
    assert "[THẺ: ****-****-****-1234]" in clean_text
