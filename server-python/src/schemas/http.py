"""HTTP API schemas using Pydantic."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


# Session Schemas


class SessionCreate(BaseModel):
    """Request to create a new session."""

    pass  # No input required


class SessionResponse(BaseModel):
    """Session response (excludes pin_hash)."""

    id: str
    created_at: datetime
    status: str
    pin: Optional[str] = None  # Only included on creation


# Round Schemas


class RoundCreate(BaseModel):
    """Request to create a new round."""

    session_id: str
    prompt: str = Field(..., min_length=1)
    max_tokens: int = Field(default=400, ge=1)
    temperature: float = Field(default=0.8, ge=0.0, le=2.0)
    deadline_ms: int = Field(default=90000, ge=0)
    seed: Optional[int] = None


class RoundStart(BaseModel):
    """Request to start a round."""

    round_id: str


class RoundStop(BaseModel):
    """Request to stop a round."""

    round_id: str


class RoundResponse(BaseModel):
    """Round response."""

    id: str
    session_id: str
    index: int
    prompt: str
    max_tokens: int
    temperature: float
    deadline_ms: int
    seed: Optional[int]
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    created_at: datetime


# Vote Schemas


class VoteCreate(BaseModel):
    """Request to cast a vote."""

    round_id: str
    participant_id: str
    score: int = Field(..., ge=1, le=5)


class VoteResponse(BaseModel):
    """Vote response."""

    id: str
    round_id: str
    participant_id: str
    score: int
    created_at: datetime


class ScoreboardEntry(BaseModel):
    """Scoreboard entry."""

    participant_id: str
    nickname: str
    runner: str
    model: str
    tokens: Optional[int] = None
    duration_ms: Optional[int] = None
    tps_avg: Optional[float] = None
    vote_count: int
    avg_score: Optional[float] = None
    total_score: float


class ScoreboardResponse(BaseModel):
    """Scoreboard response."""

    round_id: str
    round_index: int
    entries: list[ScoreboardEntry]


# Metrics Schemas


class MetricsResponse(BaseModel):
    """Session metrics response."""

    total_rounds: int
    completed_rounds: int
    total_participants: int
    total_tokens: int
    total_votes: int


# Participant Schemas


class ParticipantKick(BaseModel):
    """Request to kick a participant."""

    participant_id: str


class ParticipantResponse(BaseModel):
    """Participant response."""

    id: str
    session_id: str
    nickname: str
    runner: str
    model: str
    connected: bool
    created_at: datetime
    last_seen: datetime


# Current Round Response (with live tokens)


class CurrentRoundResponse(BaseModel):
    """Current round with live token data."""

    round: RoundResponse
    tokens: dict[str, list[str]]  # participant_id -> tokens
