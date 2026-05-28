"""Agent tools registry.

To add a tool:
1. Create a module under app/tools/ with a module-level ``tool = Tool(...)``.
2. Import it below and append to ``ALL_TOOLS``.
"""

from app.tools import (
    bash,
    glob_file,
    grep,
    list_dir,
    read,
    str_replace,
    write,
)
from app.tools.base import Tool

ALL_TOOLS: tuple[Tool, ...] = (
    read.tool,
    write.tool,
    str_replace.tool,
    bash.tool,
    grep.tool,
    glob_file.tool,
    list_dir.tool,
)

_BY_NAME: dict[str, Tool] = {t.name: t for t in ALL_TOOLS}


def openai_tool_specs() -> list[dict]:
    return [t.to_openai_spec() for t in ALL_TOOLS]


def execute_tool(name: str, arguments: str) -> str:
    tool = _BY_NAME.get(name)
    if tool is None:
        raise RuntimeError(f"Unknown tool: {name}")
    return tool.execute(arguments)


def execute_tool_call(tool_call) -> str:
    return execute_tool(tool_call.function.name, tool_call.function.arguments)
