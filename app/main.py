import argparse
import os
import sys
from pathlib import Path

from openai import OpenAI

from app.agent import run_agent_loop, run_interactive
from app.config import API_KEY, BASE_URL, DEFAULT_MAX_ITERATIONS
from app.prompts import initial_messages


def main() -> None:
    p = argparse.ArgumentParser(description="Fractal Agent — LLM coding assistant")
    p.add_argument("-p", "--prompt", help="Run a single prompt and exit")
    p.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Interactive mode (REPL); use with -p to run an initial prompt first",
    )
    p.add_argument(
        "--cwd",
        type=Path,
        default=Path.cwd(),
        help="Working directory for tools and context (default: current directory)",
    )
    p.add_argument(
        "--max-iterations",
        type=int,
        default=DEFAULT_MAX_ITERATIONS,
        metavar="N",
        help=f"Max model turns per user message (default: {DEFAULT_MAX_ITERATIONS})",
    )
    p.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Log model turns and tool calls to stderr",
    )
    args = p.parse_args()

    if not args.prompt and not args.interactive:
        p.error("provide -p/--prompt or use -i/--interactive")

    if args.max_iterations < 1:
        p.error("--max-iterations must be at least 1")

    if not API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    cwd = args.cwd.expanduser().resolve()
    if not cwd.is_dir():
        raise RuntimeError(f"--cwd is not a directory: {cwd}")

    os.chdir(cwd)

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    messages = initial_messages(cwd, args.max_iterations)

    if args.prompt:
        messages.append({"role": "user", "content": args.prompt})
        content, limited = run_agent_loop(
            client, messages, max_iterations=args.max_iterations, verbose=args.verbose
        )
        if content:
            print(content)
        if limited:
            sys.exit(1)
        if not args.interactive:
            return

    if args.interactive:
        run_interactive(
            client,
            messages,
            max_iterations=args.max_iterations,
            verbose=args.verbose,
        )


if __name__ == "__main__":
    main()
