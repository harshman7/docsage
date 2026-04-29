"""Compile LangGraph for agentic RAG."""
from __future__ import annotations

from langgraph.graph import END, StateGraph

from app.services.rag import RAGService
from app.agents.langgraph.state import AgentState
from app.agents.langgraph.nodes import (
    MAX_RETRIEVAL_LOOPS,
    node_grade,
    node_hyde_rewrite,
    node_metrics_fast,
    node_optional_sql,
    node_retrieve,
    node_rerank,
    node_route,
    node_sql_only,
    node_synthesize,
)


def _route_next(state: AgentState) -> str:
    r = state.get("route") or "agentic_rag"
    if r == "metrics_fast":
        return "metrics_fast"
    if r == "sql_only":
        return "sql_only"
    return "hyde"


def _grade_next(state: AgentState) -> str:
    if not state.get("grade_pass", False):
        it = state.get("retrieval_iteration") or 0
        if it < MAX_RETRIEVAL_LOOPS:
            return "hyde"
    return "optional_sql"


def build_agent_graph(rag: RAGService):
    graph = StateGraph(AgentState)

    graph.add_node("route", node_route)
    graph.add_node("metrics_fast", node_metrics_fast)
    graph.add_node("sql_only", node_sql_only)
    graph.add_node("hyde", node_hyde_rewrite)
    graph.add_node("retrieve", lambda s: node_retrieve(s, rag))
    graph.add_node("rerank", node_rerank)
    graph.add_node("grade", node_grade)
    graph.add_node("optional_sql", node_optional_sql)
    graph.add_node("synthesize", node_synthesize)

    graph.set_entry_point("route")
    graph.add_conditional_edges("route", _route_next)
    graph.add_edge("metrics_fast", END)
    graph.add_edge("sql_only", END)

    graph.add_edge("hyde", "retrieve")
    graph.add_edge("retrieve", "rerank")
    graph.add_edge("rerank", "grade")

    graph.add_conditional_edges("grade", _grade_next)
    graph.add_edge("optional_sql", "synthesize")
    graph.add_edge("synthesize", END)

    return graph.compile()
