"""FastAPI application entry point."""

import signal
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, Depends
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .database import get_db, init_db, close_db
from .api.routes import router
from .websocket.hub import WebSocketHub
from .core.rounds import RoundManager
from .core.votes import VoteManager
from .core.metrics import MetricsManager


# Global hub instance
hub = WebSocketHub()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    # Startup
    print(f"Starting Gambiarra Server on {settings.host}:{settings.port}")
    await init_db()
    await hub.start()

    # Setup signal handlers
    def signal_handler(sig, frame):
        print("\nShutting down gracefully...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    yield

    # Shutdown
    await hub.stop()
    await close_db()
    print("Server stopped")


# Create FastAPI app
app = FastAPI(
    title="Gambiarra LLM Club Server",
    description="Arena server for local LLM competitions",
    version="1.0.0",
    lifespan=lifespan,
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency injection for managers
def get_round_manager() -> RoundManager:
    """Get round manager instance."""
    return RoundManager(hub)


def get_vote_manager() -> VoteManager:
    """Get vote manager instance."""
    return VoteManager()


def get_metrics_manager() -> MetricsManager:
    """Get metrics manager instance."""
    return MetricsManager()


# Register HTTP routes
app.include_router(router)


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db),
):
    """WebSocket connection endpoint."""
    await hub.handle_connection(websocket, db)


# Override dependencies in routes to use our singletons
app.dependency_overrides[RoundManager] = get_round_manager
app.dependency_overrides[VoteManager] = get_vote_manager
app.dependency_overrides[MetricsManager] = get_metrics_manager


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development",
        log_level="info",
    )
