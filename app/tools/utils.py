import fnmatch
import json
import os
from pathlib import Path
from typing import Any

from app.config import MAX_TOOL_OUTPUT, SKIP_DIR_NAMES


def parse_arguments(arguments: str | dict[str, Any] | None) -> tuple[dict[str, Any] | None, str | None]:
    """Parse tool call arguments from the model into a dict."""
    if arguments is None:
        return None, "Error: missing tool arguments"
    if isinstance(arguments, dict):
        return arguments, None
    if not isinstance(arguments, str):
        arguments = str(arguments)
    text = arguments.strip()
    if not text:
        return None, "Error: empty tool arguments"
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as e:
        return None, (
            f"Error: invalid JSON in tool arguments ({e.msg} at char {e.pos}). "
            "String values must escape quotes (\\\"), backslashes (\\\\), "
            "and newlines (\\n). For large files use WriteSections (array of chunks), "
            "Bash heredoc (cat > file << 'EOF'), or Write with content_base64."
        )
    if not isinstance(parsed, dict):
        return None, "Error: tool arguments must be a JSON object"
    return parsed, None


def truncate(text: str) -> str:
    if len(text) <= MAX_TOOL_OUTPUT:
        return text
    return text[:MAX_TOOL_OUTPUT] + "\n... (output truncated)"


def resolve_path(path: str) -> Path:
    return Path(path).expanduser().resolve()


def display_path(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


def glob_pattern(pattern: str) -> str:
    if not pattern.startswith("**/"):
        return f"**/{pattern}"
    return pattern


def iter_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    if not root.is_dir():
        return []

    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIR_NAMES)
        for name in sorted(filenames):
            files.append(Path(dirpath) / name)
    return files


def matches_filename_glob(path: Path, glob_pattern: str | None) -> bool:
    if not glob_pattern:
        return True
    return fnmatch.fnmatch(path.name, glob_pattern)
