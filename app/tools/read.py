import json

from app.tools.base import Tool


def _execute(arguments: str) -> str:
    params = json.loads(arguments)
    with open(params["file_path"]) as f:
        return f.read()


tool = Tool(
    name="Read",
    description="Read and return the contents of a file",
    parameters={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "The path to the file to read",
            }
        },
        "required": ["file_path"],
    },
    execute=_execute,
)
