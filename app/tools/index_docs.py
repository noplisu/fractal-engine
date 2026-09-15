import os

from app.config import rag_paths
from app.rag_store import import_micro_rag_api
from app.tools.base import Tool
from app.tools.utils import resolve_path, truncate


def _execute(params: dict) -> str:
    if not os.getenv("OPENAI_API_KEY"):
        return (
            "Error: OPENAI_API_KEY is not set. Embeddings use OpenAI "
            "(text-embedding-3-small), separate from OpenRouter chat."
        )

    source = resolve_path(params["path"])
    if not source.exists():
        return f"Error: path not found: {source}"

    api, err = import_micro_rag_api()
    if err:
        return err

    embeddings, chunks = rag_paths()
    try:
        summary = api.index_documents(
            source,
            embeddings_path=embeddings,
            chunks_path=chunks,
            replace=bool(params.get("replace", False)),
            chunk_size=int(params.get("chunk_size", 500)),
            overlap_tokens=int(params.get("overlap_tokens", 50)),
        )
    except Exception as exc:
        return f"Error: Index failed: {type(exc).__name__}: {exc}"

    files = "\n".join(f"  {p}" for p in summary["file_paths"])
    mode = "replaced" if summary["replaced"] else "appended"
    return truncate(
        f"Indexed {summary['files']} file(s) ({mode}): {summary['new_chunks']} "
        f"new chunks, {summary['total_chunks']} total.\n"
        f"Store: {summary['embeddings_path']}\n"
        f"Chunks: {summary['chunks_path']}\n"
        f"Sources:\n{files}"
    )


tool = Tool(
    name="Index",
    description=(
        "Chunk, embed, and add documents to this workspace's RAG index "
        "({cwd}/.fractal/rag). Use before Retrieve. Known Gutenberg filenames "
        "keep chapter splitters; other .txt/.md files are packed by paragraph. "
        "Does not write to micro-rag/data."
    ),
    parameters={
        "type": "object",
        "required": ["path"],
        "properties": {
            "path": {
                "type": "string",
                "description": "File or directory of .txt/.md documents to index",
            },
            "replace": {
                "type": "boolean",
                "description": (
                    "If true, rebuild the index from only this path. "
                    "If false (default), append to the existing index."
                ),
            },
            "chunk_size": {
                "type": "integer",
                "description": "Max tokens per chunk (default 500)",
            },
            "overlap_tokens": {
                "type": "integer",
                "description": "Token overlap between consecutive chunks (default 50)",
            },
        },
    },
    execute=_execute,
)
