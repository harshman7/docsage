"""Chat / agent endpoint helpers and v1 router."""
from typing import Dict, List

from fastapi import APIRouter, HTTPException

from app.schemas import QueryRequest, QueryResponse
from app.services.rag import RAGService
from app.agents.langgraph_runner import run_agent_pipeline

router = APIRouter(prefix="/chat", tags=["chat"])

_rag_service = None


def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service


def run_chat(request: QueryRequest) -> QueryResponse:
    rag = get_rag_service()
    hist: List[Dict[str, str]] = []
    if request.history:
        hist = [
            {"role": m.role, "content": m.content}
            for m in request.history
            if m.content and m.content.strip()
        ][-20:]
    result = run_agent_pipeline(
        request.query.strip(),
        rag,
        use_rag=request.use_rag,
        use_sql=request.use_sql,
        history=hist or None,
    )

    return QueryResponse(
        answer=result["answer"],
        sources=result.get("sources"),
        sql_query=result.get("sql_query"),
        steps=result.get("steps"),
        tool_calls=result.get("tool_calls"),
    )


@router.post("/insights", response_model=QueryResponse)
def chat_insights_v1(request: QueryRequest):
    try:
        return run_chat(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
