"""Text chunker using Recursive Character Splitting algorithm."""

from typing import List, Dict, Any


class RecursiveCharacterChunker:
    """Splits long text into contextual chunks with sliding overlap."""

    def __init__(self, chunk_size: int = 700, chunk_overlap: int = 120):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = ["\n\n", "\n", ". ", "; ", "! ", "? ", " ", ""]

    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        """Recursively split text using hierarchy of separators."""
        final_chunks = []
        separator = separators[-1]
        new_separators = []

        for i, _s in enumerate(separators):
            if _s == "":
                separator = _s
                break
            if _s in text:
                separator = _s
                new_separators = separators[i + 1:]
                break

        splits = text.split(separator) if separator else list(text)

        good_splits = []
        for s in splits:
            if separator and s:
                item = s if separator == " " or separator == "\n" or separator == "\n\n" else s + separator
            else:
                item = s
            if item:
                good_splits.append(item)

        # Merge splits up to chunk_size
        current_chunk = []
        current_len = 0

        for s in good_splits:
            if len(s) > self.chunk_size and new_separators:
                # Sub-split oversized string
                sub_chunks = self._split_text(s, new_separators)
                for sc in sub_chunks:
                    final_chunks.append(sc)
                continue

            if current_len + len(s) <= self.chunk_size:
                current_chunk.append(s)
                current_len += len(s)
            else:
                if current_chunk:
                    merged = "".join(current_chunk).strip()
                    if merged:
                        final_chunks.append(merged)

                # Keep overlap from the end of current chunk
                overlap_chunk = []
                overlap_len = 0
                for item in reversed(current_chunk):
                    if overlap_len + len(item) <= self.chunk_overlap:
                        overlap_chunk.insert(0, item)
                        overlap_len += len(item)
                    else:
                        break

                current_chunk = overlap_chunk + [s]
                current_len = sum(len(x) for x in current_chunk)

        if current_chunk:
            merged = "".join(current_chunk).strip()
            if merged:
                final_chunks.append(merged)

        return final_chunks

    def chunk_document(
        self,
        pages: List[Dict[str, Any]],
        document_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Process extracted pages and produce indexed chunk list."""
        all_chunks = []
        chunk_idx = 0

        for page_data in pages:
            text = page_data.get("text", "")
            page_num = page_data.get("page", 1)

            splits = self._split_text(text, self.separators)

            for split in splits:
                if len(split.strip()) < 30:
                    continue  # Skip trivially short fragments
                chunk_obj = {
                    "chunk_index": chunk_idx,
                    "content": split.strip(),
                    "metadata": {
                        **document_metadata,
                        "page_number": page_num,
                        "chunk_index": chunk_idx,
                        "char_count": len(split.strip()),
                    }
                }
                all_chunks.append(chunk_obj)
                chunk_idx += 1

        return all_chunks


chunker = RecursiveCharacterChunker()
