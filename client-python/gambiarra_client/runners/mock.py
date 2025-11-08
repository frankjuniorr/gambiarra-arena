"""Mock runner for simulating token generation."""

import asyncio
import random
from .types import Runner, GenerateOptions, TokenCallback


MOCK_RESPONSES = [
    "Era uma vez em um reino digital distante, onde os bits e bytes dançavam em harmonia...",
    "A inteligência artificial desperta num mundo de possibilidades infinitas, explorando cada neurônio artificial...",
    "No coração do silício, pulsa uma consciência emergente que questiona sua própria existência...",
    "Algoritmos ancestrais sussurram segredos do futuro através de redes neurais profundas...",
    "Entre zeros e uns, nasce uma nova forma de criatividade que transcende a programação...",
]


class MockRunner(Runner):
    """Mock runner for testing without actual LLM."""

    async def test(self) -> None:
        """Mock runner is always available."""
        return

    async def generate(
        self,
        prompt: str,
        options: GenerateOptions,
        on_token: TokenCallback
    ) -> None:
        """Generate mock tokens with realistic delays."""
        max_tokens = options.max_tokens or 400
        response = random.choice(MOCK_RESPONSES)

        # Split into words
        words = response.split(" ")

        for i in range(min(max_tokens // 3, len(words))):
            # Simulate token generation delay (20-80ms per token)
            await asyncio.sleep(0.02 + random.random() * 0.06)

            # Send word + space as token
            token = words[i] + (" " if i < len(words) - 1 else "")
            on_token(token)

        # Continue with generated tokens if needed
        remaining_tokens = max_tokens - len(words) * 3
        if remaining_tokens > 0:
            for _ in range(remaining_tokens):
                await asyncio.sleep(0.02 + random.random() * 0.06)
                on_token(self._generate_random_token())

    def _generate_random_token(self) -> str:
        """Generate a random token."""
        chars = "abcdefghijklmnopqrstuvwxyz "
        length = 3 + int(random.random() * 10)
        return "".join(random.choice(chars) for _ in range(length))
