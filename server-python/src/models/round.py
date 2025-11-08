"""Round database model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .session import Session
    from .metrics import Metrics
    from .vote import Vote


class Round(Base):
    """Round model - represents a challenge round."""

    __tablename__ = "rounds"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    session_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    index: Mapped[int] = mapped_column(Integer, nullable=False)
    prompt: Mapped[str] = mapped_column(String, nullable=False)
    max_tokens: Mapped[int] = mapped_column(Integer, default=400, nullable=False)
    temperature: Mapped[float] = mapped_column(Float, default=0.8, nullable=False)
    deadline_ms: Mapped[int] = mapped_column(Integer, default=90000, nullable=False)
    seed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    session: Mapped["Session"] = relationship("Session", back_populates="rounds")
    metrics: Mapped[list["Metrics"]] = relationship(
        "Metrics",
        back_populates="round",
        cascade="all, delete-orphan",
    )
    votes: Mapped[list["Vote"]] = relationship(
        "Vote",
        back_populates="round",
        cascade="all, delete-orphan",
    )
