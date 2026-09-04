"""Service layer for IT Support Ticket Management."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.ticket import Ticket, TicketComment
from app.models.chat import ChatSession
from app.models.user import User
from app.schemas.ticket import (
    TicketCreate,
    TicketStatusUpdate,
    TicketAssignUpdate,
    TicketUpdate,
    TicketCommentCreate,
)

VALID_CATEGORIES = {"NETWORK", "HARDWARE", "SOFTWARE", "ACCOUNT", "GENERAL"}
VALID_PRIORITIES = {"LOW", "MEDIUM", "HIGH", "URGENT"}
VALID_STATUSES = {"OPEN", "IN_PROGRESS", "WAITING", "RESOLVED", "CLOSED"}


class TicketService:
    """Handles business logic, ticket code generation, lifecycle, and permissions."""

    @staticmethod
    def _generate_ticket_code(db: Session) -> str:
        """Generate unique human-readable ticket code (e.g. TK-20260905-A7B2C1)."""
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        for _ in range(5):
            candidate = f"TK-{date_str}-{uuid.uuid4().hex[:6].upper()}"
            existing = db.query(Ticket.id).filter(Ticket.ticket_code == candidate).first()
            if not existing:
                return candidate
        return f"TK-{date_str}-{uuid.uuid4().hex[:8].upper()}"

    @staticmethod
    def create_ticket(db: Session, user: User, ticket_in: TicketCreate) -> Ticket:
        # Validate chat_session_id if provided
        if ticket_in.chat_session_id:
            session = db.query(ChatSession).filter(ChatSession.id == ticket_in.chat_session_id).first()
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Không tìm thấy phiên hội thoại liên kết"
                )
            role_code = user.role.code if user.role else "EMPLOYEE"
            if session.user_id != user.id and role_code not in ["SUPER_ADMIN", "IT_ADMIN"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Bạn không thể liên kết ticket với phiên chat của người khác"
                )

        category = ticket_in.category.upper() if ticket_in.category else "GENERAL"
        if category not in VALID_CATEGORIES:
            category = "GENERAL"

        priority = ticket_in.priority.upper() if ticket_in.priority else "MEDIUM"
        if priority not in VALID_PRIORITIES:
            priority = "MEDIUM"

        ticket = Ticket(
            ticket_code=TicketService._generate_ticket_code(db),
            title=ticket_in.title.strip(),
            description=ticket_in.description.strip(),
            category=category,
            priority=priority,
            status="OPEN",
            created_by=user.id,
            chat_session_id=ticket_in.chat_session_id,
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        return ticket

    @staticmethod
    def get_tickets(
        db: Session,
        user: User,
        ticket_status: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        role_code = user.role.code if user.role else "EMPLOYEE"
        query = db.query(Ticket)

        # Non-admin users only see their own tickets
        if role_code == "EMPLOYEE":
            query = query.filter(Ticket.created_by == user.id)

        if ticket_status:
            query = query.filter(Ticket.status == ticket_status.upper())
        if category:
            query = query.filter(Ticket.category == category.upper())
        if priority:
            query = query.filter(Ticket.priority == priority.upper())

        tickets = query.order_by(Ticket.created_at.desc()).offset(skip).limit(limit).all()

        results = []
        for t in tickets:
            results.append({
                "id": t.id,
                "ticket_code": t.ticket_code,
                "title": t.title,
                "description": t.description,
                "category": t.category,
                "priority": t.priority,
                "status": t.status,
                "created_by": t.created_by,
                "creator_full_name": t.creator.full_name if t.creator else None,
                "creator_email": t.creator.email if t.creator else None,
                "assigned_to": t.assigned_to,
                "assignee_full_name": t.assignee.full_name if t.assignee else None,
                "chat_session_id": t.chat_session_id,
                "resolution_notes": t.resolution_notes,
                "created_at": t.created_at,
                "updated_at": t.updated_at,
                "comment_count": len(t.comments) if t.comments else 0,
            })
        return results

    @staticmethod
    def get_ticket_by_id(db: Session, ticket_id: uuid.UUID, user: User) -> Dict[str, Any]:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy yêu cầu hỗ trợ (Ticket)"
            )

        role_code = user.role.code if user.role else "EMPLOYEE"
        if role_code == "EMPLOYEE" and ticket.created_by != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền truy cập yêu cầu hỗ trợ này"
            )

        # Filter comments: employees cannot see internal IT comments
        filtered_comments = []
        for c in ticket.comments:
            if c.is_internal and role_code not in ["SUPER_ADMIN", "IT_ADMIN"]:
                continue
            filtered_comments.append({
                "id": c.id,
                "ticket_id": c.ticket_id,
                "user_id": c.user_id,
                "user_full_name": c.user.full_name if c.user else None,
                "user_role": c.user.role.name if c.user and c.user.role else None,
                "content": c.content,
                "is_internal": c.is_internal,
                "created_at": c.created_at,
            })

        return {
            "id": ticket.id,
            "ticket_code": ticket.ticket_code,
            "title": ticket.title,
            "description": ticket.description,
            "category": ticket.category,
            "priority": ticket.priority,
            "status": ticket.status,
            "created_by": ticket.created_by,
            "creator_full_name": ticket.creator.full_name if ticket.creator else None,
            "creator_email": ticket.creator.email if ticket.creator else None,
            "assigned_to": ticket.assigned_to,
            "assignee_full_name": ticket.assignee.full_name if ticket.assignee else None,
            "chat_session_id": ticket.chat_session_id,
            "resolution_notes": ticket.resolution_notes,
            "created_at": ticket.created_at,
            "updated_at": ticket.updated_at,
            "comment_count": len(filtered_comments),
            "comments": filtered_comments,
        }

    @staticmethod
    def update_status(
        db: Session,
        ticket_id: uuid.UUID,
        user: User,
        status_in: TicketStatusUpdate
    ) -> Ticket:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy yêu cầu hỗ trợ"
            )

        role_code = user.role.code if user.role else "EMPLOYEE"
        new_status = status_in.status.upper()

        if new_status not in VALID_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Trạng thái không hợp lệ. Cho phép: {', '.join(VALID_STATUSES)}"
            )

        # Employees can only close their own tickets
        if role_code == "EMPLOYEE":
            if ticket.created_by != user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Bạn không có quyền sửa trạng thái ticket này"
                )
            if new_status != "CLOSED":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Nhân viên chỉ có quyền đóng (CLOSED) ticket của mình"
                )
        else:
            # IT Admin / Super Admin
            if status_in.resolution_notes:
                ticket.resolution_notes = status_in.resolution_notes.strip()

        ticket.status = new_status
        ticket.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(ticket)
        return ticket

    @staticmethod
    def assign_ticket(
        db: Session,
        ticket_id: uuid.UUID,
        user: User,
        assign_in: TicketAssignUpdate
    ) -> Ticket:
        role_code = user.role.code if user.role else "EMPLOYEE"
        if role_code not in ["SUPER_ADMIN", "IT_ADMIN"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Chỉ Quản trị viên IT mới có quyền phân công người xử lý"
            )

        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy yêu cầu hỗ trợ"
            )

        if assign_in.assigned_to:
            assignee = db.query(User).filter(User.id == assign_in.assigned_to).first()
            if not assignee:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Không tìm thấy người dùng được chỉ định"
                )
            ticket.assigned_to = assignee.id
            if ticket.status == "OPEN":
                ticket.status = "IN_PROGRESS"
        else:
            ticket.assigned_to = None

        ticket.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(ticket)
        return ticket

    @staticmethod
    def add_comment(
        db: Session,
        ticket_id: uuid.UUID,
        user: User,
        comment_in: TicketCommentCreate
    ) -> TicketComment:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy yêu cầu hỗ trợ"
            )

        role_code = user.role.code if user.role else "EMPLOYEE"

        # Permission check: must be creator or IT/Super admin
        if role_code == "EMPLOYEE" and ticket.created_by != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền bình luận trong ticket này"
            )

        # Internal comments only allowed for IT Admin and Super Admin
        if comment_in.is_internal and role_code not in ["SUPER_ADMIN", "IT_ADMIN"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Nhân viên không được tạo ghi chú nội bộ kỹ thuật"
            )

        comment = TicketComment(
            ticket_id=ticket.id,
            user_id=user.id,
            content=comment_in.content.strip(),
            is_internal=comment_in.is_internal,
        )
        db.add(comment)
        ticket.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(comment)
        return comment

    @staticmethod
    def auto_triage(title: str, description: str) -> Dict[str, Any]:
        """Use local LLM to triage an issue into category, priority, reasoning, and suggested actions."""
        import json
        from app.rag.llm import llm_client

        prompt = (
            f"Bạn là Chuyên viên IT Helpdesk Trưởng (Senior IT Triage Specialist).\n"
            f"Hãy phân tích sự cố CNTT sau đây của nhân viên doanh nghiệp:\n\n"
            f"TIÊU ĐỀ: {title}\n"
            f"MÔ TẢ: {description}\n\n"
            f"YÊU CẦU BẮT BUỘC: Hãy trả lời DUY NHẤT một chuỗi JSON hợp lệ (không kèm lời dẫn) theo cấu trúc chính xác sau:\n"
            f"{{\n"
            f'  "suggested_category": "NETWORK | HARDWARE | SOFTWARE | ACCOUNT | GENERAL",\n'
            f'  "suggested_priority": "LOW | MEDIUM | HIGH | URGENT",\n'
            f'  "reasoning": "Giải thích ngắn gọn súc tích lý do phân loại trong 1-2 câu tiếng Việt",\n'
            f'  "suggested_initial_actions": [\n'
            f'    "Bước 1 cụ thể nhân viên có thể kiểm tra trước",\n'
            f'    "Bước 2 cụ thể..."\n'
            f'  ]\n'
            f"}}"
        )

        try:
            res = llm_client.generate(prompt=prompt, system_prompt="Bạn là chuyên gia phân loại sự cố IT nội bộ. Chỉ trả về JSON.")
            raw_text = res.get("response", "").strip()
            if "```" in raw_text:
                parts = raw_text.split("```")
                if len(parts) > 1:
                    raw_text = parts[1]
                    if raw_text.startswith("json"):
                        raw_text = raw_text[4:]
                    raw_text = raw_text.strip()
            start = raw_text.find("{")
            end = raw_text.rfind("}") + 1
            if start != -1 and end != 0:
                parsed = json.loads(raw_text[start:end])
                cat = str(parsed.get("suggested_category", "GENERAL")).upper()
                pri = str(parsed.get("suggested_priority", "MEDIUM")).upper()
                if cat not in VALID_CATEGORIES:
                    cat = "GENERAL"
                if pri not in VALID_PRIORITIES:
                    pri = "MEDIUM"
                return {
                    "suggested_category": cat,
                    "suggested_priority": pri,
                    "reasoning": parsed.get("reasoning", "Phân tích tự động dựa trên mô tả sự cố."),
                    "suggested_initial_actions": parsed.get("suggested_initial_actions", [
                        "Kiểm tra lại kết nối vật lý và cáp nguồn/mạng",
                        "Khởi động lại ứng dụng hoặc thiết bị"
                    ]),
                }
        except Exception:
            pass

        # Smart rule-based fallback
        text_lower = f"{title} {description}".lower()
        cat = "GENERAL"
        pri = "MEDIUM"
        if any(w in text_lower for w in ["mạng", "wifi", "vpn", "internet", "dns", "ping", "lan"]):
            cat = "NETWORK"
            pri = "HIGH" if ("mất" in text_lower or "không thể" in text_lower or "chậm" in text_lower) else "MEDIUM"
        elif any(w in text_lower for w in ["máy in", "chuột", "bàn phím", "màn hình", "ram", "ổ cứng", "laptop", "pc"]):
            cat = "HARDWARE"
        elif any(w in text_lower for w in ["mật khẩu", "tài khoản", "login", "đăng nhập", "khóa tài khoản", "quên pass"]):
            cat = "ACCOUNT"
            pri = "HIGH"
        elif any(w in text_lower for w in ["phần mềm", "office", "excel", "cài đặt", "lỗi app", "outlook", "teams"]):
            cat = "SOFTWARE"

        return {
            "suggested_category": cat,
            "suggested_priority": pri,
            "reasoning": "Hệ thống AI tự động phát hiện từ khóa kỹ thuật trọng tâm để đề xuất danh mục tối ưu.",
            "suggested_initial_actions": [
                "Kiểm tra lại kết nối và nguồn thiết bị",
                "Chụp lại ảnh màn hình thông báo lỗi để IT Admin tiện xử lý"
            ]
        }


ticket_service = TicketService()
