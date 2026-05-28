from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Tool:
    """One agent tool: OpenAI function schema plus an executor."""

    name: str
    description: str
    parameters: dict
    execute: Callable[[dict[str, Any]], str]

    def to_openai_spec(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
