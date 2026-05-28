import json
import subprocess

from app.tools.base import Tool


def _execute(arguments: str) -> str:
    params = json.loads(arguments)
    result = subprocess.run(
        params["command"],
        shell=True,
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr
    if result.returncode != 0 and not output.strip():
        return f"Command failed with exit code {result.returncode}"
    return output


tool = Tool(
    name="Bash",
    description="Execute a shell command",
    parameters={
        "type": "object",
        "required": ["command"],
        "properties": {
            "command": {
                "type": "string",
                "description": "The command to execute",
            }
        },
    },
    execute=_execute,
)
