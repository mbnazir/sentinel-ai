from datetime import date, datetime
from typing import Any

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.base import Base


class OrganizationModel(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    organization_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id"))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ConnectorModel(Base):
    __tablename__ = "connectors"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    connector_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="inactive")
    configuration: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ConnectorRunModel(Base):
    __tablename__ = "connector_runs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    connector_id: Mapped[int] = mapped_column(ForeignKey("connectors.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    records_imported: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)


class ScanModel(Base):
    __tablename__ = "scans"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    connector_run_id: Mapped[int | None] = mapped_column(ForeignKey("connector_runs.id"))
    scan_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RiskAssessmentModel(Base):
    __tablename__ = "risk_assessments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    scan_id: Mapped[int] = mapped_column(ForeignKey("scans.id"), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(100), nullable=False)
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(50), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RuleResultModel(Base):
    __tablename__ = "rule_results"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    risk_assessment_id: Mapped[int] = mapped_column(ForeignKey("risk_assessments.id"), nullable=False)
    rule_id: Mapped[str] = mapped_column(String(100), nullable=False)
    rule_name: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EvidenceModel(Base):
    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    rule_result_id: Mapped[int] = mapped_column(ForeignKey("rule_results.id"), nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    organization_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id"))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ExternalSourceModel(Base):
    __tablename__ = "external_sources"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    connector_id: Mapped[int] = mapped_column(ForeignKey("connectors.id"), nullable=False)
    source_system: Mapped[str] = mapped_column(String(50), nullable=False)
    external_id: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class NormalizedLoginSessionModel(Base):
    __tablename__ = "normalized_login_sessions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    connector_id: Mapped[int] = mapped_column(ForeignKey("connectors.id"), nullable=False)
    connector_run_id: Mapped[int | None] = mapped_column(ForeignKey("connector_runs.id"))
    external_id: Mapped[str] = mapped_column(String(100), nullable=False)
    agent_external_id: Mapped[str | None] = mapped_column(String(100))
    supervisor_external_id: Mapped[str | None] = mapped_column(String(100))
    shift_date: Mapped[date | None] = mapped_column(Date)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str | None] = mapped_column(String(100))
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class NormalizedActivityModel(Base):
    __tablename__ = "normalized_activities"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    connector_id: Mapped[int] = mapped_column(ForeignKey("connectors.id"), nullable=False)
    connector_run_id: Mapped[int | None] = mapped_column(ForeignKey("connector_runs.id"))
    login_session_id: Mapped[int] = mapped_column(ForeignKey("normalized_login_sessions.id"), nullable=False)
    external_id: Mapped[str] = mapped_column(String(100), nullable=False)
    login_session_external_id: Mapped[str] = mapped_column(String(100), nullable=False)
    agent_external_id: Mapped[str | None] = mapped_column(String(100))
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    source_code: Mapped[int | None] = mapped_column(Integer)
    activity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    activity_type_external_id: Mapped[str | None] = mapped_column(String(100))
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    inactivity_seconds: Mapped[int] = mapped_column(Integer, default=0)
    comment: Mapped[str | None] = mapped_column(Text)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))



class ExternalSourceModel(Base):
    __tablename__ = "external_sources"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    connector_id: Mapped[int] = mapped_column(ForeignKey("connectors.id"), nullable=False)
    source_system: Mapped[str] = mapped_column(String(50), nullable=False)
    external_id: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class NormalizedLoginSessionModel(Base):
    __tablename__ = "normalized_login_sessions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    connector_id: Mapped[int] = mapped_column(ForeignKey("connectors.id"), nullable=False)
    connector_run_id: Mapped[int | None] = mapped_column(ForeignKey("connector_runs.id"))
    external_id: Mapped[str] = mapped_column(String(100), nullable=False)
    agent_external_id: Mapped[str | None] = mapped_column(String(100))
    supervisor_external_id: Mapped[str | None] = mapped_column(String(100))
    shift_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str | None] = mapped_column(String(100))
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class NormalizedActivityModel(Base):
    __tablename__ = "normalized_activities"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    connector_id: Mapped[int] = mapped_column(ForeignKey("connectors.id"), nullable=False)
    connector_run_id: Mapped[int | None] = mapped_column(ForeignKey("connector_runs.id"))
    login_session_id: Mapped[int] = mapped_column(ForeignKey("normalized_login_sessions.id"), nullable=False)
    external_id: Mapped[str] = mapped_column(String(100), nullable=False)
    login_session_external_id: Mapped[str] = mapped_column(String(100), nullable=False)
    agent_external_id: Mapped[str | None] = mapped_column(String(100))
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    source_code: Mapped[int | None] = mapped_column(Integer)
    activity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    activity_type_external_id: Mapped[str | None] = mapped_column(String(100))
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    inactivity_seconds: Mapped[int] = mapped_column(Integer, default=0)
    comment: Mapped[str | None] = mapped_column(Text)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
