"""Round management module."""

import json
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from ..models import Session, Round, Metrics
from ..schemas.websocket import ChallengeMessage
from ..schemas.http import RoundCreate, RoundResponse


class RoundManager:
    """Manages round lifecycle and operations."""

    def __init__(self, hub):
        """Initialize with WebSocket hub for broadcasting."""
        self.hub = hub

    async def create_round(self, data: RoundCreate, db: AsyncSession) -> Round:
        """Create a new round."""
        # Get next round index for this session
        result = await db.execute(
            select(func.max(Round.index))
            .where(Round.session_id == data.session_id)
        )
        max_index = result.scalar()
        next_index = (max_index or -1) + 1

        # Create round
        round_obj = Round(
            session_id=data.session_id,
            index=next_index,
            prompt=data.prompt,
            max_tokens=data.max_tokens,
            temperature=data.temperature,
            deadline_ms=data.deadline_ms,
            seed=data.seed,
        )
        db.add(round_obj)
        await db.commit()
        await db.refresh(round_obj)

        return round_obj

    async def start_round(self, round_id: str, db: AsyncSession) -> Round:
        """Start a round and broadcast challenge."""
        # Get round
        result = await db.execute(
            select(Round)
            .where(Round.id == round_id)
            .options(selectinload(Round.session))
        )
        round_obj = result.scalar_one_or_none()

        if not round_obj:
            raise ValueError("Round not found")

        if round_obj.started_at:
            raise ValueError("Round already started")

        # Set started_at
        round_obj.started_at = datetime.utcnow()
        await db.commit()
        await db.refresh(round_obj)

        # Broadcast challenge
        challenge = ChallengeMessage(
            session_id=round_obj.session_id,
            round=round_obj.index,
            prompt=round_obj.prompt,
            max_tokens=round_obj.max_tokens,
            temperature=round_obj.temperature,
            deadline_ms=round_obj.deadline_ms,
            seed=round_obj.seed,
        )
        await self.hub.broadcast_challenge(challenge)

        return round_obj

    async def stop_round(self, round_id: str, db: AsyncSession) -> Round:
        """Stop a round."""
        # Get round
        result = await db.execute(
            select(Round).where(Round.id == round_id)
        )
        round_obj = result.scalar_one_or_none()

        if not round_obj:
            raise ValueError("Round not found")

        if not round_obj.started_at:
            raise ValueError("Round not started")

        if round_obj.ended_at:
            raise ValueError("Round already ended")

        # Set ended_at
        round_obj.ended_at = datetime.utcnow()
        await db.commit()
        await db.refresh(round_obj)

        return round_obj

    async def get_current_round(self, session_id: str, db: AsyncSession) -> Optional[Round]:
        """Get the current active round (started but not ended)."""
        result = await db.execute(
            select(Round)
            .where(
                Round.session_id == session_id,
                Round.started_at.isnot(None),
                Round.ended_at.is_(None),
            )
            .order_by(Round.index.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_round_metrics(
        self, round_id: str, db: AsyncSession
    ) -> list[Metrics]:
        """Get metrics for a round."""
        result = await db.execute(
            select(Metrics)
            .where(Metrics.round_id == round_id)
            .options(selectinload(Metrics.participant))
        )
        return list(result.scalars().all())

    async def get_round_by_id(self, round_id: str, db: AsyncSession) -> Optional[Round]:
        """Get a round by ID."""
        result = await db.execute(
            select(Round).where(Round.id == round_id)
        )
        return result.scalar_one_or_none()

    async def save_metrics(
        self,
        round_id: str,
        participant_id: str,
        tokens: int,
        latency_ms_first_token: Optional[int],
        duration_ms: int,
        model_info: Optional[dict],
        db: AsyncSession,
    ) -> Metrics:
        """Save or update metrics for a participant/round."""
        # Calculate TPS
        tps_avg = None
        if duration_ms > 0:
            tps_avg = (tokens / duration_ms) * 1000

        # Convert model_info to JSON string
        model_info_json = None
        if model_info:
            model_info_json = json.dumps(model_info)

        # Try to find existing
        result = await db.execute(
            select(Metrics).where(
                Metrics.round_id == round_id,
                Metrics.participant_id == participant_id,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update
            existing.tokens = tokens
            existing.latency_first_token_ms = latency_ms_first_token
            existing.duration_ms = duration_ms
            existing.tps_avg = tps_avg
            existing.model_info = model_info_json
            metrics = existing
        else:
            # Create
            metrics = Metrics(
                round_id=round_id,
                participant_id=participant_id,
                tokens=tokens,
                latency_first_token_ms=latency_ms_first_token,
                duration_ms=duration_ms,
                tps_avg=tps_avg,
                model_info=model_info_json,
            )
            db.add(metrics)

        await db.commit()
        await db.refresh(metrics)
        return metrics
