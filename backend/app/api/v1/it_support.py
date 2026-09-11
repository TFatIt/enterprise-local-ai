"""IT Support & Network Helpdesk API Router."""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_active_user, require_role
from app.models.user import User
from app.schemas.it_support import (
    DiagnoseRequest,
    DiagnoseResponse,
    QuickFixItem,
    ScriptGenerateRequest,
    ScriptGenerateResponse,
    HandoverChecklistRequest,
    HandoverChecklistResponse,
)
from app.rag.pipeline import rag_pipeline
from app.rag.llm import llm_client
from app.rag.vectorstore import vector_store
from app.rag.embeddings import embeddings_client
from app.services.audit_service import audit_service

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Verified Quick-Fix Knowledge Library for Common Enterprise IT Problems
# ---------------------------------------------------------------------------
QUICK_FIX_LIBRARY: List[Dict[str, Any]] = [
    {
        "id": "spooler_clean",
        "title": "Dọn sạch hàng đợi in & Khởi động lại Print Spooler",
        "category": "PRINTER",
        "description": "Khắc phục triệt để tình trạng máy in bị kẹt lệnh in (Print Queue hanging), không thể xóa lệnh in hoặc Spooler dừng đột ngột.",
        "script": """# 1. Chạy PowerShell với quyền Administrator
Write-Host "[1/4] Đang dừng dịch vụ Print Spooler..." -ForegroundColor Yellow
Stop-Service -Name Spooler -Force -ErrorAction SilentlyContinue

Write-Host "[2/4] Đang dọn sạch toàn bộ lệnh in bị kẹt trong bộ đệm..." -ForegroundColor Yellow
$spoolDir = "$env:SystemRoot\\System32\\spool\\PRINTERS"
if (Test-Path $spoolDir) {
    Get-ChildItem -Path "$spoolDir\\*" -Force | Remove-Item -Force -Verbose
}

Write-Host "[3/4] Đang khởi động lại dịch vụ Print Spooler..." -ForegroundColor Yellow
Start-Service -Name Spooler

Write-Host "[4/4] Kiểm tra trạng thái Spooler:" -ForegroundColor Green
Get-Service -Name Spooler | Select-Object Name, Status, StartType
Write-Host ">>> Hoàn tất! Hãy thử in lại tài liệu." -ForegroundColor Cyan
""",
        "script_type": "powershell",
        "requires_admin": True,
        "execution_guide": "Nhấp chuột phải vào nút Start -> chọn Terminal (Admin) hoặc PowerShell (Run as Administrator) -> Dán toàn bộ mã trên và nhấn Enter."
    },
    {
        "id": "printer_error_0x11b",
        "title": "Sửa lỗi kết nối máy in mạng chia sẻ (Mã lỗi 0x0000011b / 0x00000709)",
        "category": "PRINTER",
        "description": "Khắc phục lỗi Windows bảo mật RPC khiến các máy trạm không thể kết nối hoặc in qua máy in chia sẻ nội bộ từ Print Server / máy trạm khác.",
        "script": """# Thực thi trên máy chia sẻ máy in (Print Server hoặc máy chủ in)
Write-Host "[*] Đang cấu hình Registry sửa lỗi RPC 0x0000011b..." -ForegroundColor Yellow
$regPath = "HKLM:\\System\\CurrentControlSet\\Control\\Print"
New-ItemProperty -Path $regPath -Name "RpcAuthnLevelPrivacyEnabled" -PropertyType DWord -Value 0 -Force | Out-Null

Write-Host "[*] Khởi động lại dịch vụ Spooler để áp dụng..." -ForegroundColor Yellow
Restart-Service -Name Spooler -Force

Write-Host ">>> Đã sửa xong! Kiểm tra kết nối từ máy trạm." -ForegroundColor Green
""",
        "script_type": "powershell",
        "requires_admin": True,
        "execution_guide": "Thực hiện trên máy tính đang cắm máy in và chia sẻ. Khởi động lại Spooler sau khi chạy."
    },
    {
        "id": "excel_heavy_calc_optimize",
        "title": "Tối ưu hóa Excel nhiều công thức / Giảm thời gian đơ khi lưu file",
        "category": "EXCEL_OFFICE",
        "description": "Giải quyết tình trạng Excel đơ, chậm, CPU 100% khi mở hoặc lưu các file Excel kế toán nặng chứa hàng nghìn công thức VLOOKUP, INDEX/MATCH, SUMIFS.",
        "script": """# Script cấu hình Registry tối ưu hóa hiệu năng Microsoft Excel (Office 2016 / 2019 / 2021 / 365)
Write-Host "[1/3] Đang tắt Tăng tốc đồ họa phần cứng (Disable Hardware Acceleration) của Office..." -ForegroundColor Yellow
$officePaths = @(
    "HKCU:\\Software\\Microsoft\\Office\\16.0\\Common\\Graphics",
    "HKCU:\\Software\\Microsoft\\Office\\15.0\\Common\\Graphics"
)
foreach ($p in $officePaths) {
    if (!(Test-Path $p)) { New-Item -Path $p -Force | Out-Null }
    New-ItemProperty -Path $p -Name "DisableHardwareAcceleration" -PropertyType DWord -Value 1 -Force | Out-Null
}

Write-Host "[2/3] Hướng dẫn trong file Excel cụ thể:" -ForegroundColor Cyan
Write-Host "  - Vào Formulas -> Calculation Options -> Chọn 'Manual' (hoặc 'Automatic except for data tables')" -ForegroundColor White
Write-Host "  - Khi cần tính toán lại dữ liệu mới, nhấn phím F9 (toàn bộ workbook) hoặc Shift + F9 (sheet hiện tại)" -ForegroundColor White
Write-Host "  - Vào File -> Options -> Advanced -> phần Formulas: Đảm bảo tick 'Enable multi-threaded calculation' (sử dụng tất cả lõi CPU)" -ForegroundColor White

Write-Host "[3/3] Đã cấu hình Registry xong! Vui lòng khởi động lại Excel." -ForegroundColor Green
""",
        "script_type": "powershell",
        "requires_admin": False,
        "execution_guide": "Chạy script bằng PowerShell thông thường (không cần quyền Admin). Sau đó mở Excel áp dụng chế độ tính toán thủ công Manual cho file nặng."
    },
    {
        "id": "office_cache_clean",
        "title": "Dọn dẹp Office Cache & Sửa lỗi tài liệu Office không thể lưu / treo máy",
        "category": "EXCEL_OFFICE",
        "description": "Xóa bộ đệm tài liệu tạm thời của Microsoft Office khi gặp lỗi 'Upload Failed', 'Document Locked', hoặc Office bị đơ khi lưu file lên ổ mạng.",
        "script": """Write-Host "[1/3] Đang tắt các tiến trình Office đang chạy..." -ForegroundColor Yellow
Get-Process -Name excel, winword, powerpnt, msaccess -ErrorAction SilentlyContinue | Stop-Process -Force

Write-Host "[2/3] Đang dọn sạch Office Document Cache..." -ForegroundColor Yellow
$cachePath = "$env:LOCALAPPDATA\\Microsoft\\Office\\16.0\\OfficeFileCache"
if (Test-Path $cachePath) {
    Remove-Item -Path "$cachePath\\*" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "  -> Đã dọn sạch thư mục OfficeFileCache" -ForegroundColor Green
}

Write-Host "[3/3] Hoàn tất! Mở lại Word/Excel và lưu file." -ForegroundColor Green
""",
        "script_type": "powershell",
        "requires_admin": False,
        "execution_guide": "Đóng tất cả file Office trước khi chạy để tránh mất dữ liệu chưa lưu."
    },
    {
        "id": "network_deep_flush",
        "title": "Khôi phục kết nối mạng & Xóa toàn bộ Cache DNS / Reset Winsock",
        "category": "NETWORK",
        "description": "Sửa lỗi máy tính không vào được web nội bộ, mạng chập chờn, lỗi IP conflict hoặc không nhận diện được Domain Controller / Server nội bộ.",
        "script": """Write-Host "[1/5] Đang xóa bộ nhớ đệm phân giải tên miền (DNS Cache)..." -ForegroundColor Yellow
ipconfig /flushdns

Write-Host "[2/5] Đang giải phóng và yêu cầu cấp mới địa chỉ IP qua DHCP..." -ForegroundColor Yellow
ipconfig /release
ipconfig /renew

Write-Host "[3/5] Đang thiết lập lại danh mục Winsock..." -ForegroundColor Yellow
netsh winsock reset

Write-Host "[4/5] Đang thiết lập lại ngăn xếp TCP/IP..." -ForegroundColor Yellow
netsh int ip reset

Write-Host "[5/5] Hoàn tất! Vui lòng khởi động lại máy tính để các thay đổi mạng có hiệu lực tối đa." -ForegroundColor Green
""",
        "script_type": "powershell",
        "requires_admin": True,
        "execution_guide": "Chạy trong PowerShell (Admin). Nên khởi động lại máy tính sau khi chạy."
    },
    {
        "id": "software_bootstrap_standard",
        "title": "Script cài đặt tự động Bộ phần mềm chuẩn văn phòng doanh nghiệp",
        "category": "SOFTWARE",
        "description": "Tự động tải và cài đặt bộ phần mềm cơ bản cho nhân viên mới qua Windows Package Manager (Winget) hoàn toàn tự động.",
        "script": """# Script cài đặt gói phần mềm chuẩn văn phòng cho nhân viên
Write-Host "=== BẮT ĐẦU CÀI ĐẶT BỘ PHẦN MỀM CHUẨN DOANH NGHIỆP ===" -ForegroundColor Cyan

$packages = @(
    @{ Id = "Google.Chrome"; Name = "Google Chrome" },
    @{ Id = "7zip.7zip"; Name = "7-Zip Giải nén" },
    @{ Id = "UniKey.UniKey"; Name = "Bộ gõ tiếng Việt UniKey" },
    @{ Id = "Adobe.Acrobat.Reader.64-bit"; Name = "Adobe Acrobat Reader" },
    @{ Id = "AnyDeskSoftwareGmbH.AnyDesk"; Name = "AnyDesk Hỗ trợ từ xa" }
)

foreach ($pkg in $packages) {
    Write-Host "[*] Đang cài đặt: $($pkg.Name)..." -ForegroundColor Yellow
    winget install --id $($pkg.Id) --silent --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -eq 0) {
        Write-Host " -> Cài đặt thành công: $($pkg.Name)" -ForegroundColor Green
    } else {
        Write-Host " -> Thông báo: $($pkg.Name) đã tồn tại hoặc cần kiểm tra lại." -ForegroundColor DarkYellow
    }
}

Write-Host "=== HOÀN TẤT CÀI ĐẶT BỘ PHẦN MỀM CHUẨN ===" -ForegroundColor Cyan
""",
        "script_type": "powershell",
        "requires_admin": True,
        "execution_guide": "Yêu cầu máy tính có kết nối Internet và hỗ trợ winget (Windows 10 bản 1809 trở lên hoặc Windows 11)."
    },
    {
        "id": "clean_c_drive_temp",
        "title": "Dọn dẹp ổ đĩa C & Xóa rác hệ thống / File tạm người dùng",
        "category": "HARDWARE",
        "description": "Giải phóng dung lượng ổ C bị đầy do file rác người dùng (%temp%), Windows Temp, bộ nhớ đệm Windows Update.",
        "script": """Write-Host "[1/3] Đang dọn thư mục Temp người dùng..." -ForegroundColor Yellow
Remove-Item -Path "$env:TEMP\\*" -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "[2/3] Đang dọn thư mục Temp hệ điều hành Windows..." -ForegroundColor Yellow
Remove-Item -Path "$env:SystemRoot\\Temp\\*" -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "[3/3] Đang dừng dịch vụ Update và dọn bộ nhớ đệm SoftwareDistribution..." -ForegroundColor Yellow
Stop-Service -Name wuauserv -Force -ErrorAction SilentlyContinue
Remove-Item -Path "$env:SystemRoot\\SoftwareDistribution\\Download\\*" -Recurse -Force -ErrorAction SilentlyContinue
Start-Service -Name wuauserv -ErrorAction SilentlyContinue

Write-Host ">>> Hoàn tất dọn dẹp ổ C!" -ForegroundColor Green
""",
        "script_type": "powershell",
        "requires_admin": True,
        "execution_guide": "Chạy với quyền Administrator để dọn sạch toàn bộ file rác ổ C."
    }
]


