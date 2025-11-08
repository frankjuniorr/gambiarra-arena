"""Tests for Pydantic schemas."""

import pytest
from pydantic import ValidationError

from src.schemas.websocket import (
    RegisterMessage,
    TokenMessage,
    CompleteMessage,
    ChallengeMessage,
)
from src.schemas.http import (
    RoundCreate,
    VoteCreate,
)


class TestWebSocketSchemas:
    """Test WebSocket message schemas."""

    def test_register_message_valid(self):
        """Test valid registration message."""
        msg = RegisterMessage(
            participant_id="test-1",
            nickname="Test User",
            pin="123456",
            runner="ollama",
            model="llama3.1:8b",
        )
        assert msg.type == "register"
        assert msg.participant_id == "test-1"

    def test_register_message_invalid_empty_fields(self):
        """Test registration with empty fields fails."""
        with pytest.raises(ValidationError):
            RegisterMessage(
                participant_id="",
                nickname="Test",
                pin="123456",
                runner="ollama",
                model="llama3.1:8b",
            )

    def test_token_message_valid(self):
        """Test valid token message."""
        msg = TokenMessage(
            round=0,
            participant_id="test-1",
            seq=5,
            content="Hello",
        )
        assert msg.type == "token"
        assert msg.seq == 5

    def test_token_message_negative_seq(self):
        """Test token with negative sequence fails."""
        with pytest.raises(ValidationError):
            TokenMessage(
                round=0,
                participant_id="test-1",
                seq=-1,
                content="Hello",
            )

    def test_complete_message_valid(self):
        """Test valid completion message."""
        msg = CompleteMessage(
            round=0,
            participant_id="test-1",
            tokens=100,
            latency_ms_first_token=50,
            duration_ms=2000,
            model_info={"name": "llama3.1:8b"},
        )
        assert msg.tokens == 100
        assert msg.duration_ms == 2000

    def test_complete_message_negative_tokens(self):
        """Test completion with negative tokens fails."""
        with pytest.raises(ValidationError):
            CompleteMessage(
                round=0,
                participant_id="test-1",
                tokens=-1,
                duration_ms=2000,
            )

    def test_challenge_message_valid(self):
        """Test valid challenge message."""
        msg = ChallengeMessage(
            session_id="session-123",
            round=0,
            prompt="Write a haiku",
            max_tokens=400,
            temperature=0.8,
            deadline_ms=90000,
        )
        assert msg.type == "challenge"
        assert msg.temperature == 0.8

    def test_challenge_message_invalid_temperature(self):
        """Test challenge with invalid temperature fails."""
        with pytest.raises(ValidationError):
            ChallengeMessage(
                session_id="session-123",
                round=0,
                prompt="Write a haiku",
                max_tokens=400,
                temperature=3.0,  # > 2.0
                deadline_ms=90000,
            )


class TestHTTPSchemas:
    """Test HTTP request/response schemas."""

    def test_round_create_valid(self):
        """Test valid round creation."""
        data = RoundCreate(
            session_id="session-123",
            prompt="Write a story",
            max_tokens=500,
            temperature=0.9,
            deadline_ms=120000,
        )
        assert data.prompt == "Write a story"
        assert data.max_tokens == 500

    def test_round_create_defaults(self):
        """Test round creation with defaults."""
        data = RoundCreate(
            session_id="session-123",
            prompt="Write a story",
        )
        assert data.max_tokens == 400
        assert data.temperature == 0.8
        assert data.deadline_ms == 90000

    def test_vote_create_valid(self):
        """Test valid vote creation."""
        data = VoteCreate(
            round_id="round-123",
            participant_id="player-1",
            score=5,
        )
        assert data.score == 5

    def test_vote_create_invalid_score_low(self):
        """Test vote with score < 1 fails."""
        with pytest.raises(ValidationError):
            VoteCreate(
                round_id="round-123",
                participant_id="player-1",
                score=0,
            )

    def test_vote_create_invalid_score_high(self):
        """Test vote with score > 5 fails."""
        with pytest.raises(ValidationError):
            VoteCreate(
                round_id="round-123",
                participant_id="player-1",
                score=6,
            )
