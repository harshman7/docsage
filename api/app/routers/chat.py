"""Chat / agent endpoint helpers and v1 router."""
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException

from app.deps import get_current_user
from app.models import User
from app.schemas import QueryRequest, QueryResponse
from app.services.rag import RAGService
from app.agents.langgraph_runner import run_agent_pipeline

router = APIRouter(prefix="/chat", tags=["chat"])

_rag_services: Dict[int, RAGService] = {}


def get_rag_service(user_id: int) -> RAGService:
    if user_id not in _rag_services:
        _rag_services[user_id] = RAGService(user_id=user_id)
    return _rag_services[user_id]


def run_chat(request: QueryRequest, user_id: int) -> QueryResponse:
    rag = get_rag_service(user_id)
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
        user_id=user_id,
    )

    return QueryResponse(
        answer=result["answer"],
        sources=result.get("sources"),
        sql_query=result.get("sql_query"),
        steps=result.get("steps"),
        tool_calls=result.get("tool_calls"),
    )


@router.post("/insights", response_model=QueryResponse)
def chat_insights_v1(request: QueryRequest, current_user: User = Depends(get_current_user)):
    try:
        return run_chat(request, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
