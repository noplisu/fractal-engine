# Fractal Agent

A minimal CLI coding assistant powered by an LLM with tool calling. It reads files, writes files, and runs shell commands in an agent loop until the model produces a final answer.

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

```sh
./run.sh -p "list Python files in this directory"
```

The entry point is `app/main.py`.

## Tools

| Tool   | Description                    |
|--------|--------------------------------|
| Read   | Read a file by path            |
| Write  | Write content to a file        |
| Bash   | Run a shell command            |

## Project layout

```
app/main.py   # CLI, agent loop, and tool implementations
run.sh        # Local launcher
pyproject.toml
```
