"""Unit tests for SQLAlchemy models, relationships, and seeding logic."""

import sys
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.db.base import Base
import app.models  # noqa: F401
from app.models.role import Role
from app.models.department import Department
from app.models.user import User
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.chat import ChatSession, ChatMessage
from app.models.ticket import Ticket, TicketComment
from app.models.audit_log import AuditLog
from app.db.seed import seed_database
from app.core.security import verify_password


@pytest.fixture
def test_db():
    """Create an in-memory test database and session."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_database_seeding(test_db):
    """Test that seed_database creates default roles, departments, and users."""
    seed_database(test_db)

    # Verify Roles
    roles = test_db.query(Role).all()
    role_codes = {r.code for r in roles}
    assert "SUPER_ADMIN" in role_codes
    assert "IT_ADMIN" in role_codes
    assert "EMPLOYEE" in role_codes

    # Verify Departments
    depts = test_db.query(Department).all()
    dept_codes = {d.code for d in depts}
    assert "IT" in dept_codes
    assert "HR" in dept_codes
    assert "FINANCE" in dept_codes

    # Verify Users & Password Hashing
    admin = test_db.query(User).filter(User.email == "admin@enterprise.local").first()
    assert admin is not None
    assert admin.username == "superadmin"
    assert admin.role.code == "SUPER_ADMIN"
    assert admin.department.code == "IT"
    assert verify_password("Admin@123456", admin.hashed_password) is True


def test_document_and_chunks_cascade(test_db):
    """Test document creation and chunk cascade deletion."""
    seed_database(test_db)
    admin = test_db.query(User).filter(User.email == "admin@enterprise.local").first()
    it_dept = test_db.query(Department).filter(Department.code == "IT").first()

    # Create Document
    doc = Document(
        title="Active Directory Troubleshooting Guide",
        file_name="ad_guide.pdf",
        stored_file_name="ad_guide_uuid123.pdf",
        file_path="/uploads/ad_guide_uuid123.pdf",
        file_type="PDF",
        file_size=102400,
        department_id=it_dept.id,
        uploaded_by=admin.id,
        status="INDEXED",
        total_chunks=2,
    )
    test_db.add(doc)
    test_db.commit()

    # Add Chunks
    chunk1 = DocumentChunk(
        document_id=doc.id,
        chunk_index=0,
        content="Chunk 1 content regarding DNS settings.",
        metadata_json={"page": 1},
        chroma_id="chroma-chunk-1",
    )
    chunk2 = DocumentChunk(
        document_id=doc.id,
        chunk_index=1,
        content="Chunk 2 content regarding Kerberos time synchronization.",
        metadata_json={"page": 2},
        chroma_id="chroma-chunk-2",
    )
    test_db.add_all([chunk1, chunk2])
    test_db.commit()

    assert len(doc.chunks) == 2

    # Delete Document and verify chunks cascade
    test_db.delete(doc)
    test_db.commit()
    remaining_chunks = test_db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).all()
    assert len(remaining_chunks) == 0


def test_chat_session_and_messages(test_db):
    """Test chat session, messages, and sources JSON storage."""
    seed_database(test_db)
    user = test_db.query(User).filter(User.email == "employee@enterprise.local").first()

    session = ChatSession(user_id=user.id, title="Troubleshooting VPN issue")
    test_db.add(session)
    test_db.commit()

    msg_user = ChatMessage(
        session_id=session.id,
        sender_type="USER",
        content="How do I connect to VPN?",
        sources=[],
    )
    msg_ai = ChatMessage(
        session_id=session.id,
        sender_type="ASSISTANT",
        content="You need to use OpenVPN with your user profile.",
        sources=[{"file": "vpn_guide.pdf", "page": 3, "score": 0.91}],
        response_time_ms=1200,
    )
    test_db.add_all([msg_user, msg_ai])
    test_db.commit()

    assert len(session.messages) == 2
    assert session.messages[1].sources[0]["file"] == "vpn_guide.pdf"


def test_ticket_creation_and_comments(test_db):
    """Test ticket creation, assignment, and comments."""
    seed_database(test_db)
    employee = test_db.query(User).filter(User.email == "employee@enterprise.local").first()
    it_admin = test_db.query(User).filter(User.email == "it.admin@enterprise.local").first()

    ticket = Ticket(
        ticket_code="IT-2026-0001",
        title="Cannot join domain controller",
        description="Getting error: Domain controller could not be contacted.",
        category="NETWORK",
        priority="HIGH",
        status="OPEN",
        created_by=employee.id,
        assigned_to=it_admin.id,
    )
    test_db.add(ticket)
    test_db.commit()

    comment = TicketComment(
        ticket_id=ticket.id,
        user_id=it_admin.id,
        content="Please verify if your IPv4 DNS is set to 192.168.1.10.",
        is_internal=False,
    )
    test_db.add(comment)
    test_db.commit()

    assert ticket.creator.email == "employee@enterprise.local"
    assert ticket.assignee.email == "it.admin@enterprise.local"
    assert len(ticket.comments) == 1
