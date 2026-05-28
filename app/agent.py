import sys
from pathlib import Path

from openai import OpenAI

from app.config import MODEL
from app.prompts import initial_messages
from app.tools import execute_tool_call, openai_tool_specs


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


def run_agent_loop(
    client: OpenAI,
    messages: list[dict],
    *,
    max_iterations: int,
    verbose: bool = False,
) -> tuple[str | None, bool]:
    """Run the agent until a final assistant message or iteration limit.

    Returns (assistant_text, hit_iteration_limit).
    """
    for iteration in range(1, max_iterations + 1):
        if verbose:
            print(f"[turn {iteration}/{max_iterations}]", file=sys.stderr)

        chat = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=openai_tool_specs(),
            max_tokens=4096,
        )

        if not chat.choices:
            raise RuntimeError("no choices in response")

        message = chat.choices[0].message
        messages.append(assistant_message_to_dict(message))

        if not message.tool_calls:
            return message.content, False

        for tool_call in message.tool_calls:
            if verbose:
                print(f"  → {tool_call.function.name}", file=sys.stderr)
            result = execute_tool_call(tool_call)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                }
            )

    limit_msg = (
        f"Stopped: reached the maximum of {max_iterations} model turns "
        "for this message. Ask a follow-up or raise --max-iterations."
    )
    messages.append({"role": "assistant", "content": limit_msg})
    return limit_msg, True


def run_interactive(
    client: OpenAI,
    messages: list[dict],
    *,
    max_iterations: int,
    verbose: bool,
) -> None:
    print(f"Fractal Agent (interactive) — {Path.cwd()}")
    print("Commands: exit, quit, /clear. Ctrl-D to quit.\n")

    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", ":q"):
            break
        if user_input == "/clear":
            messages[:] = initial_messages(Path.cwd(), max_iterations)
            print("Conversation cleared.\n")
            continue

        messages.append({"role": "user", "content": user_input})
        content, limited = run_agent_loop(
            client, messages, max_iterations=max_iterations, verbose=verbose
        )
        if content:
            print(f"\n{content}\n")
        if limited:
            print(file=sys.stderr)
