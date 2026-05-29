import subprocess

from app.tools.base import Tool
from app.tools.utils import truncate


def _execute(params: dict) -> str:
    result = subprocess.run(
        params["command"],
        shell=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    output = result.stdout + result.stderr
    if result.returncode != 0 and not output.strip():
        return f"Command failed with exit code {result.returncode}"
    return truncate(output)


def _execute_safe(params: dict) -> str:
    try:
        return _execute(params)
    except subprocess.TimeoutExpired:
        return "Error: command timed out after 120 seconds"


tool = Tool(
    name="Bash",
    description=(
        "Execute a shell command. For large new files, prefer a heredoc: "
        "cat > path << 'EOF' then file body then EOF (quotes in EOF prevent expansion)."
    ),
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
    execute=_execute_safe,
)
