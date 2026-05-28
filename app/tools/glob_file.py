import json

from app.tools.base import Tool
from app.tools.utils import glob_pattern, resolve_path, truncate


def _execute(arguments: str) -> str:
    params = json.loads(arguments)
    pattern = glob_pattern(params["glob_pattern"])
    root = resolve_path(params.get("target_directory", "."))

    if not root.is_dir():
        return f"Error: not a directory: {root}"

    matches = [p for p in root.glob(pattern) if p.is_file()]
    matches.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    lines = [str(p.relative_to(root)) for p in matches]
    return truncate("\n".join(lines) or "No files found.")


tool = Tool(
    name="Glob",
    description=(
        "Find files matching a glob pattern, "
        "sorted by modification time (newest first)"
    ),
    parameters={
        "type": "object",
        "required": ["glob_pattern"],
        "properties": {
            "glob_pattern": {
                "type": "string",
                "description": "Glob pattern, e.g. '**/*.py' (recursive if no **/ prefix)",
            },
            "target_directory": {
                "type": "string",
                "description": "Directory to search (default: current directory)",
            },
        },
    },
    execute=_execute,
)
