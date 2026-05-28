import argparse
import fnmatch
import json
import os
import re
import subprocess
from pathlib import Path

from openai import OpenAI

MAX_TOOL_OUTPUT = 50_000
SKIP_DIR_NAMES = {".git", ".venv", "node_modules", "__pycache__", ".ruff_cache"}

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "Read",
            "description": "Read and return the contents of a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The path to the file to read",
                    }
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "Write",
            "description": "Write content to a file",
            "parameters": {
            "type": "object",
            "required": ["file_path", "content"],
            "properties": {
                "file_path": {
                "type": "string",
                "description": "The path of the file to write to"
                },
                "content": {
                "type": "string",
                "description": "The content to write to the file"
                }
            }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "Bash",
            "description": "Execute a shell command",
            "parameters": {
                "type": "object",
                "required": ["command"],
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The command to execute",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "Grep",
            "description": "Search file contents for a regular expression pattern",
            "parameters": {
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
                        "description": "content: matching lines; files_with_matches: paths only; count: match counts per file",
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
        },
    },
    {
        "type": "function",
        "function": {
            "name": "Glob",
            "description": "Find files matching a glob pattern, sorted by modification time (newest first)",
            "parameters": {
                "type": "object",
                "required": ["glob_pattern"],
                "properties": {
                    "glob_pattern": {
                        "type": "string",
                        "description": "Glob pattern, e.g. '**/*.py' (recursive if no **/ prefix)",
                    },
                    "target_directory": {
                        "type": "string",
                        "description": "Directory to search (default: current directory)",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ListDir",
            "description": "List files and directories in a directory (non-recursive)",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_directory": {
                        "type": "string",
                        "description": "Directory to list (default: current directory)",
                    },
                },
            },
        },
    },
]


def execute_read(arguments: str) -> str:
    params = json.loads(arguments)
    with open(params["file_path"]) as f:
        return f.read()

def execute_write(arguments: str) -> str:
    params = json.loads(arguments)
    file_path = params["file_path"]
    parent = os.path.dirname(file_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(file_path, "w") as f:
        f.write(params["content"])
    return f"Successfully wrote to {file_path}"


def execute_bash(arguments: str) -> str:
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


def _truncate(text: str) -> str:
    if len(text) <= MAX_TOOL_OUTPUT:
        return text
    return text[:MAX_TOOL_OUTPUT] + "\n... (output truncated)"


def _resolve_path(path: str) -> Path:
    return Path(path).expanduser().resolve()


def _display_path(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


def _glob_pattern(pattern: str) -> str:
    if not pattern.startswith("**/"):
        return f"**/{pattern}"
    return pattern


def _iter_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    if not root.is_dir():
        return []

    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIR_NAMES)
        for name in sorted(filenames):
            files.append(Path(dirpath) / name)
    return files


def _matches_glob(path: Path, glob_pattern: str | None) -> bool:
    if not glob_pattern:
        return True
    return fnmatch.fnmatch(path.name, glob_pattern)


def execute_grep(arguments: str) -> str:
    params = json.loads(arguments)
    pattern_str = params["pattern"]
    root = _resolve_path(params.get("path", "."))
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
    files = [p for p in _iter_files(root) if _matches_glob(p, file_glob)]
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
                rel = _display_path(file_path, display_base)
                match_lines.append(f"{rel}:{line_no}:{line}")
                if head_limit is not None and len(match_lines) >= head_limit:
                    break
            if head_limit is not None and total >= head_limit:
                break

        if file_count:
            rel = _display_path(file_path, display_base)
            file_matches.append(rel)
            counts.append(f"{rel}:{file_count}")

        if head_limit is not None and total >= head_limit:
            break

    if output_mode == "files_with_matches":
        return _truncate("\n".join(file_matches) or "No matches found.")
    if output_mode == "count":
        body = "\n".join(counts) or "No matches found."
        if counts:
            body += f"\n\nTotal: {total} matches in {len(file_matches)} files"
        return _truncate(body)
    return _truncate("\n".join(match_lines) or "No matches found.")


def execute_glob(arguments: str) -> str:
    params = json.loads(arguments)
    pattern = _glob_pattern(params["glob_pattern"])
    root = _resolve_path(params.get("target_directory", "."))

    if not root.is_dir():
        return f"Error: not a directory: {root}"

    matches = [p for p in root.glob(pattern) if p.is_file()]
    matches.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    lines = [str(p.relative_to(root)) for p in matches]
    return _truncate("\n".join(lines) or "No files found.")


def execute_list_dir(arguments: str) -> str:
    params = json.loads(arguments)
    root = _resolve_path(params.get("target_directory", "."))

    if not root.is_dir():
        return f"Error: not a directory: {root}"

    entries: list[str] = []
    for entry in sorted(root.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
        if entry.name in SKIP_DIR_NAMES:
            continue
        kind = "dir" if entry.is_dir() else "file"
        entries.append(f"{kind}\t{entry.name}")

    return _truncate("\n".join(entries) or "(empty directory)")


def assistant_message_to_dict(message) -> dict:
    msg: dict = {"role": "assistant", "content": message.content}
    if message.tool_calls:
        msg["tool_calls"] = [
            {
                "id": tool_call.id,
                "type": tool_call.type,
                "function": {
                    "name": tool_call.function.name,
                    "arguments": tool_call.function.arguments,
                },
            }
            for tool_call in message.tool_calls
        ]
    return msg


def execute_tool(tool_call) -> str:
    name = tool_call.function.name
    args = tool_call.function.arguments
    handlers = {
        "Read": execute_read,
        "Write": execute_write,
        "Bash": execute_bash,
        "Grep": execute_grep,
        "Glob": execute_glob,
        "ListDir": execute_list_dir,
    }
    handler = handlers.get(name)
    if handler is None:
        raise RuntimeError(f"Unknown tool: {name}")
    return handler(args)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-p", required=True)
    args = p.parse_args()

    if not API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    messages = [{"role": "user", "content": args.p}]

    while True:
        chat = client.chat.completions.create(
            model="anthropic/claude-haiku-4.5",
            messages=messages,
            tools=TOOLS,
            max_tokens=4096,
        )

        if not chat.choices:
            raise RuntimeError("no choices in response")

        choice = chat.choices[0]
        message = choice.message
        messages.append(assistant_message_to_dict(message))

        if not message.tool_calls:
            if message.content is not None:
                print(message.content)
            break

        for tool_call in message.tool_calls:
            result = execute_tool(tool_call)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                }
            )


if __name__ == "__main__":
    main()
