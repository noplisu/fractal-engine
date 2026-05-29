# Fractal Agent

A minimal CLI coding assistant powered by an LLM with tool calling. It searches the codebase, reads and writes files, runs shell commands, and loops until the model produces a final answer.

## Requirements

- [uv](https://docs.astral.sh/uv/)
- Python 3.14
- An [OpenRouter](https://openrouter.ai/) API key

## Setup

```sh
export OPENROUTER_API_KEY="your-key-here"
# optional:
# export OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"
```

Install dependencies:

```sh
uv sync
```

## Usage

Single prompt:

```sh
./run.sh -p "list Python files in this directory"
```

Interactive mode (multi-turn REPL):

```sh
./run.sh -i
```

Run one prompt, then continue interactively:

```sh
./run.sh -p "summarize app/main.py" -i
```

Options:

| Flag | Description |
|------|-------------|
| `-i`, `--interactive` | Start interactive mode after any `-p` prompt |
| `--cwd PATH` | Working directory for tools and system context |
| `--max-iterations N` | Max model turns per user message (default: 25) |
| `--max-tokens N` | Max tokens per model response (default: 8192) |
| `-v`, `--verbose` | Log turns and tool calls to stderr |
| `FRACTAL_MODEL` | OpenRouter model id (default: `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free`) |
| `FRACTAL_MAX_TOKENS` | Default for `--max-tokens` |

If OpenRouter returns **402 (insufficient credits)**, lower `--max-tokens` (e.g. `2048`) or add credits to your key.

The entry point is `app/main.py`.

## Tools

| Tool    | Description                                      |
|---------|--------------------------------------------------|
| Grep    | Search file contents (regex, optional glob)      |
| Glob    | Find files by glob pattern                       |
| ListDir | List entries in a directory                      |
| Read       | Read a file by path                              |
| Write          | Write content to a file (or content_base64)      |
| WriteSections  | Write a file from an array of string sections    |
| StrReplace     | Replace an exact string in a file                |
| Bash       | Run a shell command                              |

## Project layout

```
app/
  main.py          # CLI entry point
  config.py        # Environment and defaults
  prompts.py       # System prompt
  agent.py         # Agent loop and interactive REPL
  tools/           # One module per tool (see tools/__init__.py)
run.sh
pyproject.toml
```

### Adding a tool

1. Create `app/tools/my_tool.py` with a module-level `tool = Tool(...)`.
2. Register it in `app/tools/__init__.py` (`ALL_TOOLS` tuple).
