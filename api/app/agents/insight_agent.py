"""
Legacy-compatible agent façade. Prefer `langgraph_runner.run_agent_pipeline`.
"""
from typing import Any, Dict, Optional

from app.services.rag import RAGService
from app.agents.langgraph_runner import run_agent_pipeline


class DocSageAgent:
    """Thin wrapper preserving the historical class name."""

    def __init__(self, rag_service: Optional[RAGService] = None, enable_cache: bool = False):
        self.rag_service = rag_service or RAGService()
        self.enable_cache = enable_cache

    def process_query(
        self,
        query: str,
        use_rag: bool = True,
        use_sql: bool = True,
    ) -> Dict[str, Any]:
        return run_agent_pipeline(
            query,
            self.rag_service,
            use_rag=use_rag,
            use_sql=use_sql,
        )
