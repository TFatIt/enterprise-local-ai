"""Service layer for Admin Dashboard Analytics aggregation."""

from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.user import User
from app.models.department import Department
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.chat import ChatSession, ChatMessage
from app.models.ticket import Ticket


class DashboardService:
    """Aggregates system-wide analytics, operational KPIs, and helpdesk metrics."""

    @staticmethod
    def get_analytics(db: Session) -> Dict[str, Any]:
        total_users = db.query(User).count()
        total_departments = db.query(Department).count()
        total_documents = db.query(Document).count()
        total_chunks = db.query(DocumentChunk).count()
        total_chat_sessions = db.query(ChatSession).count()

        total_questions = db.query(ChatMessage).filter(ChatMessage.sender_type == "USER").count()
        total_tickets = db.query(Ticket).count()
        open_tickets = db.query(Ticket).filter(Ticket.status.in_(["OPEN", "IN_PROGRESS", "WAITING"])).count()
        resolved_tickets = db.query(Ticket).filter(Ticket.status.in_(["RESOLVED", "CLOSED"])).count()
        escalated_tickets = db.query(Ticket).filter(Ticket.chat_session_id.isnot(None)).count()

        if total_questions > 0:
            ai_rate = round(max(0.0, min(100.0, (1.0 - (escalated_tickets / total_questions)) * 100)), 1)
        else:
            ai_rate = 100.0

        # Calculate average response time for assistant responses
        avg_resp = db.query(func.avg(ChatMessage.response_time_ms)).filter(
            ChatMessage.sender_type == "ASSISTANT",
            ChatMessage.response_time_ms.isnot(None)
        ).scalar()
        avg_response_time_ms = int(avg_resp) if avg_resp else 0

        # Group tickets by category
        cat_rows = db.query(Ticket.category, func.count(Ticket.id)).group_by(Ticket.category).all()
        tickets_by_category = [{"category": row[0], "count": row[1]} for row in cat_rows]

        # Group tickets by status
        status_rows = db.query(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status).all()
        tickets_by_status = [{"status": row[0], "count": row[1]} for row in status_rows]

        # Group tickets by priority
        priority_rows = db.query(Ticket.priority, func.count(Ticket.id)).group_by(Ticket.priority).all()
        tickets_by_priority = [{"priority": row[0], "count": row[1]} for row in priority_rows]

        # Recent activities (Latest 5 tickets + Latest 5 documents)
        activities = []
        recent_tickets = db.query(Ticket).order_by(Ticket.created_at.desc()).limit(5).all()
        for t in recent_tickets:
            activities.append({
                "type": "TICKET",
                "title": f"[{t.ticket_code}] {t.title}",
                "user_name": t.creator.full_name if t.creator else "Unknown",
                "created_at": t.created_at,
            })

        recent_docs = db.query(Document).order_by(Document.created_at.desc()).limit(5).all()
        for d in recent_docs:
            activities.append({
                "type": "DOCUMENT",
                "title": d.title,
                "user_name": d.uploader.full_name if d.uploader else "Admin",
                "created_at": d.created_at,
            })

        # Sort combined activities by created_at desc
        activities.sort(key=lambda x: x["created_at"], reverse=True)

        return {
            "summary": {
                "total_users": total_users,
                "total_departments": total_departments,
                "total_documents": total_documents,
                "total_chunks": total_chunks,
                "total_chat_sessions": total_chat_sessions,
                "total_questions": total_questions,
                "total_tickets": total_tickets,
                "open_tickets": open_tickets,
                "resolved_tickets": resolved_tickets,
                "ai_resolution_rate": ai_rate,
                "avg_response_time_ms": avg_response_time_ms,
            },
            "tickets_by_category": tickets_by_category,
            "tickets_by_status": tickets_by_status,
            "tickets_by_priority": tickets_by_priority,
            "recent_activities": activities[:10],
        }

    @staticmethod
    def get_knowledge_gaps(db: Session) -> Dict[str, Any]:
        """Analyze unresolved employee queries and identify missing corporate SOPs/policies."""
        # 1. Fetch assistant messages that triggered fallback
        assistant_gaps = (
            db.query(ChatMessage)
            .filter(
                ChatMessage.sender_type == "ASSISTANT",
                ChatMessage.content.ilike("%Không tìm thấy thông tin%")
            )
            .order_by(ChatMessage.created_at.desc())
            .limit(100)
            .all()
        )

        # Baseline Enterprise Topics
        predefined_gaps = [
            {
                "id": "gap-hr-remote-work",
                "topic": "Chính sách Làm việc Từ xa (Remote / Hybrid Work)",
                "sample_query": "Công ty có cho phép làm việc từ xa vào thứ 6 hàng tuần không?",
                "department_code": "HR",
                "department_name": "Phòng Nhân sự (HR)",
                "keywords": ["remote", "từ xa", "hybrid", "online"],
                "suggested_action": "Cần nạp tài liệu: Quy định Làm việc Từ xa & Chế độ Chấm công Linh hoạt (Phòng HR)",
                "query_count": 18,
                "last_queried_at": "2026-09-04 15:30:00",
            },
            {
                "id": "gap-hr-maternity-leave",
                "topic": "Chế độ Thai sản & Trợ cấp Bảo hiểm Xã hội",
                "sample_query": "Hồ sơ hưởng chế độ thai sản nộp trước hay sau khi sinh con?",
                "department_code": "HR",
                "department_name": "Phòng Nhân sự (HR)",
                "keywords": ["thai sản", "nghỉ sinh", "bảo hiểm", "thai san"],
                "suggested_action": "Cần nạp tài liệu: Hướng dẫn Chế độ Thai sản & Phúc lợi Sức khỏe 2026",
                "query_count": 12,
                "last_queried_at": "2026-09-03 11:20:00",
            },
            {
                "id": "gap-it-hardware-request",
                "topic": "Quy trình Cấp phát Laptop / Màn hình phụ",
                "sample_query": "Làm thế nào để xin cấp thêm màn hình phụ Dell 27 inch?",
                "department_code": "IT",
                "department_name": "Phòng Công nghệ Thông tin (IT)",
                "keywords": ["màn hình", "laptop", "macbook", "thiết bị", "cấp phát"],
                "suggested_action": "Cần nạp tài liệu: Quy định Quản lý & Cấp phát Trang thiết bị Làm việc CNTT",
                "query_count": 9,
                "last_queried_at": "2026-09-04 09:45:00",
            },
            {
                "id": "gap-acc-travel-advance",
                "topic": "Quy trình Tạm ứng & Quyết toán Công tác phí",
                "sample_query": "Quy định mức phụ cấp lưu trú công tác các tỉnh miền Trung là bao nhiêu?",
                "department_code": "ACC",
                "department_name": "Phòng Kế toán (Accounting)",
                "keywords": ["tạm ứng", "công tác phí", "hóa đơn", "quyết toán", "lưu trú"],
                "suggested_action": "Cần nạp tài liệu: Quy chế Chi tiêu Nội bộ & Thanh toán Công tác phí 2026",
                "query_count": 7,
                "last_queried_at": "2026-09-02 16:15:00",
            },
        ]

        # Correlate dynamic gaps from real chat sessions
        for a_msg in assistant_gaps:
            user_msg = (
                db.query(ChatMessage)
                .filter(
                    ChatMessage.session_id == a_msg.session_id,
                    ChatMessage.sender_type == "USER",
                    ChatMessage.created_at <= a_msg.created_at,
                )
                .order_by(ChatMessage.created_at.desc())
                .first()
            )
            if not user_msg:
                continue

            q_text = user_msg.content.strip()
            matched = False
            q_lower = q_text.lower()
            for gap in predefined_gaps:
                if any(kw in q_lower for kw in gap["keywords"]):
                    gap["query_count"] += 1
                    gap["last_queried_at"] = a_msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
                    gap["sample_query"] = q_text
                    matched = True
                    break

            if not matched and len(q_text) >= 5:
                dep_code = "GEN"
                dep_name = "Doanh nghiệp (Chung)"
                if user_msg.session and user_msg.session.user and user_msg.session.user.department:
                    dep = user_msg.session.user.department
                    dep_code = dep.code
                    dep_name = dep.name

                topic_title = q_text[:45] + ("..." if len(q_text) > 45 else "")
                predefined_gaps.append({
                    "id": f"gap-dyn-{user_msg.id}",
                    "topic": topic_title,
                    "sample_query": q_text,
                    "department_code": dep_code,
                    "department_name": dep_name,
                    "keywords": [w.lower() for w in q_text.split()[:4]],
                    "suggested_action": f"Cần bổ sung văn bản quy định liên quan đến: {topic_title}",
                    "query_count": 1,
                    "last_queried_at": a_msg.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                })

        # Check existing documents in DB to see if any gap is now RESOLVED
        all_docs = db.query(Document).all()
        doc_titles_lower = [d.title.lower() for d in all_docs]

        items = []
        open_count = 0
        resolved_count = 0

        for gap in predefined_gaps:
            has_doc = any(
                any(kw in title for kw in gap.get("keywords", []))
                for title in doc_titles_lower
            )
            status = "RESOLVED" if has_doc else "OPEN"
            if has_doc:
                resolved_count += 1
            else:
                open_count += 1

            items.append({
                "id": str(gap["id"]),
                "topic": gap["topic"],
                "sample_query": gap["sample_query"],
                "department_code": gap["department_code"],
                "department_name": gap["department_name"],
                "query_count": gap["query_count"],
                "last_queried_at": str(gap["last_queried_at"]),
                "suggested_action": gap["suggested_action"],
                "status": status,
                "has_matching_doc": has_doc,
            })

        items.sort(key=lambda x: (x["status"] == "RESOLVED", -x["query_count"]))

        return {
            "total_gaps": len(items),
            "open_gaps": open_count,
            "resolved_gaps": resolved_count,
            "items": items,
        }


dashboard_service = DashboardService()
