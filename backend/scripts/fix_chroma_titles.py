"""Fix corrupted Vietnamese titles in ChromaDB metadata."""

import os
import sys
import chromadb

# Mapping of file_name to clean UTF-8 Vietnamese title
CANONICAL_TITLES = {
    "sample_it_policy.txt": "Chính sách An toàn Mật khẩu, Gia nhập Miền AD & Cấu hình VPN",
    "sample_troubleshooting_handbook.txt": "Sổ tay Xử lý Sự cố Kỹ thuật IT HelpDesk, Mạng LAN & Outlook",
    "sample_cyber_security_pdpd.txt": "Chính sách An toàn Thông tin & Tuân thủ Bảo vệ Dữ liệu Cá nhân (Nghị định 13)",
    "sample_hr_policy.txt": "Nội quy Lao động, Chế độ Nghỉ phép & Phúc lợi Nhân sự",
    "sample_finance_accounting_policy.txt": "Quy định Thanh toán, Hoàn ứng, Duyệt chi & Hóa đơn Điện tử",
    "sample_procurement_sourcing_policy.txt": "Quy trình Mua sắm Hàng hóa & Đánh giá Nhà Cung cấp (Procure-to-Pay)",
    "sample_b2b_sales_commercial_policy.txt": "Quy trình Bán hàng B2B 7 Bước & Khung Chính sách Giá Chiết khấu",
    "Ban_Do_Tai_Lieu_Tri_Thuc_Doanh_Nghiep.docx": "Bản đồ Khám phá & Quy hoạch Tri thức Toàn Doanh nghiệp",
}


def fix_chroma_metadata(chroma_path="chroma_data"):
    print(f"Connecting to ChromaDB at '{chroma_path}'...")
    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.get_collection("enterprise_knowledge_base")
    total_count = collection.count()
    print(f"Total chunks in collection: {total_count}")

    # Fetch all records
    results = collection.get(include=["metadatas"])
    ids_to_update = []
    new_metadatas = []

    for chunk_id, meta in zip(results["ids"], results["metadatas"]):
        file_name = meta.get("file_name", "")
        current_title = meta.get("title", "")

        # Check if title has question marks or matches our canonical mapping
        canonical = CANONICAL_TITLES.get(file_name)
        if canonical and (canonical != current_title or "?" in current_title):
            updated_meta = dict(meta)
            updated_meta["title"] = canonical
            ids_to_update.append(chunk_id)
            new_metadatas.append(updated_meta)
        elif "?" in current_title and file_name in CANONICAL_TITLES:
            updated_meta = dict(meta)
            updated_meta["title"] = CANONICAL_TITLES[file_name]
            ids_to_update.append(chunk_id)
            new_metadatas.append(updated_meta)

    print(f"Found {len(ids_to_update)} chunks with corrupted titles to update.")
    if ids_to_update:
        # ChromaDB batch update
        batch_size = 100
        for i in range(0, len(ids_to_update), batch_size):
            batch_ids = ids_to_update[i:i+batch_size]
            batch_metas = new_metadatas[i:i+batch_size]
            collection.update(ids=batch_ids, metadatas=batch_metas)
            print(f"  Updated batch {i+1} - {min(i+batch_size, len(ids_to_update))}")

        print("Successfully updated all corrupted ChromaDB metadata titles!")

    # Verify
    verify_results = collection.get(limit=200, include=["metadatas"])
    corrupt_count = sum(1 for m in verify_results["metadatas"] if "?" in m.get("title", ""))
    print(f"Verification: remaining corrupted titles in sample: {corrupt_count}")


if __name__ == "__main__":
    fix_chroma_metadata()
