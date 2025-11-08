"""Metrics aggregation and export module."""

import csv
import io
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from ..models import Session, Round, Participant, Metrics, Vote


class MetricsManager:
    """Manages metrics aggregation and CSV export."""

    async def get_session_metrics(
        self,
        session_id: str,
        db: AsyncSession,
    ) -> dict:
        """Get aggregated metrics for a session."""
        # Total rounds
        total_rounds_result = await db.execute(
            select(func.count(Round.id)).where(Round.session_id == session_id)
        )
        total_rounds = total_rounds_result.scalar() or 0

        # Completed rounds (ended)
        completed_rounds_result = await db.execute(
            select(func.count(Round.id)).where(
                Round.session_id == session_id,
                Round.ended_at.isnot(None),
            )
        )
        completed_rounds = completed_rounds_result.scalar() or 0

        # Total participants (distinct)
        total_participants_result = await db.execute(
            select(func.count(func.distinct(Participant.id))).where(
                Participant.session_id == session_id
            )
        )
        total_participants = total_participants_result.scalar() or 0

        # Total tokens across all metrics
        # Need to join Metrics with Rounds to filter by session
        total_tokens_result = await db.execute(
            select(func.sum(Metrics.tokens))
            .join(Round, Metrics.round_id == Round.id)
            .where(Round.session_id == session_id)
        )
        total_tokens = total_tokens_result.scalar() or 0

        # Total votes
        total_votes_result = await db.execute(
            select(func.count(Vote.id))
            .join(Round, Vote.round_id == Round.id)
            .where(Round.session_id == session_id)
        )
        total_votes = total_votes_result.scalar() or 0

        return {
            "total_rounds": total_rounds,
            "completed_rounds": completed_rounds,
            "total_participants": total_participants,
            "total_tokens": total_tokens,
            "total_votes": total_votes,
        }

    async def export_session_csv(
        self,
        session_id: str,
        db: AsyncSession,
    ) -> str:
        """Export session data as CSV."""
        # Get all rounds for session
        rounds_result = await db.execute(
            select(Round)
            .where(Round.session_id == session_id)
            .order_by(Round.index)
            .options(
                selectinload(Round.metrics).selectinload(Metrics.participant),
            )
        )
        rounds = list(rounds_result.scalars().all())

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            "round",
            "participant_id",
            "nickname",
            "tokens",
            "latency_first_token_ms",
            "duration_ms",
            "tps_avg",
            "votes",
            "avg_score",
        ])

        # Write data
        for round_obj in rounds:
            for metric in round_obj.metrics:
                participant = metric.participant

                # Get vote stats for this participant/round
                vote_result = await db.execute(
                    select(
                        func.count(Vote.id).label("vote_count"),
                        func.avg(Vote.score).label("avg_score"),
                    )
                    .where(
                        Vote.round_id == round_obj.id,
                        Vote.participant_id == participant.id,
                    )
                    .group_by(Vote.participant_id)
                )
                vote_row = vote_result.first()
                vote_count = vote_row.vote_count if vote_row else 0
                avg_score = vote_row.avg_score if vote_row else None

                writer.writerow([
                    round_obj.index,
                    participant.id,
                    participant.nickname,
                    metric.tokens,
                    metric.latency_first_token_ms or "",
                    metric.duration_ms,
                    f"{metric.tps_avg:.2f}" if metric.tps_avg else "",
                    vote_count,
                    f"{avg_score:.2f}" if avg_score else "",
                ])

        return output.getvalue()
