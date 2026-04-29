"""Graph state definitions."""
from __future__ import annotations

import operator
from typing import Any, Annotated, Dict, List, Optional, TypedDict


class AgentState(TypedDict, total=False):
    query: str
    use_rag: bool
    use_sql: bool

    route: str
    steps: Annotated[List[Dict[str, Any]], operator.add]

    hyde_text: str
    search_query: str
    refinement_hint: str
    retrieval_iteration: int

    retrieved: List[Dict[str, Any]]
    reranked: List[Dict[str, Any]]
    grade_pass: bool

    sql_query: Optional[str]
    sql_answer: Optional[str]

    answer: str
    sources: List[Any]
