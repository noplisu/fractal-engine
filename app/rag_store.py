"""Helpers for Fractal's workspace-local RAG store."""

from __future__ import annotations

from types import ModuleType


def import_micro_rag_api() -> tuple[ModuleType | None, str | None]:
    try:
        from micro_rag import api as micro_rag_api
    except ImportError as exc:
        return None, (
            "Error: micro-rag is not installed. From fractal-engine run `uv sync` "
            "(https://github.com/noplisu/micro-rag). "
            f"Details: {exc}"
        )
    return micro_rag_api, None
