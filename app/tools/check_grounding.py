from app.config import rag_paths
from app.rag_store import import_micro_rag_api
from app.tools.base import Tool
from app.tools.utils import truncate


def _execute(params: dict) -> str:
    answer = params.get("answer", "")
    if not isinstance(answer, str) or not answer.strip():
        return "Error: answer is required"

    api, err = import_micro_rag_api()
    if err:
        return err

    embeddings, chunks = rag_paths()
    try:
        result = api.check_grounding(
            answer,
            embeddings_path=embeddings,
            chunks_path=chunks,
        )
    except Exception as exc:
        return f"Error: CheckGrounding failed: {type(exc).__name__}: {exc}"

    if result.get("error"):
        return f"Error: {result['error']}"

    unmatched = result.get("unmatched") or []
    retrieved_count = result.get("retrieved_count", 0)
    if not unmatched:
        return (
            f"Grounding: all citations match retrieved sources "
            f"({retrieved_count} chunk(s) in the allowlist)."
        )
    lines = [
        "Grounding warnings — citations not in retrieved sources:",
        *[f"  - {citation}" for citation in unmatched],
        f"Allowlist size: {retrieved_count} retrieved chunk(s).",
        "Retrieve again or fix citations before the final answer.",
    ]
    return truncate("\n".join(lines))


tool = Tool(
    name="CheckGrounding",
    description=(
        "Validate [Book Title, Chapter] or [source, locator] citations in a draft "
        "answer against chunks returned by Retrieve in this session. "
        "Does not call a model. Retrieve first."
    ),
    parameters={
        "type": "object",
        "required": ["answer"],
        "properties": {
            "answer": {
                "type": "string",
                "description": "Draft answer containing [source, locator] citations",
            },
        },
    },
    execute=_execute,
)
