from app.config import SKIP_DIR_NAMES
from app.tools.base import Tool
from app.tools.utils import resolve_path, truncate


def _execute(params: dict) -> str:
    root = resolve_path(params.get("target_directory", "."))

    if not root.is_dir():
        return f"Error: not a directory: {root}"

    entries: list[str] = []
    for entry in sorted(root.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
        if entry.name in SKIP_DIR_NAMES:
            continue
        kind = "dir" if entry.is_dir() else "file"
        entries.append(f"{kind}\t{entry.name}")

    return truncate("\n".join(entries) or "(empty directory)")


tool = Tool(
    name="ListDir",
    description="List files and directories in a directory (non-recursive)",
    parameters={
        "type": "object",
        "properties": {
            "target_directory": {
                "type": "string",
                "description": "Directory to list (default: current directory)",
            },
        },
    },
    execute=_execute,
)
