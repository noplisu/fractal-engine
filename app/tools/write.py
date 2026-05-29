import base64
import os

from app.tools.base import Tool
from app.tools.utils import resolve_path


def _decode_content(params: dict) -> tuple[str | None, str | None]:
    if "content_base64" in params:
        raw = params["content_base64"]
        if not isinstance(raw, str):
            return None, "Error: content_base64 must be a string"
        try:
            return base64.b64decode(raw, validate=True).decode("utf-8"), None
        except (ValueError, UnicodeDecodeError) as e:
            return None, f"Error: invalid content_base64: {e}"
    if "content" in params:
        content = params["content"]
        if not isinstance(content, str):
            return None, "Error: content must be a string"
        return content, None
    return None, "Error: provide content or content_base64"


def _execute(params: dict) -> str:
    file_path = resolve_path(params["file_path"])
    content, err = _decode_content(params)
    if err:
        return err

    parent = file_path.parent
    if str(parent) not in (".", ""):
        parent.mkdir(parents=True, exist_ok=True)

    try:
        file_path.write_text(content, encoding="utf-8")
    except OSError as e:
        return f"Error: cannot write {file_path}: {e}"

    return f"Successfully wrote {len(content)} bytes to {file_path}"


tool = Tool(
    name="Write",
    description=(
        "Write content to a file (creates parent directories). "
        "For large text with quotes/newlines, use content_base64 instead of content."
    ),
    parameters={
        "type": "object",
        "required": ["file_path"],
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file to write",
            },
            "content": {
                "type": "string",
                "description": "File content (escape JSON: \\\", \\n, \\\\)",
            },
            "content_base64": {
                "type": "string",
                "description": "UTF-8 file content as standard base64 (preferred for large HTML)",
            },
        },
    },
    execute=_execute,
)
