"""Type definitions for runners."""

from abc import ABC, abstractmethod
from typing import Callable, Optional
from dataclasses import dataclass


@dataclass
class GenerateOptions:
    """Options for text generation."""

    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    seed: Optional[int] = None


TokenCallback = Callable[[str], None]


class Runner(ABC):
    """Abstract base class for LLM runners."""

    @abstractmethod
    async def test(self) -> None:
        """Test if the runner is available and working."""
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        options: GenerateOptions,
        on_token: TokenCallback
    ) -> None:
        """Generate text with streaming."""
        pass
