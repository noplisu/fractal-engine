from app.tools.base import Tool
from app.tools.utils import resolve_path


def _execute(params: dict) -> str:
    file_path = resolve_path(params["file_path"])
    sections = params["sections"]
    if not isinstance(sections, list) or not sections:
        return "Error: sections must be a non-empty array of strings"
    if not all(isinstance(s, str) for s in sections):
        return "Error: every section must be a string"

    separator = params.get("separator", "")
    if separator is not None and not isinstance(separator, str):
        return "Error: separator must be a string"
    separator = separator or ""

    content = separator.join(sections)

    parent = file_path.parent
    if str(parent) not in (".", ""):
        parent.mkdir(parents=True, exist_ok=True)

    try:
        file_path.write_text(content, encoding="utf-8")
    except OSError as e:
        return f"Error: cannot write {file_path}: {e}"

    return (
        f"Successfully wrote {len(content)} bytes to {file_path} "
        f"({len(sections)} section(s))"
    )


tool = Tool(
    name="WriteSections",
    description=(
        "Write a file by joining multiple string sections (best for large HTML). "
        "Each section should be a manageable chunk (e.g. head, nav, hero, footer). "
        "JSON-escape each section separately; avoids one giant escaped string."
    ),
    parameters={
        "type": "object",
        "required": ["file_path", "sections"],
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file to write",
            },
            "sections": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Ordered file chunks to concatenate",
            },
            "separator": {
                "type": "string",
                "description": "Text between sections (default: empty string)",
            },
        },
    },
    execute=_execute,
)
