"""Seed script to populate database with test data."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from passlib.hash import bcrypt
from src.database import AsyncSessionLocal, init_db
from src.models import Session, Round


async def seed():
    """Seed database with test data."""
    print("Initializing database...")
    await init_db()

    async with AsyncSessionLocal() as db:
        # Create test session with known PIN
        pin = "123456"
        pin_hash = bcrypt.hash(pin)

        session = Session(
            pin_hash=pin_hash,
            status="active",
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

        print(f"✓ Created session: {session.id}")
        print(f"  PIN: {pin}")

        # Create test rounds
        prompts = [
            "Escreva um haiku sobre inteligência artificial",
            "Complete a história: Era uma vez um robô que...",
            "Explique o teorema de Pitágoras em uma frase",
        ]

        for i, prompt in enumerate(prompts):
            round_obj = Round(
                session_id=session.id,
                index=i,
                prompt=prompt,
                max_tokens=400,
                temperature=0.8,
                deadline_ms=90000,
            )
            db.add(round_obj)

        await db.commit()
        print(f"✓ Created {len(prompts)} test rounds")

        print("\n✅ Seed completed successfully!")
        print(f"\nYou can now:")
        print(f"1. Start the server: python -m src.main")
        print(f"2. Connect clients with PIN: {pin}")
        print(f"3. Start a round via API: POST /rounds/start")


if __name__ == "__main__":
    asyncio.run(seed())
