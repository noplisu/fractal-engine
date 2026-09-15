import os
from pathlib import Path

MAX_TOOL_OUTPUT = 50_000
DEFAULT_MAX_ITERATIONS = 25
DEFAULT_MAX_TOKENS = 8192
SKIP_DIR_NAMES = frozenset(
    {".git", ".venv", "node_modules", "__pycache__", ".ruff_cache", ".fractal"}
)

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")
MODEL = os.getenv(
    "FRACTAL_MODEL",
    "anthropic/claude-haiku-4.5",
)
MAX_TOKENS = int(os.getenv("FRACTAL_MAX_TOKENS", str(DEFAULT_MAX_TOKENS)))


def rag_dir() -> Path:
    raw = os.getenv("FRACTAL_RAG_DIR")
    if raw:
        return Path(raw).expanduser().resolve()
    return Path.cwd() / ".fractal" / "rag"


def rag_paths() -> tuple[Path, Path]:
    store = rag_dir()
    return store / "embeddings.npy", store / "chunks.jsonl"
