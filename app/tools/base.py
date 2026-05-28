from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class Tool:
    """One agent tool: OpenAI function schema plus an executor."""

    name: str
    description: str
    parameters: dict
    execute: Callable[[str], str]

    def to_openai_spec(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
