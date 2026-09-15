import os

from app.config import rag_paths
from app.rag_store import import_micro_rag_api
from app.tools.base import Tool
from app.tools.utils import truncate


def _execute(params: dict) -> str:
    if not os.getenv("OPENAI_API_KEY"):
        return (
            "Error: OPENAI_API_KEY is not set. Query embeddings use OpenAI "
            "(text-embedding-3-small), separate from OpenRouter chat."
        )

    query = params.get("query", "")
    if not isinstance(query, str) or not query.strip():
        return "Error: query is required"

    k = int(params.get("k", 5))
    api, err = import_micro_rag_api()
    if err:
        return err

    embeddings, chunks = rag_paths()
    try:
        results = api.retrieve(
            query.strip(),
            embeddings_path=embeddings,
            chunks_path=chunks,
            k=k,
        )
    except FileNotFoundError as exc:
        return (
            "Error: no index in this workspace. Use Index on a directory of "
            f"documents first. ({exc})"
        )
    except Exception as exc:
        return f"Error: Retrieve failed: {type(exc).__name__}: {exc}"

    if not results:
        return "No chunks retrieved."
    return truncate(api.format_excerpts(results))


tool = Tool(
    name="Retrieve",
    description=(
        "Semantically search the workspace RAG index and return top-k excerpts "
        "with [source, locator] labels and scores. Does not generate an answer. "
        "Use Index first if there is no index. Prefer Retrieve for meaning; "
        "use Grep or Read to verify a quote in the source file."
    ),
    parameters={
        "type": "object",
        "required": ["query"],
        "properties": {
            "query": {
                "type": "string",
                "description": "Natural-language search query to embed",
            },
            "k": {
                "type": "integer",
                "description": "Number of chunks to return (default 5)",
            },
        },
    },
    execute=_execute,
)
