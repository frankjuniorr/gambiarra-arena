"""HTTP API routes."""

import secrets
import string
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from passlib.hash import bcrypt

from ..database import get_db
from ..models import Session, Participant, Round
from ..schemas.http import (
    SessionCreate,
    SessionResponse,
    RoundCreate,
    RoundStart,
    RoundStop,
    RoundResponse,
    VoteCreate,
    VoteResponse,
    ScoreboardResponse,
    MetricsResponse,
    ParticipantKick,
    CurrentRoundResponse,
)
from ..core.rounds import RoundManager
from ..core.votes import VoteManager
from ..core.metrics import MetricsManager
from ..config import settings


router = APIRouter()


def generate_pin(length: int = 6) -> str:
    """Generate a random PIN."""
    return "".join(secrets.choice(string.digits) for _ in range(length))


# Health check
@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


# Session routes


@router.post("/session", response_model=SessionResponse)
async def create_session(
    data: SessionCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new session."""
    # End any active sessions
    await db.execute(
        update(Session)
        .where(Session.status == "active")
        .values(status="ended")
    )
    await db.commit()

    # Generate PIN
    pin = generate_pin(settings.pin_length)
    pin_hash = bcrypt.hash(pin)

    # Create session
    session = Session(
        pin_hash=pin_hash,
        status="active",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    # Return with PIN (only time it's exposed)
    return SessionResponse(
        id=session.id,
        created_at=session.created_at,
        status=session.status,
        pin=pin,
    )


@router.get("/session", response_model=SessionResponse)
async def get_session(db: AsyncSession = Depends(get_db)):
    """Get active session."""
    result = await db.execute(
        select(Session)
        .where(Session.status == "active")
        .order_by(Session.created_at.desc())
        .limit(1)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="No active session")

    return SessionResponse(
        id=session.id,
        created_at=session.created_at,
        status=session.status,
    )


# Round routes


@router.post("/rounds", response_model=RoundResponse)
async def create_round(
    data: RoundCreate,
    round_manager: RoundManager = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Create a new round."""
    round_obj = await round_manager.create_round(data, db)

    return RoundResponse(
        id=round_obj.id,
        session_id=round_obj.session_id,
        index=round_obj.index,
        prompt=round_obj.prompt,
        max_tokens=round_obj.max_tokens,
        temperature=round_obj.temperature,
        deadline_ms=round_obj.deadline_ms,
        seed=round_obj.seed,
        started_at=round_obj.started_at,
        ended_at=round_obj.ended_at,
        created_at=round_obj.created_at,
    )


@router.post("/rounds/start", response_model=RoundResponse)
async def start_round(
    data: RoundStart,
    round_manager: RoundManager = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Start a round."""
    try:
        round_obj = await round_manager.start_round(data.round_id, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return RoundResponse(
        id=round_obj.id,
        session_id=round_obj.session_id,
        index=round_obj.index,
        prompt=round_obj.prompt,
        max_tokens=round_obj.max_tokens,
        temperature=round_obj.temperature,
        deadline_ms=round_obj.deadline_ms,
        seed=round_obj.seed,
        started_at=round_obj.started_at,
        ended_at=round_obj.ended_at,
        created_at=round_obj.created_at,
    )


@router.post("/rounds/stop", response_model=RoundResponse)
async def stop_round(
    data: RoundStop,
    round_manager: RoundManager = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Stop a round."""
    try:
        round_obj = await round_manager.stop_round(data.round_id, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return RoundResponse(
        id=round_obj.id,
        session_id=round_obj.session_id,
        index=round_obj.index,
        prompt=round_obj.prompt,
        max_tokens=round_obj.max_tokens,
        temperature=round_obj.temperature,
        deadline_ms=round_obj.deadline_ms,
        seed=round_obj.seed,
        started_at=round_obj.started_at,
        ended_at=round_obj.ended_at,
        created_at=round_obj.created_at,
    )


@router.get("/rounds/current", response_model=CurrentRoundResponse)
async def get_current_round(
    round_manager: RoundManager = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Get current round with live tokens."""
    # Get active session
    session_result = await db.execute(
        select(Session)
        .where(Session.status == "active")
        .order_by(Session.created_at.desc())
        .limit(1)
    )
    session = session_result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="No active session")

    # Get current round
    round_obj = await round_manager.get_current_round(session.id, db)

    if not round_obj:
        raise HTTPException(status_code=404, detail="No current round")

    # Get live tokens from hub
    tokens = round_manager.hub.get_all_tokens_for_round(round_obj.index)

    return CurrentRoundResponse(
        round=RoundResponse(
            id=round_obj.id,
            session_id=round_obj.session_id,
            index=round_obj.index,
            prompt=round_obj.prompt,
            max_tokens=round_obj.max_tokens,
            temperature=round_obj.temperature,
            deadline_ms=round_obj.deadline_ms,
            seed=round_obj.seed,
            started_at=round_obj.started_at,
            ended_at=round_obj.ended_at,
            created_at=round_obj.created_at,
        ),
        tokens=tokens,
    )


# Vote routes


@router.post("/votes", response_model=VoteResponse)
async def cast_vote(
    data: VoteCreate,
    request: Request,
    vote_manager: VoteManager = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Cast a vote."""
    # Use request IP as voter ID
    voter_id = request.client.host if request.client else "unknown"

    try:
        vote = await vote_manager.cast_vote(data, voter_id, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return VoteResponse(
        id=vote.id,
        round_id=vote.round_id,
        participant_id=vote.participant_id,
        score=vote.score,
        created_at=vote.created_at,
    )


@router.post("/votes/close")
async def close_voting(
    round_id: str,
    vote_manager: VoteManager = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Close voting for a round."""
    await vote_manager.close_voting(round_id, db)
    return {"status": "ok"}


@router.get("/scoreboard", response_model=ScoreboardResponse)
async def get_scoreboard(
    round_manager: RoundManager = Depends(),
    vote_manager: VoteManager = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Get scoreboard for current round."""
    # Get active session
    session_result = await db.execute(
        select(Session)
        .where(Session.status == "active")
        .order_by(Session.created_at.desc())
        .limit(1)
    )
    session = session_result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="No active session")

    # Get current round
    round_obj = await round_manager.get_current_round(session.id, db)

    if not round_obj:
        raise HTTPException(status_code=404, detail="No current round")

    # Get scoreboard
    entries = await vote_manager.get_scoreboard(round_obj.id, db)

    return ScoreboardResponse(
        round_id=round_obj.id,
        round_index=round_obj.index,
        entries=entries,
    )


# Metrics routes


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    metrics_manager: MetricsManager = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Get session metrics."""
    # Get active session
    session_result = await db.execute(
        select(Session)
        .where(Session.status == "active")
        .order_by(Session.created_at.desc())
        .limit(1)
    )
    session = session_result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="No active session")

    # Get metrics
    metrics = await metrics_manager.get_session_metrics(session.id, db)

    return MetricsResponse(**metrics)


@router.get("/export.csv")
async def export_csv(
    metrics_manager: MetricsManager = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Export session data as CSV."""
    # Get active session
    session_result = await db.execute(
        select(Session)
        .where(Session.status == "active")
        .order_by(Session.created_at.desc())
        .limit(1)
    )
    session = session_result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="No active session")

    # Export CSV
    csv_content = await metrics_manager.export_session_csv(session.id, db)

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="session_{session.id}.csv"'
        },
    )


# Participant routes


@router.post("/participants/kick")
async def kick_participant(
    data: ParticipantKick,
    db: AsyncSession = Depends(get_db),
):
    """Kick a participant."""
    # Update participant as disconnected
    result = await db.execute(
        update(Participant)
        .where(Participant.id == data.participant_id)
        .values(connected=False, last_seen=datetime.utcnow())
    )
    await db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Participant not found")

    return {"status": "ok"}
