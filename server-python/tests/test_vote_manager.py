"""Tests for VoteManager."""

import pytest
from src.core.votes import VoteManager
from src.schemas.http import VoteCreate


@pytest.mark.asyncio
class TestVoteManager:
    """Test voting functionality."""

    def test_hash_voter_id(self):
        """Test voter ID hashing."""
        manager = VoteManager()
        hash1 = manager.hash_voter_id("192.168.1.1")
        hash2 = manager.hash_voter_id("192.168.1.1")
        hash3 = manager.hash_voter_id("192.168.1.2")

        # Same input produces same hash
        assert hash1 == hash2

        # Different input produces different hash
        assert hash1 != hash3

        # Hash is hex string
        assert len(hash1) == 64  # SHA-256 produces 64 hex chars

    async def test_cast_vote_invalid_score(self, db_session):
        """Test casting vote with invalid score raises error."""
        manager = VoteManager()

        with pytest.raises(ValueError, match="Score must be between 1 and 5"):
            await manager.cast_vote(
                VoteCreate(
                    round_id="round-1",
                    participant_id="player-1",
                    score=6,  # Invalid
                ),
                voter_id="voter-1",
                db=db_session,
            )
