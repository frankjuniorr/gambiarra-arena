"""WebSocket message schemas using Pydantic."""

from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator


# Client → Server Messages


class RegisterMessage(BaseModel):
    """Client registration message."""

    type: Literal["register"] = "register"
    participant_id: str = Field(..., min_length=1)
    nickname: str = Field(..., min_length=1)
    pin: str = Field(..., min_length=1)
    runner: str = Field(..., min_length=1)
    model: str = Field(..., min_length=1)


class TokenMessage(BaseModel):
    """Token streaming message."""

    type: Literal["token"] = "token"
    round: int = Field(..., ge=0)
    participant_id: str = Field(..., min_length=1)
    seq: int = Field(..., ge=0)
    content: str


class CompleteMessage(BaseModel):
    """Completion message with metrics."""

    type: Literal["complete"] = "complete"
    round: int = Field(..., ge=0)
    participant_id: str = Field(..., min_length=1)
    tokens: int = Field(..., ge=0)
    latency_ms_first_token: Optional[int] = Field(None, ge=0)
    duration_ms: int = Field(..., ge=0)
    model_info: Optional[dict] = None


class ErrorMessage(BaseModel):
    """Error reporting message."""

    type: Literal["error"] = "error"
    round: int = Field(..., ge=0)
    participant_id: str = Field(..., min_length=1)
    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class TelaoRegisterMessage(BaseModel):
    """Telao registration message."""

    type: Literal["telao_register"] = "telao_register"
    view: Optional[str] = None


# Server → Client Messages


class ChallengeMessage(BaseModel):
    """Challenge broadcast message."""

    type: Literal["challenge"] = "challenge"
    session_id: str
    round: int = Field(..., ge=0)
    prompt: str = Field(..., min_length=1)
    max_tokens: int = Field(..., ge=1)
    temperature: float = Field(..., ge=0.0, le=2.0)
    deadline_ms: int = Field(..., ge=0)
    seed: Optional[int] = None


class HeartbeatMessage(BaseModel):
    """Heartbeat message."""

    type: Literal["heartbeat"] = "heartbeat"
    ts: int = Field(..., description="Unix timestamp in milliseconds")


# Server → Telao Messages


class ParticipantRegisteredMessage(BaseModel):
    """Participant registered broadcast to telao."""

    type: Literal["participant_registered"] = "participant_registered"
    participant: dict


class TokenUpdateMessage(BaseModel):
    """Token update broadcast to telao."""

    type: Literal["token_update"] = "token_update"
    participant_id: str
    round: int
    seq: int
    content: str
    total_tokens: int


class CompletionBroadcastMessage(BaseModel):
    """Completion broadcast to telao."""

    type: Literal["completion"] = "completion"
    participant_id: str
    round: int
    tokens: int
    duration_ms: int


class ParticipantDisconnectedMessage(BaseModel):
    """Participant disconnected broadcast to telao."""

    type: Literal["participant_disconnected"] = "participant_disconnected"
    participant_id: str
    ts: int
