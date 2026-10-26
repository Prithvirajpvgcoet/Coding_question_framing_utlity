"""
SQLAlchemy ORM models.
"""
import datetime
import uuid
from typing import Optional

from sqlalchemy import String, Integer, Float, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

def utcnow():
    return datetime.datetime.now(datetime.timezone.utc)

class Base(DeclarativeBase):
    pass

class Client(Base):
    __tablename__ = "clients"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    api_key_hash: Mapped[str] = mapped_column(String, nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, default={})
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class QuestionBank(Base):
    __tablename__ = "question_banks"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    imocha_bank_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class Question(Base):
    __tablename__ = "questions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id"), nullable=False)
    bank_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("question_banks.id"), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String, nullable=False, default="PROCESSING")
    state: Mapped[dict] = mapped_column(JSONB, default={})
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class Feedback(Base):
    __tablename__ = "feedbacks"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id"), nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)  # APPROVE, REJECT
    feedback_text: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class QuestionVersion(Base):
    __tablename__ = "question_versions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    triggered_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    re_entry_agent: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    state_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    state_diff: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class AgentRun(Base):
    __tablename__ = "agent_runs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    question_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("questions.id"), nullable=True)
    agent_name: Mapped[str] = mapped_column(String, nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)
    prompt_hash: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    input_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cost_usd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    internal_step: Mapped[bool] = mapped_column(Boolean, default=False)
    error_detail: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UploadJob(Base):
    __tablename__ = "upload_jobs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id"), nullable=False)
    question_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("questions.id"), nullable=False)
    bank_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="QUEUED")  # QUEUED, IN_PROGRESS, COMPLETED, FAILED
    queue_position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    payload_json: Mapped[dict] = mapped_column(JSONB, default={})
    steps_log: Mapped[list] = mapped_column(JSONB, default=[])
    error: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    started_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class ReferenceDocument(Base):
    __tablename__ = "reference_documents"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    doc_type: Mapped[str] = mapped_column(String, nullable=False, default="DOMAIN_SCENARIO")
    format: Mapped[str] = mapped_column(String, nullable=False, default="json")
    topic: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    subtopic: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    difficulty: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    domain: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    tags: Mapped[list] = mapped_column(JSONB, default=[])
    raw_content: Mapped[str] = mapped_column(String, nullable=False)
    structured_data: Mapped[dict] = mapped_column(JSONB, default={})
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
