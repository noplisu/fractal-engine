import os

from app.tools.base import Tool


def _execute(params: dict) -> str:
    file_path = params["file_path"]
    parent = os.path.dirname(file_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(file_path, "w") as f:
        f.write(params["content"])
    return f"Successfully wrote to {file_path}"


tool = Tool(
    name="Write",
    description="Write content to a file",
    parameters={
        "type": "object",
        "required": ["file_path", "content"],
        "properties": {
            "file_path": {
                "type": "string",
                "description": "The path of the file to write to",
            },
            "content": {
                "type": "string",
                "description": "The content to write to the file",
            },
        },
    },
    execute=_execute,
)
