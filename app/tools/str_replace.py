import json
from pathlib import Path

from app.tools.base import Tool
from app.tools.utils import display_path, resolve_path


def _execute(arguments: str) -> str:
    params = json.loads(arguments)
    path = resolve_path(params["path"])
    old_string = params["old_string"]
    new_string = params["new_string"]
    replace_all = params.get("replace_all", False)

    if not path.is_file():
        return f"Error: file not found: {path}"

    try:
        content = path.read_text(encoding="utf-8")
    except OSError as e:
        return f"Error: cannot read file: {e}"

    count = content.count(old_string)
    if count == 0:
        return (
            "Error: old_string not found in file. "
            "Use Read to verify the exact text, including whitespace."
        )

    if not replace_all and count > 1:
        return (
            f"Error: old_string appears {count} times. "
            "Use replace_all=true or include more surrounding context in old_string."
        )

    if replace_all:
        new_content = content.replace(old_string, new_string)
        replacements = count
    else:
        new_content = content.replace(old_string, new_string, 1)
        replacements = 1

    try:
        path.write_text(new_content, encoding="utf-8")
    except OSError as e:
        return f"Error: cannot write file: {e}"

    rel = display_path(path, Path.cwd())
    return f"Successfully replaced {replacements} occurrence(s) in {rel}"


tool = Tool(
    name="StrReplace",
    description=(
        "Replace an exact string in a file. "
        "old_string must be unique unless replace_all is true."
    ),
    parameters={
        "type": "object",
        "required": ["path", "old_string", "new_string"],
        "properties": {
            "path": {
                "type": "string",
                "description": "The path to the file to modify",
            },
            "old_string": {
                "type": "string",
                "description": "The exact text to replace",
            },
            "new_string": {
                "type": "string",
                "description": "The text to replace it with",
            },
            "replace_all": {
                "type": "boolean",
                "description": "Replace all occurrences (default: false)",
            },
        },
    },
    execute=_execute,
)
