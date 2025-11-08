#!/usr/bin/env python3
"""CLI for Gambiarra LLM Club Client."""

import argparse
import asyncio
import sys
from datetime import datetime
from typing import Optional

from .net.ws import GambiarraClient, ClientConfig, Challenge, TokenMessage, CompleteMessage, ErrorMessage
from .runners import Runner, GenerateOptions, MockRunner, OllamaRunner, LMStudioRunner


# ANSI color codes for terminal output
class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    GRAY = '\033[90m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_banner():
    """Print startup banner."""
    print(f"{Colors.BOLD}{Colors.CYAN}\n🎮 Gambiarra LLM Club Client\n{Colors.END}")


def print_success(message: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")


def print_error(message: str):
    """Print error message."""
    print(f"{Colors.RED}✗ {message}{Colors.END}")


def print_info(message: str):
    """Print info message."""
    print(f"{Colors.GRAY}{message}{Colors.END}")


def print_warning(message: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}{message}{Colors.END}")


async def handle_challenge(
    client: GambiarraClient,
    runner: Runner,
    challenge: Challenge,
    options: argparse.Namespace
):
    """Handle incoming challenge."""
    print(f"\n{Colors.BOLD}{Colors.YELLOW}📢 New Challenge - Round {challenge.round}{Colors.END}")
    print_info(f"Prompt: {challenge.prompt}")
    print_info(f"Max tokens: {challenge.max_tokens}, Deadline: {challenge.deadline_ms}ms\n")

    try:
        seq = 0
        start_time = datetime.now()
        first_token_time: Optional[datetime] = None
        all_tokens = []

        def on_token(token: str):
            nonlocal seq, first_token_time
            if first_token_time is None:
                first_token_time = datetime.now()

            all_tokens.append(token)

            # Send token to server
            asyncio.create_task(client.send_token(TokenMessage(
                round=challenge.round,
                seq=seq,
                content=token
            )))

            # Log progress
            print(f"{Colors.GRAY}.{Colors.END}", end="", flush=True)
            seq += 1

        # Generate tokens
        await runner.generate(
            challenge.prompt,
            GenerateOptions(
                max_tokens=challenge.max_tokens,
                temperature=challenge.temperature,
                seed=challenge.seed,
            ),
            on_token
        )

        end_time = datetime.now()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        latency_ms_first_token = None
        if first_token_time:
            latency_ms_first_token = int((first_token_time - start_time).total_seconds() * 1000)

        print(f"\n\n{Colors.GREEN}✓ Completed {seq} tokens in {duration_ms / 1000:.2f}s{Colors.END}")

        if latency_ms_first_token:
            print_info(f"  First token latency: {latency_ms_first_token}ms")

        # Send completion
        await client.send_complete(CompleteMessage(
            round=challenge.round,
            tokens=seq,
            latency_ms_first_token=latency_ms_first_token,
            duration_ms=duration_ms,
            model_info={
                "name": options.model,
                "runner": options.runner,
            }
        ))

    except Exception as e:
        print_error(f"Generation failed: {e}")

        await client.send_error(ErrorMessage(
            round=challenge.round,
            code="GENERATION_FAILED",
            message=str(e)
        ))


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Cliente para Gambiarra LLM Club Arena",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("--url", default="ws://localhost:3000/ws", help="WebSocket server URL")
    parser.add_argument("--pin", required=True, help="Session PIN")
    parser.add_argument("--participant-id", required=True, help="Participant ID")
    parser.add_argument("--nickname", required=True, help="Participant nickname")
    parser.add_argument("--runner", default="ollama", choices=["ollama", "lmstudio", "mock"], help="Runner type")
    parser.add_argument("--model", default="llama3.1:8b", help="Model name")
    parser.add_argument("--temperature", type=float, default=0.8, help="Temperature")
    parser.add_argument("--max-tokens", type=int, default=400, help="Max tokens")
    parser.add_argument("--ollama-url", default="http://localhost:11434", help="Ollama API URL")
    parser.add_argument("--lmstudio-url", default="http://localhost:1234", help="LM Studio API URL")

    args = parser.parse_args()

    print_banner()

    # Create runner
    runner: Runner
    if args.runner == "ollama":
        print_info(f"Using Ollama at {args.ollama_url}")
        runner = OllamaRunner(args.ollama_url, args.model)
    elif args.runner == "lmstudio":
        print_info(f"Using LM Studio at {args.lmstudio_url}")
        runner = LMStudioRunner(args.lmstudio_url, args.model)
    elif args.runner == "mock":
        print_warning("Using Mock runner (simulated tokens)")
        runner = MockRunner()
    else:
        print_error(f"Unknown runner: {args.runner}")
        sys.exit(1)

    # Test runner
    try:
        await runner.test()
        print_success("Runner connection OK\n")
    except Exception as e:
        print_error(f"Runner connection failed: {e}")
        sys.exit(1)

    # Create client
    client = GambiarraClient(ClientConfig(
        url=args.url,
        participant_id=args.participant_id,
        nickname=args.nickname,
        pin=args.pin,
        runner=args.runner,
        model=args.model,
    ))

    # Connect
    try:
        await client.connect()
        print_success("Connected to server\n")
    except Exception as e:
        print_error(f"Failed to connect: {e}")
        sys.exit(1)

    # Handle challenges
    async def on_challenge(challenge: Challenge):
        await handle_challenge(client, runner, challenge, args)

    client.on("challenge", on_challenge)

    # Handle disconnect
    def on_close():
        print_warning("\n⚠️  Disconnected from server")
        sys.exit(0)

    client.on("close", on_close)

    print_success("Ready and waiting for challenges...")

    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print_warning("\n\nShutting down...")
        await client.disconnect()
        sys.exit(0)


def run():
    """Entry point for CLI."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
