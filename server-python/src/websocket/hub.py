"""WebSocket Hub - manages connections and message routing."""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from passlib.hash import bcrypt

from ..models import Session, Participant, Metrics
from ..schemas.websocket import (
    RegisterMessage,
    TokenMessage,
    CompleteMessage,
    ErrorMessage,
    TelaoRegisterMessage,
    ChallengeMessage,
    HeartbeatMessage,
    ParticipantRegisteredMessage,
    TokenUpdateMessage,
    CompletionBroadcastMessage,
    ParticipantDisconnectedMessage,
)


class WebSocketHub:
    """Manages WebSocket connections and message broadcasting."""

    def __init__(self):
        # participant_id -> WebSocket
        self.connections: Dict[str, WebSocket] = {}

        # telao WebSocket connections
        self.telao_connections: List[WebSocket] = []

        # Token buffer: participant_id -> round_index -> tokens[]
        self.token_buffer: Dict[str, Dict[int, List[str]]] = {}

        # Heartbeat task
        self.heartbeat_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the hub (e.g., heartbeat task)."""
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def stop(self):
        """Stop the hub and cleanup."""
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass

    async def _heartbeat_loop(self):
        """Send periodic heartbeats to all connections."""
        while True:
            try:
                await asyncio.sleep(30)  # 30 seconds
                message = HeartbeatMessage(ts=int(time.time() * 1000))
                await self.broadcast(message.model_dump())
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Heartbeat error: {e}")

    async def handle_connection(self, websocket: WebSocket, db: AsyncSession):
        """Handle a WebSocket connection."""
        await websocket.accept()
        participant_id: Optional[str] = None
        is_telao = False

        try:
            while True:
                # Receive message
                data = await websocket.receive_text()
                message = json.loads(data)
                msg_type = message.get("type")

                if msg_type == "register":
                    participant_id = await self._handle_register(
                        RegisterMessage(**message), websocket, db
                    )

                elif msg_type == "telao_register":
                    is_telao = True
                    await self._handle_telao_register(
                        TelaoRegisterMessage(**message), websocket
                    )

                elif msg_type == "token":
                    await self._handle_token(TokenMessage(**message), db)

                elif msg_type == "complete":
                    await self._handle_complete(CompleteMessage(**message), db)

                elif msg_type == "error":
                    await self._handle_error(ErrorMessage(**message))

        except Exception as e:
            print(f"WebSocket error: {e}")

        finally:
            # Cleanup
            if is_telao and websocket in self.telao_connections:
                self.telao_connections.remove(websocket)
            elif participant_id and participant_id in self.connections:
                del self.connections[participant_id]

                # Update participant as disconnected
                await db.execute(
                    update(Participant)
                    .where(Participant.id == participant_id)
                    .values(connected=False, last_seen=datetime.utcnow())
                )
                await db.commit()

                # Broadcast disconnection
                await self.broadcast_to_telao(
                    ParticipantDisconnectedMessage(
                        participant_id=participant_id,
                        ts=int(time.time() * 1000),
                    ).model_dump()
                )

    async def _handle_register(
        self, message: RegisterMessage, websocket: WebSocket, db: AsyncSession
    ) -> str:
        """Handle participant registration."""
        # Find active session
        result = await db.execute(
            select(Session)
            .where(Session.status == "active")
            .order_by(Session.created_at.desc())
            .limit(1)
        )
        session = result.scalar_one_or_none()

        if not session:
            await websocket.send_json({"type": "error", "message": "No active session"})
            raise Exception("No active session")

        # Verify PIN
        if not bcrypt.verify(message.pin, session.pin_hash):
            await websocket.send_json({"type": "error", "message": "Invalid PIN"})
            raise Exception("Invalid PIN")

        # Upsert participant
        result = await db.execute(
            select(Participant).where(Participant.id == message.participant_id)
        )
        participant = result.scalar_one_or_none()

        if participant:
            # Update existing
            participant.nickname = message.nickname
            participant.runner = message.runner
            participant.model = message.model
            participant.connected = True
            participant.last_seen = datetime.utcnow()
        else:
            # Create new
            participant = Participant(
                id=message.participant_id,
                session_id=session.id,
                nickname=message.nickname,
                runner=message.runner,
                model=message.model,
                connected=True,
            )
            db.add(participant)

        await db.commit()
        await db.refresh(participant)

        # Store connection
        self.connections[message.participant_id] = websocket

        # Send success
        await websocket.send_json({"type": "registered", "participant_id": message.participant_id})

        # Broadcast to telao
        await self.broadcast_to_telao(
            ParticipantRegisteredMessage(
                participant={
                    "id": participant.id,
                    "nickname": participant.nickname,
                    "runner": participant.runner,
                    "model": participant.model,
                    "connected": participant.connected,
                    "last_seen": participant.last_seen.isoformat(),
                }
            ).model_dump()
        )

        return message.participant_id

    async def _handle_telao_register(self, message: TelaoRegisterMessage, websocket: WebSocket):
        """Handle telao registration."""
        self.telao_connections.append(websocket)
        await websocket.send_json({"type": "telao_registered"})

    async def _handle_token(self, message: TokenMessage, db: AsyncSession):
        """Handle token streaming."""
        participant_id = message.participant_id
        round_index = message.round

        # Initialize buffer
        if participant_id not in self.token_buffer:
            self.token_buffer[participant_id] = {}
        if round_index not in self.token_buffer[participant_id]:
            self.token_buffer[participant_id][round_index] = []

        tokens = self.token_buffer[participant_id][round_index]

        # Validate sequence
        if message.seq != len(tokens):
            print(
                f"Sequence mismatch for {participant_id} round {round_index}: "
                f"expected {len(tokens)}, got {message.seq}"
            )
            return  # Drop token

        # Add token
        tokens.append(message.content)

        # Update last seen
        await db.execute(
            update(Participant)
            .where(Participant.id == participant_id)
            .values(last_seen=datetime.utcnow())
        )
        await db.commit()

        # Broadcast to telao
        await self.broadcast_to_telao(
            TokenUpdateMessage(
                participant_id=participant_id,
                round=round_index,
                seq=message.seq,
                content=message.content,
                total_tokens=len(tokens),
            ).model_dump()
        )

    async def _handle_complete(self, message: CompleteMessage, db: AsyncSession):
        """Handle completion message."""
        # Calculate TPS
        tps_avg = None
        if message.duration_ms > 0:
            tps_avg = (message.tokens / message.duration_ms) * 1000

        # Store metrics (upsert)
        # First try to find existing
        result = await db.execute(
            select(Metrics).where(
                Metrics.round_id == str(message.round),  # This needs round_id not index
                Metrics.participant_id == message.participant_id,
            )
        )
        existing = result.scalar_one_or_none()

        model_info_json = None
        if message.model_info:
            model_info_json = json.dumps(message.model_info)

        if existing:
            # Update
            existing.tokens = message.tokens
            existing.latency_first_token_ms = message.latency_ms_first_token
            existing.duration_ms = message.duration_ms
            existing.tps_avg = tps_avg
            existing.model_info = model_info_json
        else:
            # Note: We need round_id, not round index. This will need to be resolved
            # when integrating with rounds manager
            pass  # Will be handled by core/rounds.py

        await db.commit()

        # Broadcast to telao
        await self.broadcast_to_telao(
            CompletionBroadcastMessage(
                participant_id=message.participant_id,
                round=message.round,
                tokens=message.tokens,
                duration_ms=message.duration_ms,
            ).model_dump()
        )

    async def _handle_error(self, message: ErrorMessage):
        """Handle error message."""
        print(
            f"Client error from {message.participant_id} in round {message.round}: "
            f"{message.code} - {message.message}"
        )

    async def broadcast(self, message: dict):
        """Broadcast message to all participants."""
        disconnected = []
        for participant_id, ws in self.connections.items():
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(participant_id)

        # Cleanup disconnected
        for participant_id in disconnected:
            del self.connections[participant_id]

    async def broadcast_to_telao(self, message: dict):
        """Broadcast message to all telao connections."""
        disconnected = []
        for ws in self.telao_connections:
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(ws)

        # Cleanup disconnected
        for ws in disconnected:
            self.telao_connections.remove(ws)

    async def broadcast_challenge(self, challenge: ChallengeMessage):
        """Broadcast challenge to all participants."""
        await self.broadcast(challenge.model_dump())

    def get_tokens(self, participant_id: str, round_index: int) -> List[str]:
        """Get buffered tokens for a participant/round."""
        return self.token_buffer.get(participant_id, {}).get(round_index, [])

    def get_all_tokens_for_round(self, round_index: int) -> Dict[str, List[str]]:
        """Get all tokens for a round."""
        result = {}
        for participant_id, rounds in self.token_buffer.items():
            if round_index in rounds:
                result[participant_id] = rounds[round_index]
        return result
