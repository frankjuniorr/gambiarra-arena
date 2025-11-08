"""WebSocket client for Gambiarra arena."""

import asyncio
import json
import websockets
from typing import Any, Dict, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class MessageType(str, Enum):
    """WebSocket message types."""
    CHALLENGE = "challenge"
    HEARTBEAT = "heartbeat"
    REGISTERED = "registered"
    ERROR = "error"
    REGISTER = "register"
    TOKEN = "token"
    COMPLETE = "complete"


@dataclass
class ClientConfig:
    """Configuration for Gambiarra client."""
    url: str
    participant_id: str
    nickname: str
    pin: str
    runner: str
    model: str


@dataclass
class Challenge:
    """Challenge message from server."""
    session_id: str
    round: int
    prompt: str
    max_tokens: int
    temperature: float
    deadline_ms: int
    seed: Optional[int] = None


@dataclass
class TokenMessage:
    """Token message to send."""
    round: int
    seq: int
    content: str


@dataclass
class CompleteMessage:
    """Completion message to send."""
    round: int
    tokens: int
    latency_ms_first_token: Optional[int]
    duration_ms: int
    model_info: Optional[Dict[str, str]] = None


@dataclass
class ErrorMessage:
    """Error message to send."""
    round: int
    code: str
    message: str


class GambiarraClient:
    """WebSocket client for connecting to Gambiarra arena."""

    def __init__(self, config: ClientConfig):
        self.config = config
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 1.0
        self.running = False

        # Event handlers
        self._on_challenge: Optional[Callable[[Challenge], None]] = None
        self._on_close: Optional[Callable[[], None]] = None
        self._on_registered: Optional[Callable[[Dict], None]] = None

    def on(self, event: str, callback: Callable) -> None:
        """Register event handler."""
        if event == "challenge":
            self._on_challenge = callback
        elif event == "close":
            self._on_close = callback
        elif event == "registered":
            self._on_registered = callback

    async def connect(self) -> None:
        """Connect to WebSocket server."""
        try:
            self.ws = await websockets.connect(self.config.url)
            self.reconnect_attempts = 0
            self.running = True

            # Send registration
            await self._send({
                "type": MessageType.REGISTER,
                "participant_id": self.config.participant_id,
                "nickname": self.config.nickname,
                "pin": self.config.pin,
                "runner": self.config.runner,
                "model": self.config.model,
            })

            # Start message loop
            asyncio.create_task(self._message_loop())

        except Exception as e:
            raise Exception(f"Failed to connect: {e}")

    async def _message_loop(self) -> None:
        """Listen for messages from server."""
        try:
            async for message in self.ws:
                try:
                    data = json.loads(message)
                    await self._handle_message(data)
                except json.JSONDecodeError as e:
                    print(f"Failed to parse message: {e}")
        except websockets.exceptions.ConnectionClosed:
            if self._on_close:
                self._on_close()
            await self._attempt_reconnect()

    async def _handle_message(self, message: Dict[str, Any]) -> None:
        """Handle incoming message."""
        msg_type = message.get("type")

        if msg_type == MessageType.CHALLENGE:
            if self._on_challenge:
                challenge = Challenge(
                    session_id=message["session_id"],
                    round=message["round"],
                    prompt=message["prompt"],
                    max_tokens=message["max_tokens"],
                    temperature=message["temperature"],
                    deadline_ms=message["deadline_ms"],
                    seed=message.get("seed"),
                )
                await self._on_challenge(challenge)

        elif msg_type == MessageType.HEARTBEAT:
            # Respond to heartbeat if needed
            pass

        elif msg_type == MessageType.REGISTERED:
            if self._on_registered:
                self._on_registered(message)

        elif msg_type == MessageType.ERROR:
            print(f"Server error: {message.get('message')}")

        else:
            print(f"Unknown message type: {msg_type}")

    async def send_token(self, data: TokenMessage) -> None:
        """Send token to server."""
        await self._send({
            "type": MessageType.TOKEN,
            "round": data.round,
            "participant_id": self.config.participant_id,
            "seq": data.seq,
            "content": data.content,
        })

    async def send_complete(self, data: CompleteMessage) -> None:
        """Send completion to server."""
        await self._send({
            "type": MessageType.COMPLETE,
            "round": data.round,
            "participant_id": self.config.participant_id,
            "tokens": data.tokens,
            "latency_ms_first_token": data.latency_ms_first_token,
            "duration_ms": data.duration_ms,
            "model_info": data.model_info,
        })

    async def send_error(self, data: ErrorMessage) -> None:
        """Send error to server."""
        await self._send({
            "type": MessageType.ERROR,
            "round": data.round,
            "participant_id": self.config.participant_id,
            "code": data.code,
            "message": data.message,
        })

    async def _send(self, data: Dict[str, Any]) -> None:
        """Send message to server."""
        if self.ws:
            await self.ws.send(json.dumps(data))

    async def _attempt_reconnect(self) -> None:
        """Attempt to reconnect with exponential backoff."""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            print("Max reconnection attempts reached")
            return

        self.reconnect_attempts += 1
        delay = self.reconnect_delay * (2 ** (self.reconnect_attempts - 1))

        print(f"Reconnecting in {delay}s (attempt {self.reconnect_attempts}/{self.max_reconnect_attempts})")

        await asyncio.sleep(delay)

        try:
            await self.connect()
        except Exception as e:
            print(f"Reconnection failed: {e}")

    async def disconnect(self) -> None:
        """Disconnect from server."""
        self.running = False
        if self.ws:
            await self.ws.close()
            self.ws = None
