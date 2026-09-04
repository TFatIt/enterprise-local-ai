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


dashboard_service = DashboardService()
