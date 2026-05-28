import sys
from pathlib import Path
from typing import Literal

from openai import APIConnectionError, APIStatusError, OpenAI, RateLimitError

from app.config import MAX_TOKENS, MODEL
from app.prompts import initial_messages
from app.spinner import Spinner
from app.tools import execute_tool_call, openai_tool_specs

LoopStatus = Literal["ok", "limit", "api"]


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


def _api_error_message(exc: Exception) -> str:
    if isinstance(exc, APIStatusError):
        if exc.status_code == 402:
            return (
                "OpenRouter: insufficient credits for this request (402). "
                "Lower --max-tokens (e.g. 2048), add credits, or raise your "
                "API key limit at https://openrouter.ai/settings/keys"
            )
        if exc.status_code == 429:
            return "OpenRouter: rate limited (429). Wait a moment and try again."
        detail = exc.message or str(exc)
        return f"OpenRouter API error ({exc.status_code}): {detail}"
    if isinstance(exc, RateLimitError):
        return "OpenRouter: rate limited. Wait a moment and try again."
    if isinstance(exc, APIConnectionError):
        return f"OpenRouter: connection failed — {exc}"
    return f"API error: {exc}"


def run_agent_loop(
    client: OpenAI,
    messages: list[dict],
    *,
    max_iterations: int,
    max_tokens: int,
    verbose: bool = False,
) -> tuple[str | None, LoopStatus]:
    """Run the agent until a final assistant message, limit, or API error."""
    with Spinner("Thinking", enabled=not verbose) as spinner:
        for iteration in range(1, max_iterations + 1):
            if verbose:
                print(f"[turn {iteration}/{max_iterations}]", file=sys.stderr)
            else:
                spinner.set_message(f"Thinking ({iteration}/{max_iterations})")

            try:
                chat = client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    tools=openai_tool_specs(),
                    max_tokens=max_tokens,
                )
            except Exception as e:
                return _api_error_message(e), "api"

            if not chat.choices:
                return "Error: model returned no choices.", "api"

            message = chat.choices[0].message
            messages.append(assistant_message_to_dict(message))

            if not message.tool_calls:
                return message.content, "ok"

            for tool_call in message.tool_calls:
                name = tool_call.function.name
                if verbose:
                    print(f"  → {name}", file=sys.stderr)
                else:
                    spinner.set_message(f"Running {name}…")
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
    return limit_msg, "limit"


def run_interactive(
    client: OpenAI,
    messages: list[dict],
    *,
    max_iterations: int,
    max_tokens: int,
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
        content, status = run_agent_loop(
            client,
            messages,
            max_iterations=max_iterations,
            max_tokens=max_tokens,
            verbose=verbose,
        )
        if content:
            print(f"\n{content}\n")
        if status == "api":
            print("(API error — not added to history; fix and retry)\n", file=sys.stderr)
            # Remove the user message so a retry does not duplicate context
            if messages and messages[-1].get("role") == "user":
                messages.pop()
        elif status == "limit":
            print(file=sys.stderr)