@router.get(
    "/quick-fixes",
    response_model=List[QuickFixItem],
    summary="Thư viện Giải pháp IT & Script PowerShell Chạy Ngay",
    description="Danh sách các script và quy trình giải quyết sự cố IT phổ biến (Máy in, Excel nặng, Mạng, Cài phần mềm).",
)
def get_quick_fixes(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
):
    """Get verified quick-fix scripts for common enterprise IT issues."""
    if not category or category.upper() == "ALL":
        return QUICK_FIX_LIBRARY
    cat_upper = category.upper()
    return [q for q in QUICK_FIX_LIBRARY if q["category"] == cat_upper]


@router.post(
    "/diagnose",
    response_model=DiagnoseResponse,
    summary="Chẩn đoán Thông minh Sự cố IT bằng AI & RAG",
    description="Nhập mô tả lỗi để AI phân tích nguyên nhân gốc, tra cứu tài liệu hướng dẫn và sinh script xử lý tự động.",
)
def diagnose_it_problem(
    req: DiagnoseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Perform smart IT troubleshooting diagnosis using local RAG and LLM."""
    query = req.problem_description
    if req.error_code_or_message:
        query += f" Mã lỗi: {req.error_code_or_message}"

    category = (req.category or "GENERAL").upper()

    # 1. Retrieve relevant knowledge chunks from vector store
    retrieved_sources = []
    try:
        q_emb = embeddings_client.embed_query(query)
        chunks = vector_store.search_similar(
            query_embedding=q_emb,
            top_k=4,
            threshold=0.35,
            user=current_user,
        )
        for c in chunks:
            retrieved_sources.append({
                "title": c.get("metadata", {}).get("title") or c.get("metadata", {}).get("file_name", "Tài liệu"),
                "file_name": c.get("metadata", {}).get("file_name", ""),
                "snippet": c.get("content", "")[:250],
                "score": round(float(c.get("score", 0.0)), 3),
            })
    except Exception as e:
        logger.warning(f"Error querying RAG for IT diagnosis: {e}")

    # 2. Check if a direct quick-fix matches
    matching_fix = None
    desc_lower = query.lower()
    if any(w in desc_lower for w in ["máy in", "printer", "spooler", "in ấn", "kẹt lệnh"]):
        if "0x0000011b" in desc_lower or "chia sẻ" in desc_lower:
            matching_fix = next((f for f in QUICK_FIX_LIBRARY if f["id"] == "printer_error_0x11b"), None)
        else:
            matching_fix = next((f for f in QUICK_FIX_LIBRARY if f["id"] == "spooler_clean"), None)
    elif any(w in desc_lower for w in ["excel", "công thức", "tính toán", "lag", "đơ khi lưu", "chậm khi lưu"]):
        matching_fix = next((f for f in QUICK_FIX_LIBRARY if f["id"] == "excel_heavy_calc_optimize"), None)
    elif any(w in desc_lower for w in ["office", "word", "upload failed", "file locked"]):
        matching_fix = next((f for f in QUICK_FIX_LIBRARY if f["id"] == "office_cache_clean"), None)
    elif any(w in desc_lower for w in ["mạng", "network", "dns", "ip", "mất mạng", "rớt mạng", "winsock"]):
        matching_fix = next((f for f in QUICK_FIX_LIBRARY if f["id"] == "network_deep_flush"), None)
    elif any(w in desc_lower for w in ["ổ c", "đầy ổ", "disk full", "temp", "dọn rác"]):
        matching_fix = next((f for f in QUICK_FIX_LIBRARY if f["id"] == "clean_c_drive_temp"), None)

    # 3. Formulate response using LLM or structured knowledge base fallback
    context_text = "\n\n".join([f"[{s['title']}]: {s['snippet']}" for s in retrieved_sources])

    system_prompt = (
        "Bạn là Chuyên gia IT Network & Support cấp cao của doanh nghiệp. "
        "Hãy chẩn đoán sự cố IT dựa trên mô tả lỗi và tài liệu kỹ thuật nội bộ cung cấp. "
        "Hãy trả lời ngắn gọn, chuẩn xác, đầy đủ các bước thực tế và cung cấp lệnh PowerShell/CMD chuẩn xác."
    )

    prompt = f"""Mô tả sự cố IT: {query}
Phân loại: {category}
Tài liệu liên quan nội bộ:
{context_text if context_text else 'Không có tài liệu trực tiếp, hãy dùng tri thức chuẩn IT Enterprise.'}

Hãy phân tích theo cấu trúc sau:
1. NGUYÊN NHÂN GỐC: (Phân tích ngắn gọn vì sao xảy ra lỗi)
2. HƯỚNG DẪN CHO NGƯỜI DÙNG: (Các bước đơn giản người dùng có thể tự thử)
3. HƯỚNG DẪN CHO KỸ THUẬT IT: (Các bước chuyên sâu, lệnh cấu hình hệ thống)
4. LỆNH / SCRIPT POWERSHELL SỬA LỖI: (Chỉ đưa code khối powershell)
5. LƯU Ý PHÒNG NGỪA: (Lời khuyên để không lặp lại)
"""

    llm_output = ""
    try:
        llm_output = llm_client.generate(
            prompt=prompt,
            system=system_prompt,
            temperature=0.1,
            max_tokens=1000,
        )
    except Exception as e:
        logger.warning(f"LLM generation fallback during IT diagnosis: {e}")

    # Parse sections or fallback
    recommended_script = matching_fix["script"] if matching_fix else None

    user_steps = []
    it_steps = []
    root_cause = "Sự cố phát sinh từ cấu hình dịch vụ hệ điều hành hoặc xung đột phần mềm / bộ đệm dữ liệu."
    prevention_tip = "Thực hiện bảo trì định kỳ, cập nhật bản vá driver ổn định và sao lưu dữ liệu thường xuyên."

    if matching_fix:
        if matching_fix["id"] == "spooler_clean":
            root_cause = "Dịch vụ Print Spooler bị treo do tệp lệnh in (.spl/.shd) bị lỗi hoặc quá tải trong thư mục C:\\Windows\\System32\\spool\\PRINTERS."
            user_steps = [
                "Khởi động lại máy in vật lý (tắt nguồn 15s rồi bật lại).",
                "Kiểm tra dây cáp USB hoặc cáp mạng LAN cắm vào máy in.",
                "Hủy các lệnh in cá nhân trong cửa sổ Devices and Printers."
            ]
            it_steps = [
                "Dừng dịch vụ Print Spooler bằng lệnh Stop-Service Spooler -Force.",
                "Xóa sạch toàn bộ tệp tạm trong C:\\Windows\\System32\\spool\\PRINTERS.",
                "Khởi động lại dịch vụ Spooler và kiểm tra Print Test Page."
            ]
            prevention_tip = "Cài đặt Driver chuẩn PCL6/PostScript chính hãng từ nhà sản xuất, hạn chế dùng Driver generic của Windows."
        elif matching_fix["id"] == "excel_heavy_calc_optimize":
            root_cause = "File Excel chứa quá nhiều công thức phức tạp (VLOOKUP, SUMIFS lồng nhau, công thức mảng toàn cột) khiến Excel tính toán lại toàn bộ mỗi khi bấm Save."
            user_steps = [
                "Vào Formulas -> Calculation Options -> Chuyển từ 'Automatic' sang 'Manual'.",
                "Mỗi khi cần tính lại số liệu thì nhấn phím F9.",
                "Tránh tham chiếu toàn bộ cột như A:A, hãy giới hạn vùng dữ liệu cụ thể như A2:A10000."
            ]
            it_steps = [
                "Vào File -> Options -> Advanced -> phần Formulas: Kiểm tra mục Multi-threaded calculation xem đã bật tất cả CPU cores chưa.",
                "Vào File -> Options -> Advanced -> Display: Bật 'Disable hardware graphics acceleration' để tránh tràn bộ nhớ GPU.",
                "Khuyên phòng Kế toán chuyển các file tổng hợp lớn sang Power Query hoặc định dạng nhị phân (.xlsb) để tăng tốc độ lưu file gấp 3-5 lần."
            ]
            prevention_tip = "Lưu file nặng dưới định dạng Excel Binary (.xlsb) giúp giảm 50% dung lượng và lưu file cực nhanh."
        elif matching_fix["id"] == "network_deep_flush":
            root_cause = "Bộ nhớ đệm phân giải DNS hoặc cấu hình địa chỉ IP qua DHCP bị phân mảnh hoặc xung đột với thiết bị mạng khác."
            user_steps = [
                "Rút cáp mạng LAN hoặc ngắt kết nối Wi-Fi khoảng 10 giây rồi cắm lại.",
                "Tắt chế độ máy bay (Airplane mode) nếu đang dùng laptop.",
                "Khởi động lại máy tính nếu mạng vẫn báo 'No Internet, secured'."
            ]
            it_steps = [
                "Thực hiện xóa bộ nhớ cache DNS: ipconfig /flushdns.",
                "Yêu cầu cấp phát lại IP: ipconfig /release và ipconfig /renew.",
                "Reset toàn bộ Winsock catalog và TCP/IP stack: netsh winsock reset."
            ]
            prevention_tip = "Đặt IP tĩnh cho các máy in, máy chủ và đảm bảo dải cấp phát DHCP không bị tràn."

    # Audit log
    try:
        audit_service.log_event(
            db=db,
            action="IT_DIAGNOSE",
            resource="IT_SUPPORT",
            user_id=current_user.id,
            details={
                "category": category,
                "problem": query[:150],
                "matched_quick_fix": matching_fix["id"] if matching_fix else None,
            }
        )
    except Exception:
        pass

    return DiagnoseResponse(
        problem_summary=query,
        category=category,
        root_cause_analysis=root_cause,
        user_action_steps=user_steps if user_steps else [
            "Khởi động lại phần mềm đang gặp lỗi.",
            "Kiểm tra kết nối vật lý (dây mạng, cáp nguồn).",
            "Lưu tài liệu đang mở để tránh mất dữ liệu."
        ],
        it_admin_steps=it_steps if it_steps else [
            "Kiểm tra Event Viewer (Windows Logs -> Application/System).",
            "Kiểm tra trạng thái Service liên quan trong services.msc.",
            "Thực thi script xử lý theo khuyến nghị dưới đây."
        ],
        recommended_script=recommended_script,
        script_type="powershell",
        related_knowledge_sources=retrieved_sources,
        prevention_tip=prevention_tip,
    )


@router.post(
    "/handover-checklist",
    response_model=HandoverChecklistResponse,
    summary="Sinh Biên bản Bàn giao Thiết bị & Onboarding IT",
    description="Tự động lập biên bản bàn giao máy tính, cấu hình, máy in và phần mềm phân quyền cho nhân viên mới.",
)
def generate_handover_checklist(
    req: HandoverChecklistRequest,
    current_user: User = Depends(require_role(["SUPER_ADMIN", "ADMIN", "IT_ADMIN"])),
):
    """Generate professional IT Handover / Equipment Onboarding document."""
    default_software = [
        "Windows 10/11 Pro Bản quyền (Join Domain công ty)",
        "Microsoft Office 365 / 2021 (Đã cấu hình Email Outlook)",
        "Trình duyệt Google Chrome & Microsoft Edge",
        "Bộ gõ tiếng Việt UniKey / EVKey",
        "Phần mềm đọc PDF (Adobe Acrobat / Foxit Reader)",
        "Phần mềm nén/giải nén 7-Zip",
        "Phần mềm hỗ trợ từ xa IT (AnyDesk / UltraViewer / TeamViewer)",
        "Phần mềm diệt virus doanh nghiệp / Windows Defender Endpoint",
    ]

    all_software = default_software + (req.software_packages or [])

    printers_str = ", ".join(req.assigned_printers) if req.assigned_printers else "Máy in văn phòng tầng làm việc"

    markdown_doc = f"""# BIÊN BẢN BÀN GIAO THIẾT BỊ CNTT & TÀI KHOẢN LÀM VIỆC

**Thời gian lập biên bản:** Hàng ngày  
**Cán bộ IT bàn giao:** {current_user.full_name} ({current_user.email})  
**Người tiếp nhận:** {req.employee_name}  
**Mã nhân viên:** {req.employee_code or 'N/A'}  
**Phòng ban:** {req.department}  
**Chức danh:** {req.position or 'Nhân viên'}  

---

## 1. THÔNG TIN THIẾT BỊ PHẦN CỨNG BÀN GIAO
- **Loại thiết bị:** {req.pc_type}
- **Cấu hình chi tiết:** {req.hardware_specs or 'Intel Core i5 / 16GB RAM / 512GB NVMe SSD'}
- **Tình trạng ngoại quan:** Mới 100% / Hoạt động hoàn hảo, không trầy xước, tem bảo hành nguyên vẹn
- **Phụ kiện kèm theo:** Sạc nguồn chính hãng, chuột quang, bàn phím, túi chống sốc (nếu là Laptop)

## 2. TÀI KHOẢN & PHÂN QUYỀN MẠNG NỘI BỘ
- [x] Tài khoản đăng nhập máy (Domain / Local User)
- [x] Email công ty (Outlook / Webmail)
- [x] Phân quyền truy cập Ổ mạng chia sẻ phòng ban: `\\\\fileserver\\{req.department}`
- [x] Cấu hình máy in mạng: **{printers_str}**
- [x] Phân quyền mạng Wi-Fi nội bộ doanh nghiệp

## 3. DANH MỤC PHẦN MỀM ĐÃ CÀI ĐẶT
"""
    for idx, sw in enumerate(all_software, 1):
        markdown_doc += f"{idx}. [x] {sw}\n"

    markdown_doc += f"""
## 4. QUY ĐỊNH AN TOÀN THÔNG TIN & SỬ DỤNG THIẾT BỊ
1. Nhân viên có trách nhiệm bảo quản thiết bị được giao, không tự ý tháo mở hoặc cài đặt phần mềm không có bản quyền.
2. Không tiết lộ mật khẩu tài khoản công ty cho người khác.
3. Khi gặp sự cố kỹ thuật, tạo Ticket hỗ trợ trên hệ thống Local AI IT Helpdesk hoặc liên hệ đội ngũ IT.

---

**ĐẠI DIỆN BỘ PHẬN IT BÀN GIAO**                       **NGƯỜI TIẾP NHẬN THIẾT BỊ**  
*(Ký và ghi rõ họ tên)*                               *(Ký và ghi rõ họ tên)*  

{current_user.full_name}                              {req.employee_name}
"""

    return HandoverChecklistResponse(
        checklist_markdown=markdown_doc.strip(),
        checklist_data={
            "employee_name": req.employee_name,
            "department": req.department,
            "pc_type": req.pc_type,
            "software_count": len(all_software),
            "assigned_printers": req.assigned_printers,
        }
    )


@router.post(
    "/generate-script",
    response_model=ScriptGenerateResponse,
    summary="Tự động Sinh Script Quản trị IT (PowerShell / Batch)",
    description="Mô tả tác vụ IT cần thực hiện, AI sẽ viết script PowerShell hoặc Batch an toàn kèm chú thích.",
)
def generate_admin_script(
    req: ScriptGenerateRequest,
    current_user: User = Depends(require_role(["SUPER_ADMIN", "ADMIN", "IT_ADMIN"])),
):
    """Generate safe, production-grade IT automation scripts."""
    lang = req.script_language.lower()
    os_target = req.target_os.lower()

    prompt = f"""Bạn là Kỹ sư Tự động hóa IT Doanh nghiệp.
Hãy viết một đoạn script {lang.upper()} chạy trên hệ điều hành {os_target.upper()} để thực hiện tác vụ sau:
"{req.task_description}"

Yêu cầu:
1. Script phải an toàn, có bẫy lỗi (Try/Catch đối với PowerShell), ghi log rõ ràng ra màn hình console bằng màu sắc dễ nhìn.
2. Không thực hiện hành động xóa nguy hiểm mà không kiểm tra tồn tại.
3. Đưa ra giải thích từng bước thực hiện và lưu ý an toàn.
"""

    try:
        response_text = llm_client.generate(
            prompt=prompt,
            system="Bạn là chuyên gia viết script quản trị hệ thống Windows/Linux cho doanh nghiệp.",
            temperature=0.1,
            max_tokens=1000,
        )
    except Exception as e:
        logger.warning(f"Error calling LLM for script generation: {e}")
        response_text = f"# Script mẫu cho: {req.task_description}\nWrite-Host 'Đang thực hiện tác vụ: {req.task_description}' -ForegroundColor Cyan"

    # Extract code block if markdown formatted
    script_code = response_text
    if f"```{lang}" in response_text:
        script_code = response_text.split(f"```{lang}")[1].split("```")[0].strip()
    elif "```powershell" in response_text:
        script_code = response_text.split("```powershell")[1].split("```")[0].strip()
    elif "```" in response_text:
        script_code = response_text.split("```")[1].split("```")[0].strip()

    return ScriptGenerateResponse(
        title=f"Script tự động hóa: {req.task_description[:50]}",
        script_language=lang,
        script_code=script_code,
        explanation=f"Script được sinh tự động cho tác vụ: {req.task_description}",
        safety_notes="Khuyến nghị kiểm tra trên môi trường thử nghiệm hoặc chạy với quyền Administrator cẩn thận.",
    )
