from datetime import datetime
from typing import Any
from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.infrastructure.persistence.base import Base

class InvestigationCaseModel(Base):
    __tablename__ = "investigation_cases"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    case_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    organization_id: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(100), nullable=False)
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    priority: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    assigned_to: Mapped[str | None] = mapped_column(String(100))
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class InvestigationEvidenceLinkModel(Base):
    __tablename__ = "investigation_evidence_links"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    case_id: Mapped[str] = mapped_column(String(64), ForeignKey("investigation_cases.case_id"), nullable=False)
    evidence_id: Mapped[str] = mapped_column(String(255), nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(100), nullable=False)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)

class InvestigationCommentModel(Base):
    __tablename__ = "investigation_comments"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    case_id: Mapped[str] = mapped_column(String(64), ForeignKey("investigation_cases.case_id"), nullable=False)
    author_id: Mapped[str] = mapped_column(String(100), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class InvestigationNarrativeModel(Base):
    __tablename__ = "investigation_narratives"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    case_id: Mapped[str] = mapped_column(String(64), ForeignKey("investigation_cases.case_id"), nullable=False)
    executive_summary: Mapped[str] = mapped_column(Text, nullable=False)
    key_findings: Mapped[list[Any]] = mapped_column(JSON, nullable=False)
    evidence_summary: Mapped[list[Any]] = mapped_column(JSON, nullable=False)
    recommended_next_steps: Mapped[list[Any]] = mapped_column(JSON, nullable=False)
    limitations: Mapped[list[Any]] = mapped_column(JSON, nullable=False)
    raw_model_output: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
