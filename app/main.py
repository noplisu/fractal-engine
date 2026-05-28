import argparse
import json
import os
import subprocess
import sys

from openai import OpenAI

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
    if tool_call.function.name == "Read":
        return execute_read(tool_call.function.arguments)
    elif tool_call.function.name == "Write":
        return execute_write(tool_call.function.arguments)
    elif tool_call.function.name == "Bash":
        return execute_bash(tool_call.function.arguments)
    raise RuntimeError(f"Unknown tool: {tool_call.function.name}")


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
