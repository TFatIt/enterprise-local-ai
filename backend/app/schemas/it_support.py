"""Pydantic schemas for IT Support & Network Helpdesk API."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class DiagnoseRequest(BaseModel):
    problem_description: str = Field(
        ...,
        min_length=3,
        description="Mô tả chi tiết sự cố IT gặp phải (vd: máy in kẹt lệnh in, Excel đơ khi lưu, mất mạng nội bộ...)"
    )
    category: Optional[str] = Field(
        default="GENERAL",
        description="Phân loại sự cố: PRINTER, EXCEL_OFFICE, NETWORK, SOFTWARE, HARDWARE, ONBOARDING, GENERAL"
    )
    error_code_or_message: Optional[str] = Field(
        default=None,
        description="Mã lỗi hoặc thông báo lỗi chính xác nếu có (vd: 0x0000011b, #VALUE!, 10060, v.v.)"
    )
    affected_user_or_pc: Optional[str] = Field(
        default=None,
        description="Tên người dùng, phòng ban hoặc mã máy tính bị ảnh hưởng"
    )


class DiagnoseResponse(BaseModel):
    problem_summary: str
    category: str
    root_cause_analysis: str
    user_action_steps: List[str]
    it_admin_steps: List[str]
    recommended_script: Optional[str] = None
    script_type: Optional[str] = "powershell"
    related_knowledge_sources: List[Dict[str, Any]] = []
    prevention_tip: Optional[str] = None


class QuickFixItem(BaseModel):
    id: str
    title: str
    category: str
    description: str
    script: str
    script_type: str = "powershell"
    requires_admin: bool = True
    execution_guide: str


class ScriptGenerateRequest(BaseModel):
    task_description: str = Field(
        ...,
        min_length=5,
        description="Mô tả tác vụ quản trị IT cần tự động hóa (vd: dọn dẹp file rác thư mục Temp của người dùng, kiểm tra cổng mạng 445...)"
    )
    script_language: Optional[str] = Field(
        default="powershell",
        description="powershell, bat, bash, vbs"
    )
    target_os: Optional[str] = Field(
        default="windows",
        description="windows, linux"
    )


class ScriptGenerateResponse(BaseModel):
    title: str
    script_language: str
    script_code: str
    explanation: str
    safety_notes: str


class HandoverChecklistRequest(BaseModel):
    employee_name: str = Field(..., min_length=2, description="Họ và tên nhân viên tiếp nhận")
    employee_code: Optional[str] = Field(default="", description="Mã nhân viên (nếu có)")
    department: str = Field(..., description="Phòng ban tiếp nhận (vd: Kế toán, Nhân sự, Sales...)")
    position: Optional[str] = Field(default="Nhân viên", description="Chức danh công việc")
    pc_type: Optional[str] = Field(default="LAPTOP", description="LAPTOP hoặc DESKTOP")
    hardware_specs: Optional[str] = Field(default="", description="Cấu hình máy bàn giao (CPU, RAM, SSD, Serial/Service Tag)")
    assigned_printers: Optional[List[str]] = Field(default_factory=list, description="Danh sách máy in được kết nối")
    software_packages: Optional[List[str]] = Field(default_factory=list, description="Phần mềm cần cài đặt riêng")


class HandoverChecklistResponse(BaseModel):
    checklist_markdown: str
    checklist_data: Dict[str, Any]
