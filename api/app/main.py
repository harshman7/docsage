"""
FastAPI entrypoint for DocSage.
"""
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import init_db
from app.schemas import QueryRequest, QueryResponse
from app.routers import analytics, anomalies, chat, compare, documents, export_routes, receipts, report_routes


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="DocSage",
    description="Intelligent Document Processing with agentic RAG and analytics APIs",
    version="2.0.0",
    lifespan=lifespan,
)

cors_origins = settings.cors_origins_list
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if "*" not in cors_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_v1 = APIRouter()
api_v1.include_router(analytics.router)
api_v1.include_router(anomalies.router)
api_v1.include_router(documents.router)
api_v1.include_router(compare.router)
api_v1.include_router(receipts.router)
api_v1.include_router(export_routes.router)
api_v1.include_router(report_routes.router)
api_v1.include_router(chat.router)
app.include_router(api_v1, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "message": "DocSage API",
        "version": "2.0.0",
        "prefix": "/api/v1",
        "legacy_chat": "/chat/insights",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/chat/insights", response_model=QueryResponse)
async def chat_insights_legacy(request: QueryRequest):
    """Backward-compatible path; prefer POST /api/v1/chat/insights."""
    try:
        from app.routers.chat import run_chat

        return run_chat(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=False,
    )
