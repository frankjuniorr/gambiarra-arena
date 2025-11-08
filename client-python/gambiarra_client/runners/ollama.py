"""Ollama runner for local LLM execution."""

import aiohttp
import json
from .types import Runner, GenerateOptions, TokenCallback


class OllamaRunner(Runner):
    """Runner for Ollama API."""

    def __init__(self, base_url: str, model: str):
        self.base_url = base_url
        self.model = model

    async def test(self) -> None:
        """Test if Ollama is available."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/api/tags") as response:
                if not response.ok:
                    raise Exception(f"Ollama not available at {self.base_url}")

    async def generate(
        self,
        prompt: str,
        options: GenerateOptions,
        on_token: TokenCallback
    ) -> None:
        """Generate text using Ollama API with streaming."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "num_predict": options.max_tokens or 400,
                "temperature": options.temperature or 0.8,
            }
        }

        if options.seed is not None:
            payload["options"]["seed"] = options.seed

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/generate",
                json=payload
            ) as response:
                if not response.ok:
                    raise Exception(f"Ollama API error: {response.status}")

                # Read streaming response
                async for line in response.content:
                    if not line:
                        continue

                    try:
                        data = json.loads(line.decode('utf-8'))
                        if "response" in data:
                            on_token(data["response"])
                        if data.get("done"):
                            return
                    except json.JSONDecodeError as e:
                        print(f"Failed to parse Ollama response: {e}")
