"""Vote database model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .round import Round
    from .participant import Participant


class Vote(Base):
    """Vote model - stores votes for participants in rounds."""

    __tablename__ = "votes"

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
    voter_hash: Mapped[str] = mapped_column(String, nullable=False)
    participant_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("participants.id", ondelete="CASCADE"),
        nullable=False,
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    round: Mapped["Round"] = relationship("Round", back_populates="votes")
    participant: Mapped["Participant"] = relationship("Participant", back_populates="votes")

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "round_id", "voter_hash", "participant_id", name="uq_vote_round_voter_participant"
        ),
    )
