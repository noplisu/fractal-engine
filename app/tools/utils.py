import fnmatch
import os
from pathlib import Path

from app.config import MAX_TOOL_OUTPUT, SKIP_DIR_NAMES


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
