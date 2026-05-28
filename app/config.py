import os

MAX_TOOL_OUTPUT = 50_000
DEFAULT_MAX_ITERATIONS = 25
SKIP_DIR_NAMES = frozenset(
    {".git", ".venv", "node_modules", "__pycache__", ".ruff_cache"}
)

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")
MODEL = os.getenv("FRACTAL_MODEL", "anthropic/claude-haiku-4.5")
