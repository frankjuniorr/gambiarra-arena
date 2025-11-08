"""LM Studio runner for local LLM execution."""

import aiohttp
import json
from .types import Runner, GenerateOptions, TokenCallback


class LMStudioRunner(Runner):
    """Runner for LM Studio API."""

    def __init__(self, base_url: str, model: str):
        self.base_url = base_url
        self.model = model

    async def test(self) -> None:
        """Test if LM Studio is available."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/v1/models") as response:
                if not response.ok:
                    raise Exception(f"LM Studio not available at {self.base_url}")

    async def generate(
        self,
        prompt: str,
        options: GenerateOptions,
        on_token: TokenCallback
    ) -> None:
        """Generate text using LM Studio API with streaming."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "max_tokens": options.max_tokens or 400,
            "temperature": options.temperature or 0.8,
            "stream": True,
        }

        if options.seed is not None:
            payload["seed"] = options.seed

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/v1/completions",
                json=payload
            ) as response:
                if not response.ok:
                    raise Exception(f"LM Studio API error: {response.status}")

                # Read streaming response (SSE format)
                async for line in response.content:
                    if not line:
                        continue

                    line_str = line.decode('utf-8').strip()
                    if not line_str or not line_str.startswith("data: "):
                        continue

                    data_str = line_str[6:]  # Remove 'data: ' prefix
                    if data_str == "[DONE]":
                        return

                    try:
                        data = json.loads(data_str)
                        token = data.get("choices", [{}])[0].get("text")
                        if token:
                            on_token(token)
                    except json.JSONDecodeError as e:
                        print(f"Failed to parse LM Studio response: {e}")
