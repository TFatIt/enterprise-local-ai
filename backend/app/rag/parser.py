"""Document parser module supporting PDF, DOCX, and TXT files."""

import os
import re
from typing import List, Dict, Any
from pypdf import PdfReader
from docx import Document as DocxDocument


class DocumentParser:
    """Extracts raw text and metadata from corporate document files."""

    @staticmethod
    def clean_text(text: str) -> str:
        """Normalize whitespace and strip non-printable control characters."""
        if not text:
            return ""
        # Remove null bytes and non-printable control chars except \n, \t, \r
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)
        # Normalize multiple spaces on the same line
        text = re.sub(r"[ \t]+", " ", text)
        # Normalize more than two consecutive newlines into double newlines
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
        return text.strip()

    @classmethod
    def parse_pdf(cls, file_path: str) -> List[Dict[str, Any]]:
        """Extract text from PDF page by page."""
        pages = []
        reader = PdfReader(file_path)
        for page_idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            cleaned = cls.clean_text(text)
            if cleaned:
                pages.append({
                    "text": cleaned,
                    "page": page_idx + 1,
                })
        return pages

    @classmethod
    def parse_docx(cls, file_path: str) -> List[Dict[str, Any]]:
        """Extract text from DOCX paragraphs and tables."""
        doc = DocxDocument(file_path)
        full_text = []

        for para in doc.paragraphs:
            if para.text.strip():
                full_text.append(para.text.strip())

        for table in doc.tables:
            for row in table.rows:
                row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_text:
                    full_text.append(" | ".join(row_text))

        combined = "\n\n".join(full_text)
        cleaned = cls.clean_text(combined)
        return [{"text": cleaned, "page": 1}] if cleaned else []

    @classmethod
    def parse_txt(cls, file_path: str) -> List[Dict[str, Any]]:
        """Read standard UTF-8 text file."""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        cleaned = cls.clean_text(content)
        return [{"text": cleaned, "page": 1}] if cleaned else []

    @classmethod
    def parse_file(cls, file_path: str, file_type: str) -> List[Dict[str, Any]]:
        """Dispatch parsing based on file extension."""
        ft = file_type.upper()
        if ft == "PDF":
            return cls.parse_pdf(file_path)
        elif ft in ["DOCX", "DOC"]:
            return cls.parse_docx(file_path)
        elif ft == "TXT":
            return cls.parse_txt(file_path)
        else:
            raise ValueError(f"Định dạng tệp '{file_type}' không được hỗ trợ.")


parser = DocumentParser()
