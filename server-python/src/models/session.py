"""Session database model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .participant import Participant
    from .round import Round


class Session(Base):
    """Session model - represents a game session."""

    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    pin_hash: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="active", nullable=False)

    # Relationships
    participants: Mapped[list["Participant"]] = relationship(
        "Participant",
        back_populates="session",
        cascade="all, delete-orphan",
    )
    rounds: Mapped[list["Round"]] = relationship(
        "Round",
        back_populates="session",
        cascade="all, delete-orphan",
    )
