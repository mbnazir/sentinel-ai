from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.base import Base


class NormalizedLoginSessionModel(Base):
    __tablename__ = "normalized_login_sessions"
    __table_args__ = (
        UniqueConstraint("organization_id", "external_id", name="uq_normalized_session_org_external"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(100), nullable=False)
    connector_type: Mapped[str] = mapped_column(String(50), nullable=False)
    external_id: Mapped[str] = mapped_column(String(100), nullable=False)
    agent_external_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    supervisor_external_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    shift_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str | None] = mapped_column(String(100), nullable=True)


class NormalizedActivityModel(Base):
    __tablename__ = "normalized_activities"
    __table_args__ = (
        UniqueConstraint("organization_id", "external_id", name="uq_normalized_activity_org_external"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(100), nullable=False)
    connector_type: Mapped[str] = mapped_column(String(50), nullable=False)
    external_id: Mapped[str] = mapped_column(String(100), nullable=False)
    login_session_external_id: Mapped[str] = mapped_column(String(100), nullable=False)
    agent_external_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    activity_type: Mapped[str] = mapped_column(String(255), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
