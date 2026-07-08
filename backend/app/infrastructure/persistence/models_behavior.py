from datetime import date, datetime
from typing import Any

from sqlalchemy import BigInteger, Date, DateTime, Float, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.base import Base


class BehaviorFeatureSnapshotModel(Base):
    __tablename__ = "behavior_feature_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "entity_type",
            "entity_id",
            "window_days",
            "as_of_date",
            name="uq_behavior_feature_snapshot",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(100), nullable=False)
    window_days: Mapped[int] = mapped_column(Integer, nullable=False)
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)

    session_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    average_risk_score: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    max_risk_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    high_risk_session_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    inserted_activity_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deleted_activity_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    extended_activity_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    payroll_adjustment_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    manual_added_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rule_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    behavior_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    behavior_level: Mapped[str] = mapped_column(String(50), nullable=False, default="normal")
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class BehaviorPeerDeviationModel(Base):
    __tablename__ = "behavior_peer_deviations"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "entity_type",
            "entity_id",
            "metric_name",
            "window_days",
            "as_of_date",
            name="uq_behavior_peer_deviation",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    window_days: Mapped[int] = mapped_column(Integer, nullable=False)
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)

    entity_value: Mapped[float] = mapped_column(Float, nullable=False)
    peer_average: Mapped[float] = mapped_column(Float, nullable=False)
    peer_stddev: Mapped[float] = mapped_column(Float, nullable=False)
    z_score: Mapped[float] = mapped_column(Float, nullable=False)
    is_outlier: Mapped[bool] = mapped_column(nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
