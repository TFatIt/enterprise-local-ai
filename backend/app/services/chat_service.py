"""Service layer for Chat Sessions, AI Messages, and Dynamic Intent Routing."""

import uuid
import json
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.chat import ChatSession, ChatMessage
from app.models.user import User
from app.schemas.chat import ChatSessionCreate, ChatSessionUpdate, ChatMessageCreate
from app.rag.pipeline import rag_pipeline
from app.rag.intent_classifier import intent_classifier
from app.rag.conversation_memory import conversation_memory
from app.services.audit_service import audit_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class ChatService:
    """Handles business logic for chat sessions, messages, and RAG integration."""

    @staticmethod
    def create_session(db: Session, user: User, session_in: ChatSessionCreate) -> ChatSession:
        title = session_in.title.strip() if session_in.title and session_in.title.strip() else "Cuộc hội thoại mới"
        session = ChatSession(
            user_id=user.id,
            title=title,
            is_active=True,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def get_user_sessions(
        db: Session,
        user: User,
        skip: int = 0,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        query = db.query(ChatSession).filter(ChatSession.user_id == user.id)
        sessions = query.order_by(ChatSession.updated_at.desc()).offset(skip).limit(limit).all()

        results = []
        for s in sessions:
            results.append({
                "id": s.id,
                "user_id": s.user_id,
                "title": s.title,
                "is_active": s.is_active,
                "created_at": s.created_at,
                "updated_at": s.updated_at,
                "message_count": len(s.messages) if s.messages else 0,
            })
        return results

    @staticmethod
    def get_session_by_id(db: Session, session_id: uuid.UUID, user: User) -> ChatSession:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy phiên hội thoại"
            )
        role_name = user.role.name if user.role else ""
        if session.user_id != user.id and role_name != "SUPER_ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền truy cập phiên hội thoại này"
            )
        return session

    @staticmethod
    def update_session(
        db: Session,
        session_id: uuid.UUID,
        user: User,
        update_in: ChatSessionUpdate
    ) -> ChatSession:
        session = ChatService.get_session_by_id(db, session_id, user)
        if update_in.title is not None:
            session.title = update_in.title.strip()
        if update_in.is_active is not None:
            session.is_active = update_in.is_active

        session.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def delete_session(db: Session, session_id: uuid.UUID, user: User) -> None:
        session = ChatService.get_session_by_id(db, session_id, user)
        db.delete(session)
        db.commit()

    @staticmethod
    def send_message(
        db: Session,
        session_id: uuid.UUID,
        user: User,
        message_in: ChatMessageCreate
    ) -> Dict[str, Any]:
        session = ChatService.get_session_by_id(db, session_id, user)

        if not session.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phiên hội thoại này đã được đóng."
            )

        content = message_in.content.strip()

        # Auto-title session if it has default title
        if session.title == "Cuộc hội thoại mới" or not session.title:
            cleaned_title = content.replace("\n", " ")
            session.title = cleaned_title[:40] + ("..." if len(cleaned_title) > 40 else "")

        # Extract recent conversation history before saving current message
        history = conversation_memory.get_recent_history(session.messages, max_messages=6)

        # 1. Save user question
        user_msg = ChatMessage(
            session_id=session.id,
            sender_type="USER",
            content=content,
            sources=[],
        )
        db.add(user_msg)
        db.commit()

        # 2. Dynamic Intent Classification
        intent_result = intent_classifier.classify(content)
        logger.info(f"Chat intent classified: {intent_result.intent} (is_enterprise={intent_result.is_enterprise_query}, conf={intent_result.confidence})")

        # 3. Execution Routing: General Chat vs Enterprise Knowledge Base RAG
        if not intent_result.is_enterprise_query:
            # Bypass RAG vector retrieval entirely
            ai_response = rag_pipeline.chat_general(
                question=content,
                history=history
            )
        else:
            # Execute Enterprise RAG with ACL and contextual query reformulation
            ai_response = rag_pipeline.ask(
                question=content,
                department_id=None,
                top_k=settings.RAG_TOP_K,
                user=user,
                history=history
            )

        audit_service.log_event(
            db=db,
            action="CHAT_QUERY",
            resource="CHAT",
            user_id=user.id,
            details={
                "query": content[:200],
                "intent": intent_result.intent,
                "is_enterprise": intent_result.is_enterprise_query,
                "source_count": len(ai_response.get("sources", []))
            }
        )

        # 4. Save assistant response
        assistant_msg = ChatMessage(
            session_id=session.id,
            sender_type="ASSISTANT",
            content=ai_response.get("answer", ""),
            sources=ai_response.get("sources", []),
            response_time_ms=ai_response.get("response_time_ms", 0),
        )
        db.add(assistant_msg)

        session.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(assistant_msg)

        return {
            "id": assistant_msg.id,
            "session_id": assistant_msg.session_id,
            "sender_type": assistant_msg.sender_type,
            "content": assistant_msg.content,
            "sources": assistant_msg.sources,
            "suggest_ticket": ai_response.get("suggest_ticket", False),
            "response_time_ms": assistant_msg.response_time_ms,
            "created_at": assistant_msg.created_at,
        }

    @staticmethod
    def send_message_stream(
        db: Session,
        session_id: uuid.UUID,
        user: User,
        message_in: ChatMessageCreate
    ):
        """Send message and yield Server-Sent Events (SSE) chunks, persisting result upon completion."""
        session = ChatService.get_session_by_id(db, session_id, user)

        if not session.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phiên hội thoại này đã được đóng."
            )

        content = message_in.content.strip()

        # Auto-title session if default
        if session.title == "Cuộc hội thoại mới" or not session.title:
            cleaned_title = content.replace("\n", " ")
            session.title = cleaned_title[:40] + ("..." if len(cleaned_title) > 40 else "")

        # Extract recent conversation history before saving current message
        history = conversation_memory.get_recent_history(session.messages, max_messages=6)

        # 1. Save user question
        user_msg = ChatMessage(
            session_id=session.id,
            sender_type="USER",
            content=content,
            sources=[],
        )
        db.add(user_msg)
        db.commit()

        # 2. Dynamic Intent Classification
        intent_result = intent_classifier.classify(content)
        logger.info(f"Stream intent classified: {intent_result.intent} (is_enterprise={intent_result.is_enterprise_query})")

        db_bind = db.get_bind()
        session_id_val = session.id
        user_id_val = user.id

        # 3. Generator yielding SSE lines and persisting assistant response on 'done'
        def sse_generator():
            full_answer = ""
            sources = []
            response_time_ms = 0

            # Select stream source
            if not intent_result.is_enterprise_query:
                stream_iter = rag_pipeline.chat_general_stream(
                    question=content,
                    history=history
                )
            else:
                stream_iter = rag_pipeline.ask_stream(
                    question=content,
                    department_id=None,
                    top_k=settings.RAG_TOP_K,
                    user=user,
                    history=history
                )

            for sse_line in stream_iter:
                yield sse_line
                if sse_line.startswith("data: "):
                    try:
                        data = json.loads(sse_line[6:].strip())
                        if data.get("type") == "done":
                            full_answer = data.get("full_answer", "")
                            sources = data.get("sources", [])
                            response_time_ms = data.get("response_time_ms", 0)
                    except Exception:
                        pass

            # 4. Persist assistant message in DB using dedicated session
            try:
                from sqlalchemy.orm import sessionmaker
                DedicatedSession = sessionmaker(autocommit=False, autoflush=False, bind=db_bind)
                with DedicatedSession() as write_db:
                    assistant_msg = ChatMessage(
                        session_id=session_id_val,
                        sender_type="ASSISTANT",
                        content=full_answer,
                        sources=sources,
                        response_time_ms=response_time_ms,
                    )
                    write_db.add(assistant_msg)
                    db_sess = write_db.query(ChatSession).filter(ChatSession.id == session_id_val).first()
                    if db_sess:
                        db_sess.updated_at = datetime.now(timezone.utc)
                    write_db.commit()

                    # Audit log for stream response
                    audit_service.log_event(
                        db=write_db,
                        action="CHAT_STREAM_QUERY",
                        resource="CHAT",
                        user_id=user_id_val,
                        details={
                            "query": content[:200],
                            "intent": intent_result.intent,
                            "is_enterprise": intent_result.is_enterprise_query,
                            "source_count": len(sources)
                        }
                    )
            except Exception as e:
                logger.error(f"Failed to persist assistant message in stream: {e}")

        return sse_generator()

    @staticmethod
    def submit_feedback(
        db: Session,
        session_id: uuid.UUID,
        message_id: uuid.UUID,
        user: User,
        rating: int,
        comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """Record user feedback (rating 1-5 or thumbs up/down) for an assistant message."""
        # Validate session ownership
        ChatService.get_session_by_id(db, session_id, user)

        message = db.query(ChatMessage).filter(
            ChatMessage.id == message_id,
            ChatMessage.session_id == session_id
        ).first()

        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy tin nhắn cần gửi phản hồi"
            )

        # Store feedback in audit log and message sources metadata
        feedback_data = {
            "rating": rating,
            "comment": comment or "",
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "user_id": str(user.id)
        }

        # Safely attach to sources if list
        current_sources = list(message.sources or [])
        # Check if feedback item already exists, update or append
        updated = False
        for item in current_sources:
            if isinstance(item, dict) and "_feedback" in item:
                item["_feedback"] = feedback_data
                updated = True
                break
        if not updated:
            current_sources.append({"_feedback": feedback_data})

        message.sources = current_sources
        db.commit()

        audit_service.log_event(
            db=db,
            action="MESSAGE_FEEDBACK",
            resource="CHAT",
            user_id=user.id,
            details={
                "message_id": str(message_id),
                "rating": rating,
                "comment": comment or ""
            }
        )

        return {
            "status": "success",
            "message_id": str(message_id),
            "feedback": feedback_data
        }


chat_service = ChatService()
