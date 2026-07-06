from datetime import date, datetime
from typing import Any

from sqlalchemy import BigInteger, Boolean, Date, DateTime, Float, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.base import Base


class AnomalyFindingModel(Base):
    __tablename__ = "anomaly_findings"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "entity_type",
            "entity_id",
            "window_days",
            "as_of_date",
            name="uq_anomaly_finding_entity_window",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(100), nullable=False)
    window_days: Mapped[int] = mapped_column(Integer, nullable=False)
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)

    anomaly_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    severity: Mapped[str] = mapped_column(String(50), nullable=False, default="none")
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    anomaly_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    details: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
