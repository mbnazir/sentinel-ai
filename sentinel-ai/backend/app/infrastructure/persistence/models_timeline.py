from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.base import Base


class NormalizedTimelineActivityModel(Base):
    """Read model for normalized timeline activity data.

    This table is intentionally connector-neutral. Quartz, CSV, and future connectors
    should normalize into this shape before timeline retrieval.
    """

    __tablename__ = "normalized_timeline_activities"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(100), nullable=False)
    external_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    login_session_external_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    agent_external_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    data_source_id: Mapped[int] = mapped_column(Integer, nullable=False)
    source_label: Mapped[str] = mapped_column(String(50), nullable=False)
    activity_type_id: Mapped[int] = mapped_column(Integer, nullable=False)
    activity_type_label: Mapped[str] = mapped_column(String(255), nullable=False)
    source_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    risk_note: Mapped[str | None] = mapped_column(Text, nullable=True)
