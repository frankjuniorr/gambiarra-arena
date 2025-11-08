"""Voting system module."""

import hashlib
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from ..models import Vote, Participant, Metrics
from ..schemas.http import VoteCreate, ScoreboardEntry


class VoteManager:
    """Manages voting and scoreboard operations."""

    @staticmethod
    def hash_voter_id(voter_id: str) -> str:
        """Hash voter ID for privacy."""
        return hashlib.sha256(voter_id.encode()).hexdigest()

    async def cast_vote(
        self,
        data: VoteCreate,
        voter_id: str,
        db: AsyncSession,
    ) -> Vote:
        """Cast or update a vote."""
        # Hash voter ID
        voter_hash = self.hash_voter_id(voter_id)

        # Validate score
        if not 1 <= data.score <= 5:
            raise ValueError("Score must be between 1 and 5")

        # Try to find existing vote
        result = await db.execute(
            select(Vote).where(
                Vote.round_id == data.round_id,
                Vote.voter_hash == voter_hash,
                Vote.participant_id == data.participant_id,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update
            existing.score = data.score
            vote = existing
        else:
            # Create
            vote = Vote(
                round_id=data.round_id,
                voter_hash=voter_hash,
                participant_id=data.participant_id,
                score=data.score,
            )
            db.add(vote)

        await db.commit()
        await db.refresh(vote)
        return vote

    async def get_scoreboard(
        self,
        round_id: str,
        db: AsyncSession,
    ) -> list[ScoreboardEntry]:
        """Get scoreboard for a round."""
        # Query to get vote aggregates
        vote_subq = (
            select(
                Vote.participant_id,
                func.count(Vote.id).label("vote_count"),
                func.avg(Vote.score).label("avg_score"),
            )
            .where(Vote.round_id == round_id)
            .group_by(Vote.participant_id)
            .subquery()
        )

        # Query to get metrics
        metrics_subq = (
            select(
                Metrics.participant_id,
                Metrics.tokens,
                Metrics.duration_ms,
                Metrics.tps_avg,
            )
            .where(Metrics.round_id == round_id)
            .subquery()
        )

        # Join with participants
        query = (
            select(
                Participant.id,
                Participant.nickname,
                Participant.runner,
                Participant.model,
                metrics_subq.c.tokens,
                metrics_subq.c.duration_ms,
                metrics_subq.c.tps_avg,
                func.coalesce(vote_subq.c.vote_count, 0).label("vote_count"),
                vote_subq.c.avg_score,
            )
            .outerjoin(vote_subq, Participant.id == vote_subq.c.participant_id)
            .outerjoin(metrics_subq, Participant.id == metrics_subq.c.participant_id)
            .where(
                # Only participants who have metrics for this round
                metrics_subq.c.participant_id.isnot(None)
            )
        )

        result = await db.execute(query)
        rows = result.all()

        # Build scoreboard entries
        entries = []
        for row in rows:
            # Calculate total_score
            vote_count = row.vote_count or 0
            avg_score = row.avg_score or 0.0
            total_score = avg_score * vote_count

            entries.append(
                ScoreboardEntry(
                    participant_id=row.id,
                    nickname=row.nickname,
                    runner=row.runner,
                    model=row.model,
                    tokens=row.tokens,
                    duration_ms=row.duration_ms,
                    tps_avg=row.tps_avg,
                    vote_count=vote_count,
                    avg_score=avg_score,
                    total_score=total_score,
                )
            )

        # Sort by total_score descending
        entries.sort(key=lambda x: x.total_score, reverse=True)

        return entries

    async def close_voting(self, round_id: str, db: AsyncSession) -> None:
        """Close voting for a round (placeholder for future functionality)."""
        # Could add a voted_closed flag to Round model
        # For now, this is a no-op
        pass
