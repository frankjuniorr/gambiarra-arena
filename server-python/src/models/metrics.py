"""Metrics database model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .round import Round
    from .participant import Participant


class Metrics(Base):
    """Metrics model - stores performance metrics for each participant/round."""

    __tablename__ = "metrics"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    round_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("rounds.id", ondelete="CASCADE"),
        nullable=False,
    )
    participant_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("participants.id", ondelete="CASCADE"),
        nullable=False,
    )
    tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    latency_first_token_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    tps_avg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    model_info: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # JSON string
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    round: Mapped["Round"] = relationship("Round", back_populates="metrics")
    participant: Mapped["Participant"] = relationship("Participant", back_populates="metrics")

    # Constraints
    __table_args__ = (
        UniqueConstraint("round_id", "participant_id", name="uq_metrics_round_participant"),
    )
