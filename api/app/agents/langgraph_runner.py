"""Public entrypoints for LangGraph agent."""
from typing import Any, Dict

from app.services.rag import RAGService
from app.agents.langgraph.graph import build_agent_graph


_graph_instance = None


def get_compiled_graph(rag: RAGService):
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = build_agent_graph(rag)
    return _graph_instance


def run_agent_pipeline(
    query: str,
    rag: RAGService,
    *,
    use_rag: bool = True,
    use_sql: bool = True,
) -> Dict[str, Any]:
    graph = get_compiled_graph(rag)

    seed: Dict[str, Any] = {
        "query": query.strip(),
        "use_rag": use_rag,
        "use_sql": use_sql,
        "sources": [],
        "retrieval_iteration": 0,
        "hyde_text": "",
        "search_query": "",
        "refinement_hint": "",
        "answer": "",
    }

    out = graph.invoke(seed)

    all_steps = out.get("steps") or []
    if not isinstance(all_steps, list):
        all_steps = [all_steps]

    return {
        "answer": out.get("answer", "").strip(),
        "sources": out.get("sources") if use_rag else [],
        "sql_query": out.get("sql_query"),
        "steps": all_steps,
        "tool_calls": [
            {"name": x.get("step"), "detail": x.get("detail")}
            for x in all_steps
            if isinstance(x, dict)
        ],
    }
