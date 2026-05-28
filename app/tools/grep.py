import re

from app.tools.base import Tool
from app.tools.utils import (
    display_path,
    iter_files,
    matches_filename_glob,
    resolve_path,
    truncate,
)


def _execute(params: dict) -> str:
    pattern_str = params["pattern"]
    root = resolve_path(params.get("path", "."))
    file_glob = params.get("glob")
    output_mode = params.get("output_mode", "content")
    head_limit = params.get("head_limit")
    flags = re.IGNORECASE if params.get("-i") else 0

    try:
        regex = re.compile(pattern_str, flags)
    except re.error as e:
        return f"Error: invalid pattern: {e}"

    if not root.exists():
        return f"Error: path not found: {root}"

    display_base = root if root.is_dir() else root.parent
    files = [p for p in iter_files(root) if matches_filename_glob(p, file_glob)]
    match_lines: list[str] = []
    file_matches: list[str] = []
    counts: list[str] = []
    total = 0

    for file_path in files:
        try:
            text = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            if output_mode == "content":
                match_lines.append(f"Error reading {file_path}: {e}")
            continue

        file_count = 0
        for line_no, line in enumerate(text.splitlines(), 1):
            if not regex.search(line):
                continue
            file_count += 1
            total += 1
            if output_mode == "content":
                rel = display_path(file_path, display_base)
                match_lines.append(f"{rel}:{line_no}:{line}")
                if head_limit is not None and len(match_lines) >= head_limit:
                    break
            if head_limit is not None and total >= head_limit:
                break

        if file_count:
            rel = display_path(file_path, display_base)
            file_matches.append(rel)
            counts.append(f"{rel}:{file_count}")

        if head_limit is not None and total >= head_limit:
            break

    if output_mode == "files_with_matches":
        return truncate("\n".join(file_matches) or "No matches found.")
    if output_mode == "count":
        body = "\n".join(counts) or "No matches found."
        if counts:
            body += f"\n\nTotal: {total} matches in {len(file_matches)} files"
        return truncate(body)
    return truncate("\n".join(match_lines) or "No matches found.")


tool = Tool(
    name="Grep",
    description="Search file contents for a regular expression pattern",
    parameters={
        "type": "object",
        "required": ["pattern"],
        "properties": {
            "pattern": {
                "type": "string",
                "description": "Regular expression to search for",
            },
            "path": {
                "type": "string",
                "description": "File or directory to search (default: current directory)",
            },
            "glob": {
                "type": "string",
                "description": "Filter filenames, e.g. '*.py' or '*.{ts,tsx}'",
            },
            "output_mode": {
                "type": "string",
                "enum": ["content", "files_with_matches", "count"],
                "description": (
                    "content: matching lines; files_with_matches: paths only; "
                    "count: match counts per file"
                ),
            },
            "-i": {
                "type": "boolean",
                "description": "Case-insensitive search",
            },
            "head_limit": {
                "type": "integer",
                "description": "Max matches to return (content/count modes)",
            },
        },
    },
    execute=_execute,
)
