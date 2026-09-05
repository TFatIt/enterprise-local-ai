#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
ENTERPRISE INTENT CLASSIFIER & ROUTING ENGINE
===============================================================================
Hybrid Intent Classifier combining ultra-fast rule-based regex (<1ms) and
domain keyword/semantic scoring. Distinguishes General Chat / Greetings /
Small Talk from Enterprise Knowledge Queries requiring RAG.
"""

import re
from typing import Optional, Dict, Any
from dataclasses import dataclass


class IntentCategory:
    GREETING = "GREETING"
    SMALL_TALK = "SMALL_TALK"
    WRITING_ASSISTANT = "WRITING_ASSISTANT"
    TRANSLATION = "TRANSLATION"
    GENERAL_CHAT = "GENERAL_CHAT"
    IT_HELPDESK = "IT_HELPDESK"
    IT_NETWORK = "IT_NETWORK"
    IT_SYSTEM = "IT_SYSTEM"
    IT_SECURITY = "IT_SECURITY"
    HR = "HR"
    ACCOUNTING = "ACCOUNTING"
    FINANCE = "FINANCE"
    SALES = "SALES"
    PROCUREMENT = "PROCUREMENT"
    LEGAL = "LEGAL"
    QA_QC = "QA_QC"
    PRODUCTION_LOGISTICS = "PRODUCTION_LOGISTICS"
    PLANNING_GENERAL = "PLANNING_GENERAL"
    EMPTY = "EMPTY"


@dataclass
class IntentResult:
    intent: str
    is_enterprise_query: bool
    target_department: Optional[str]
    confidence: float
    reason: str


class IntentClassifier:
    """Classifies user queries into granular intents and determines RAG routing."""

    # 1. GREETING PATTERNS (Vietnamese & English)
    GREETING_REGEX = re.compile(
        r"^(hi|hello|hey|alo|chào|chao|xin chào|xin chao|good morning|good afternoon|good evening|greetings)"
        r"(\s+(bạn|ban|anh|chị|chi|em|ad|admin|bot|cả nhà|mọi người|nhé|nhe))?[\s!.,?~]*$",
        re.IGNORECASE
    )

    # 2. SMALL TALK PATTERNS
    SMALL_TALK_REGEX = re.compile(
        r"(\b(bạn là ai|ban la ai|bạn tên gì|ban ten gi|who are you|what is your name|"
        r"bạn khỏe không|ban khoe khong|how are you|hôm nay thế nào|hom nay the nao|"
        r"hôm nay tôi hơi mệt|hom nay toi hoi met|tôi mệt quá|mệt mỏi|chán quá|stress|áp lực quá|"
        r"cảm ơn|cam on|thank you|thanks|tạm biệt|tam biet|bye|goodbye|see you|"
        r"bạn làm được gì|ban lam duoc gi|what can you do|bạn có thể giúp gì|"
        r"chúc bạn|chuc ban|chúc ngày mới|thời tiết hôm nay|kể chuyện cười)\b)",
        re.IGNORECASE
    )

    # 3. WRITING ASSISTANT PATTERNS
    WRITING_REGEX = re.compile(
        r"\b(viết giúp|viet giup|soạn giúp|soan giup|soạn thảo|soan thao|soạn|soan|"
        r"viết email|viet email|viết thư|viet thu|viết đoạn văn|soạn bài|lập dàn ý|"
        r"đặt câu|viết một bài|write an email|draft an email|write a letter|compose)\b",
        re.IGNORECASE
    )

    # 4. TRANSLATION PATTERNS
    TRANSLATION_REGEX = re.compile(
        r"\b(dịch sang|dich sang|dịch đoạn này|translate to|translate into|"
        r"dịch câu|tiếng anh của từ|nghĩa là gì trong tiếng anh)\b",
        re.IGNORECASE
    )

    # 5. GENERAL CONCEPT EXPLANATION (Not company-specific)
    TECH_TERMS = (
        r"(dhcp|dns|tcp/ip|osi|http|https|rest api|sql|python|javascript|"
        r"docker|kubernetes|ai|machine learning|deep learning|ram|cpu|ssd|gpu|"
        r"firewall|vlan|router|switch|agile|scrum|kanban)"
    )
    GENERAL_CONCEPT_REGEX = re.compile(
        rf"(\b(khái niệm|định nghĩa|thế nào là|the nao la|what is|define|explain)\s+{TECH_TERMS}\b|"
        rf"\b{TECH_TERMS}\s+(là gì|la gi|nghĩa là gì|để làm gì|hoạt động thế nào)\b)",
        re.IGNORECASE
    )

    # 6. ENTERPRISE DOMAIN KEYWORDS
    ENTERPRISE_DOMAINS = {
        "IT_HELPDESK": [
            "bsod", "màn hình xanh", "man hinh xanh", "treo máy", "kẹt in",
            "máy in", "may in", "print spooler", "outlook", "không nhận mail",
            "khong nhan mail", "m365", "teams", "bitlocker", "cài win", "driver",
            "mật khẩu máy", "reset pass", "tai khoan noi bo", "it support", "ticket"
        ],
        "IT_NETWORK": [
            "vlan", "trunking", "cisco", "switch", "router", "ospf", "bgp",
            "lacp", "etherchannel", "vpn", "ssl-vpn", "fortinet", "ipsec",
            "mạng nội bộ", "wifi công ty", "mất mạng", "đứt cáp", "mạng lan"
        ],
        "IT_SYSTEM": [
            "active directory", "domain controller", "gpo", "dns server",
            "file server", "smb", "nfs", "windows server", "linux", "vmware",
            "esxi", "vcenter", "hyper-v", "sao lưu", "backup", "veeam", "synology"
        ],
        "IT_SECURITY": [
            "soc", "siem", "wazuh", "edr", "antivirus", "kaspersky", "defender",
            "mfa", "2fa", "phishing", "mã độc", "ransomware", "lỗ hổng", "cve",
            "chính sách bảo mật", "an toàn thông tin", "iso 27001"
        ],
        "HR": [
            "nghỉ phép", "nghi phep", "phép năm", "phep nam", "bộ luật lao động",
            "luat lao dong", "hợp đồng lao động", "hop dong lao dong", "thai sản",
            "bảo hiểm xã hội", "bhxh", "bhyt", "lương", "tính lương", "thưởng",
            "thử việc", "thu viec", "onboarding", "kỷ luật lao động", "nội quy công ty"
        ],
        "ACCOUNTING": [
            "kế toán", "ke toan", "thông tư 200", "thong tu 200", "hạch toán",
            "chứng từ", "báo cáo tài chính", "bctc", "khấu hao", "tài sản cố định",
            "sổ cái", "công nợ", "đối chiếu công nợ", "tạm ứng", "hoàn ứng"
        ],
        "FINANCE": [
            "hóa đơn điện tử", "hoa don dien tu", "nghị định 123", "thông tư 78",
            "thuế", "thuế gtgt", "thuế tndn", "quy chế chi tiêu", "duyệt chi",
            "ngân sách", "thanh toán", "chuyển khoản", "chi phí"
        ],
        "SALES": [
            "bán hàng", "ban hang", "b2b", "báo giá", "quotation", "hợp đồng kinh tế",
            "chiết khấu", "hạn mức công nợ", "khách hàng doanh nghiệp", "pipeline", "crm"
        ],
        "PROCUREMENT": [
            "mua sắm", "mua sam", "đấu thầu", "dau thau", "luật đấu thầu",
            "phiếu pr", "purchase requisition", "đơn đặt hàng", "purchase order",
            "nhà cung cấp", "vendor", "so sánh báo giá", "rfq"
        ],
        "LEGAL": [
            "pháp chế", "phap che", "luật doanh nghiệp", "luật an ninh mạng",
            "bảo mật thông tin", "bí mật kinh doanh", "hợp đồng thương mại", "tranh chấp"
        ],
        "QA_QC": [
            "iso 9001", "quản lý chất lượng", "kiểm soát chất lượng", "kiểm tra chất lượng",
            "qa", "qc", "iqc", "ipqc", "oqc", "capa", "hành động khắc phục", "5 whys",
            "biểu đồ xương cá", "sai hỏng", "aql"
        ],
        "PRODUCTION_LOGISTICS": [
            "sản xuất", "5s", "kaizen", "tpm", "bảo trì máy móc", "kho bãi",
            "fifo", "fefo", "mã vạch", "kiểm kê kho", "giao nhận", "vận chuyển",
            "incoterms", "đội xe"
        ],
        "PLANNING_GENERAL": [
            "mrp", "mps", "hoạch định nguồn lực", "pmbok", "tiến độ dự án",
            "scrum", "bcp", "duy trì hoạt động liên tục", "iso 31000", "quản trị rủi ro"
        ]
    }

    # 7. EXPLICIT COMPANY CONTEXT CUES
    COMPANY_CUES = [
        "công ty", "cong ty", "doanh nghiệp", "doanh nghiep", "nội bộ", "noi bo",
        "quy trình", "quy trinh", "chính sách", "chinh sach", "quy định", "quy dinh",
        "hướng dẫn", "huong dan", "quy chế", "quy che", "sop", "biểu mẫu", "bieu mau",
        "theo luật", "theo nghị định", "theo thông tư"
    ]

    @classmethod
    def classify(cls, query: str) -> IntentResult:
        """Classify user query and decide if RAG search is required."""
        raw_text = query.strip()
        text_lower = raw_text.lower()

        if not text_lower:
            return IntentResult(
                intent="EMPTY",
                is_enterprise_query=False,
                target_department=None,
                confidence=1.0,
                reason="Tin nhắn rỗng"
            )

        # ---------------------------------------------------------------------
        # STEP 1: Fast-Path Greeting Detection (Zero RAG)
        # ---------------------------------------------------------------------
        if cls.GREETING_REGEX.match(text_lower):
            return IntentResult(
                intent="GREETING",
                is_enterprise_query=False,
                target_department=None,
                confidence=0.98,
                reason="Chào hỏi thông thường, phản hồi tự nhiên phong cách ChatGPT."
            )

        # ---------------------------------------------------------------------
        # STEP 2: Fast-Path Small Talk Detection (Zero RAG)
        # ---------------------------------------------------------------------
        if cls.SMALL_TALK_REGEX.match(text_lower):
            return IntentResult(
                intent="SMALL_TALK",
                is_enterprise_query=False,
                target_department=None,
                confidence=0.95,
                reason="Tâm sự, hỏi thăm, cảm ơn hoặc hỏi năng lực AI."
            )

        # ---------------------------------------------------------------------
        # STEP 3: Writing / Translation / General Skills (Zero RAG)
        # ---------------------------------------------------------------------
        if cls.WRITING_REGEX.search(text_lower) and not any(cue in text_lower for cue in ["quy chế", "sop", "tài liệu nội bộ"]):
            return IntentResult(
                intent="WRITING_ASSISTANT",
                is_enterprise_query=False,
                target_department=None,
                confidence=0.92,
                reason="Yêu cầu viết nội dung, soạn email hoặc thư từ tự nhiên."
            )

        if cls.TRANSLATION_REGEX.search(text_lower):
            return IntentResult(
                intent="TRANSLATION",
                is_enterprise_query=False,
                target_department=None,
                confidence=0.95,
                reason="Yêu cầu dịch thuật ngôn ngữ."
            )

        if cls.GENERAL_CONCEPT_REGEX.search(text_lower) and not any(cue in text_lower for cue in ["công ty", "nội bộ", "quy định"]):
            return IntentResult(
                intent="GENERAL_CHAT",
                is_enterprise_query=False,
                target_department=None,
                confidence=0.90,
                reason="Hỏi đáp kiến thức kỹ thuật phổ thông không thuộc chính sách riêng của công ty."
            )

        # ---------------------------------------------------------------------
        # STEP 4: Enterprise Domain Matching (Requires RAG)
        # ---------------------------------------------------------------------
        matched_domains = []
        for dept, keywords in cls.ENTERPRISE_DOMAINS.items():
            for kw in keywords:
                if kw in text_lower:
                    matched_domains.append((dept, kw))
                    break

        has_company_cue = any(cue in text_lower for cue in cls.COMPANY_CUES)

        if matched_domains:
            primary_dept = matched_domains[0][0]
            keyword_hit = matched_domains[0][1]

            # Determine specific enterprise intent
            if "IT" in primary_dept:
                intent_code = "IT_SUPPORT"
            elif primary_dept == "HR":
                intent_code = "HR_QUERY"
            elif primary_dept in ["ACCOUNTING", "FINANCE"]:
                intent_code = "FINANCE_QUERY"
            elif primary_dept == "SALES":
                intent_code = "SALES_QUERY"
            elif primary_dept == "PROCUREMENT":
                intent_code = "PROCUREMENT_QUERY"
            elif primary_dept == "LEGAL":
                intent_code = "LEGAL_QUERY"
            elif primary_dept == "QA_QC":
                intent_code = "QA_QC_QUERY"
            else:
                intent_code = "ENTERPRISE_KNOWLEDGE"

            return IntentResult(
                intent=intent_code,
                is_enterprise_query=True,
                target_department=primary_dept,
                confidence=0.92 if has_company_cue else 0.85,
                reason=f"Phát hiện chủ đề nghiệp vụ doanh nghiệp: {primary_dept} (Từ khóa: '{keyword_hit}')"
            )

        if has_company_cue:
            return IntentResult(
                intent="COMPANY_POLICY_QUERY",
                is_enterprise_query=True,
                target_department=None,
                confidence=0.82,
                reason="Phát hiện dấu hiệu truy vấn chính sách / quy trình nội bộ công ty."
            )

        # ---------------------------------------------------------------------
        # STEP 5: Default Fallback - General Chat
        # ---------------------------------------------------------------------
        # If query is short or casual without any enterprise match -> General Chat
        return IntentResult(
            intent="GENERAL_CHAT",
            is_enterprise_query=False,
            target_department=None,
            confidence=0.75,
            reason="Hội thoại tự nhiên chung, giải đáp bằng kiến thức nền của LLM."
        )


intent_classifier = IntentClassifier()
