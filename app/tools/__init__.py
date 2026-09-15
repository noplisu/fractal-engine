"""Agent tools registry.

To add a tool:
1. Create a module under app/tools/ with a module-level ``tool = Tool(...)``.
2. Import it below and append to ``ALL_TOOLS``.
"""

from app.tools import (
    bash,
    check_grounding,
    glob_file,
    grep,
    index_docs,
    list_dir,
    read,
    retrieve,
    str_replace,
    write,
    write_sections,
)
from app.tools.base import Tool
from app.tools.utils import parse_arguments

ALL_TOOLS: tuple[Tool, ...] = (
    read.tool,
    write.tool,
    write_sections.tool,
    str_replace.tool,
    bash.tool,
    grep.tool,
    glob_file.tool,
    list_dir.tool,
    index_docs.tool,
    retrieve.tool,
    check_grounding.tool,
)

_BY_NAME: dict[str, Tool] = {t.name: t for t in ALL_TOOLS}


def openai_tool_specs() -> list[dict]:
    return [t.to_openai_spec() for t in ALL_TOOLS]


def execute_tool(name: str, arguments: str | dict) -> str:
    tool = _BY_NAME.get(name)
    if tool is None:
        raise RuntimeError(f"Unknown tool: {name}")

    params, err = parse_arguments(arguments)
    if err:
        return err

    try:
        return tool.execute(params)
    except Exception as e:
        return f"Error: {name} failed: {type(e).__name__}: {e}"


def execute_tool_call(tool_call) -> str:
    return execute_tool(tool_call.function.name, tool_call.function.arguments)
