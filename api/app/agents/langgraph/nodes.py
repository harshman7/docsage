"""Graph node functions for agentic RAG."""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from app.services.llm_service import call_llm
from app.services.rag import RAGService
from app.services.sql_tools import SQLTools
from app.services.insights import InsightsService
from app.agents.langgraph.state import AgentState

MAX_RETRIEVAL_LOOPS = 3
RERANK_POOL = 24
RERANK_KEEP = 8
RETRIEVE_K = 40

_ce_model = None


def _cross_encoder():
    global _ce_model
    if _ce_model is None:
        from sentence_transformers import CrossEncoder

        _ce_model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _ce_model


def node_route(state: AgentState) -> Dict[str, Any]:
    q = state["query"].lower()
    hints = [
        "top vendor",
        "vendor stat",
        "vendors by spend",
        "top vendors",
        "category breakdown",
        "spending by category",
        "by category",
    ]
    if any(h in q for h in hints):
        return {
            "route": "metrics_fast",
            "steps": [{"step": "route", "detail": "metrics_fast_keyword"}],
        }

    sql_hints = [
        "total",
        "sum",
        "count",
        "average",
        "monthly",
        "how much",
        "list all",
        "select",
    ]
    use_sql = state.get("use_sql", True)
    use_rag = state.get("use_rag", True)
    needs_sql = any(k in q for k in sql_hints)

    if needs_sql and use_sql and not use_rag:
        return {
            "route": "sql_only",
            "steps": [{"step": "route", "detail": "sql_only"}],
        }

    return {
        "route": "agentic_rag",
        "steps": [{"step": "route", "detail": "agentic_rag"}],
    }


def node_metrics_fast(state: AgentState) -> Dict[str, Any]:
    q = state["query"].lower()
    try:
        if "category" in q or "breakdown" in q:
            data = InsightsService.get_category_breakdown()
            text = "Category breakdown:\n" + "\n".join(
                f"- {row['category']}: ${row['total_spend']:,.2f}"
                for row in data[:15]
            )
        else:
            stats = InsightsService.get_vendor_stats(limit=15)
            text = "Top vendors by spend:\n" + "\n".join(
                f"{i}. {r['vendor']}: ${r['total_spend']:,.2f}"
                for i, r in enumerate(stats, 1)
            )
        return {
            "answer": text,
            "sources": [],
            "steps": [{"step": "metrics_fast", "detail": "precomputed_metrics"}],
        }
    except Exception as e:
        return {
            "answer": f"Error loading metrics: {e}",
            "sources": [],
            "steps": [{"step": "metrics_fast", "detail": str(e)}],
        }


def _conversation_block(state: AgentState) -> str:
    hist = state.get("history") or []
    if not hist:
        return ""
    lines: List[str] = []
    for m in hist[-10:]:
        if not isinstance(m, dict):
            continue
        role = str(m.get("role", "user"))
        content = str(m.get("content", "")).strip()
        if content:
            lines.append(f"{role}: {content}")
    if not lines:
        return ""
    return "Conversation so far:\n" + "\n".join(lines) + "\n\n"


def _generate_sql(state: AgentState) -> str | None:
    q = state["query"]
    conv = _conversation_block(state)
    try:
        ctx = SQLTools.get_multitable_sql_llm_context(sample_rows=3)
        prompt = f"""Given schemas and samples for tables `documents` and `transactions`, output ONE SQL SELECT only for:
{q}

{conv}Relationship: `transactions.document_id` references `documents.id` (JOIN allowed).

documents columns (schema):
{json.dumps(ctx["documents_schema"], indent=2)}

transactions columns (schema):
{json.dumps(ctx["transactions_schema"], indent=2)}

documents sample rows (raw_text truncated; extracted_data may be JSON):
{json.dumps(ctx["documents_sample"], indent=2, default=str)}

transactions sample rows:
{json.dumps(ctx["transactions_sample"], indent=2, default=str)}

Rules: SELECT only; JOIN documents and transactions when the question needs both; use exact column names from the schemas; SQLite and PostgreSQL compatible SQL preferred (avoid dialect-only functions unless necessary); no markdown fences."""
        raw = call_llm(prompt, timeout=25).strip()
        raw = re.sub(r"```sql\s*", "", raw)
        raw = re.sub(r"```\s*", "", raw).strip()
        return raw if raw.lower().startswith("select") else None
    except Exception:
        return None


def node_sql_only(state: AgentState) -> Dict[str, Any]:
    q = state["query"]
    sql = _generate_sql(state)
    if not sql:
        return {
            "answer": "Could not generate a valid SQL query for this question.",
            "sql_query": None,
            "steps": [{"step": "sql_only", "detail": "generate_failed"}],
        }
    try:
        rows = SQLTools.execute_query(sql)
        snippet = json.dumps(rows[:20], default=str)
        summary = call_llm(
            f"{_conversation_block(state)}User question: {q}\nSQL result JSON:\n{snippet}\nSummarize clearly for the user.",
            timeout=30,
        )
        return {
            "answer": summary,
            "sql_query": sql,
            "sources": [],
            "steps": [{"step": "sql_only", "detail": "executed"}],
        }
    except Exception as e:
        return {
            "answer": f"SQL error: {e}",
            "sql_query": sql,
            "sources": [],
            "steps": [{"step": "sql_only", "detail": str(e)}],
        }


def node_hyde_rewrite(state: AgentState) -> Dict[str, Any]:
    q = state["query"]
    prev = state.get("refinement_hint", "")
    conv = _conversation_block(state)
    hyde = call_llm(
        f"{conv}Write a short hypothetical passage (2-4 sentences) that would answer this:\n{q}",
        timeout=25,
    )
    rewritten = call_llm(
        f"{conv}{('Refine search because: ' + prev + chr(10)) if prev else ''}"
        f"Rewrite this user question into a standalone search query for a vector DB (one line):\n{q}",
        timeout=20,
    )
    search_q = (hyde[:400] + " " + rewritten.strip())[:1024].strip()

    step = {"step": "hyde_rewrite", "detail": "hyde+rewrite"}

    out: Dict[str, Any] = {
        "hyde_text": hyde,
        "search_query": search_q,
        "steps": [step],
    }
    return out


def node_retrieve(state: AgentState, rag: RAGService) -> Dict[str, Any]:
    if not state.get("use_rag", True):
        return {"retrieved": [], "steps": [{"step": "retrieve", "detail": "skipped"}]}
    sq = state.get("search_query") or state["query"]
    hits = rag.search(sq, k=RETRIEVE_K)

    iteration = state.get("retrieval_iteration") or 0
    iteration += 1

    hits = [_normalize_hit(h) for h in hits][:RETRIEVE_K]

    return {
        "retrieved": hits,
        "reranked": [],  # next node fills reranked
        "retrieval_iteration": iteration,
        "steps": [
            {
                "step": "retrieve",
                "detail": f"faiss_k={len(hits)} iter={iteration}",
            }
        ],
    }


def _normalize_hit(h: Dict[str, Any]) -> Dict[str, Any]:
    doc = h.get("document", {})
    text = doc.get("text", "") or ""
    return {
        "document": doc,
        "score": float(h.get("score", 1.0)),
        "snippet": text[:800],
        "distance": float(h.get("score", 1.0)),
    }


def node_rerank(state: AgentState) -> Dict[str, Any]:
    retrieved = state.get("retrieved", [])
    if not retrieved:
        return {"reranked": [], "steps": [{"step": "rerank", "detail": "empty"}]}

    pairs = retrieved[:RERANK_POOL]
    q = state["query"]
    texts = []
    for item in pairs:
        t = item.get("snippet") or ""
        texts.append([q, t])

    scores = []
    try:
        model = _cross_encoder()
        scores = model.predict(texts).tolist()
    except Exception:
        scores = [-float(item.get("distance", 999)) for item in pairs]

    for i, s in enumerate(scores):
        pairs[i]["rerank_score"] = float(s)
    pairs_sorted = sorted(pairs, key=lambda x: -x["rerank_score"])[:RERANK_KEEP]

    norm = [
        {
            "document": x["document"],
            "score": x["rerank_score"],
            "snippet": x.get("snippet", "")[:800],
        }
        for x in pairs_sorted
    ]
    sources = []
    for item in norm:
        d = item.get("document") or {}
        sources.append(
            {
                "document_id": d.get("id"),
                "filename": d.get("filename"),
                "chunk_index": d.get("chunk_index"),
                "chunk_type": d.get("chunk_type"),
                "score": item.get("score"),
            }
        )

    return {"reranked": norm, "sources": sources,
            "steps": [{"step": "rerank", "detail": f"top_{len(norm)}"}]
            }


def node_grade(state: AgentState) -> Dict[str, Any]:
    chunks = "\n".join(
        (r.get("snippet") or "")[:300] for r in state.get("reranked", [])[:5]
    )
    judge = call_llm(
        (
            f"{_conversation_block(state)}User question: {state['query']}\n\nPassages:\n{chunks}\n\n"
            'Reply JSON only: {"sufficient": true|false, "hint": "..."}'
        ),
        timeout=20,
    )
    ok = "true" in judge.lower()
    hint = ""
    try:
        m = re.search(r"\{[\s\S]*\}", judge)
        if m:
            parsed = json.loads(m.group())
            ok = bool(parsed.get("sufficient", ok))
            hint = str(parsed.get("hint") or "")
    except Exception:
        hint = ""

    return {
        "grade_pass": ok,
        "refinement_hint": hint,
        "steps": [{"step": "grade_documents", "detail": judge[:200]}],
    }


def node_optional_sql(state: AgentState) -> Dict[str, Any]:
    if not state.get("use_sql", True):
        return {"sql_query": None, "sql_answer": None, 
                "steps": [{"step": "sql_hybrid", "detail": "skipped"}]}

    q = state["query"]
    if not any(
        k in q.lower()
        for k in [
            "total",
            "sum",
            "count",
            "average",
            "transaction",
            "spend",
            "document",
            "invoice",
            "file",
        ]
    ):
        return {
            "sql_query": None,
            "sql_answer": None,
            "steps": [{"step": "sql_hybrid", "detail": "skipped_keywords"}],
        }

    sql = _generate_sql(state)
    if not sql:
        return {"sql_query": None, "sql_answer": None}

    try:
        rows = SQLTools.execute_query(sql)
        snippet = json.dumps(rows[:25], default=str)
        return {
            "sql_query": sql,
            "sql_answer": snippet,
            "steps": [{"step": "sql_hybrid", "detail": "ok"}],
        }
    except Exception as e:
        return {
            "sql_query": sql,
            "sql_answer": f"(sql error {e})",
            "steps": [{"step": "sql_hybrid", "detail": str(e)}],
        }


def node_synthesize(state: AgentState) -> Dict[str, Any]:
    ctx_parts = []
    for r in state.get("reranked", [])[:6]:
        ctx_parts.append((r.get("snippet") or ""))
    rag_block = "\n---\n".join(ctx_parts) if ctx_parts else "(no retrieval)"
    sql_ans = state.get("sql_answer")

    conv = _conversation_block(state)
    sql_useful = bool(
        sql_ans
        and str(sql_ans).strip()
        and not str(sql_ans).strip().lower().startswith("(sql error")
    )

    syn = []
    syn.append(
        call_llm(
            f"""You are DocSage. Answer using retrieval context and optional SQL facts below.

{conv}Question: {state['query']}

Retrieval excerpts (may be empty):
{rag_block}

SQL JSON facts (may be empty):
{sql_ans if sql_useful else "none"}

Rules:
- If there are no retrieval excerpts and no usable SQL facts, say clearly that you did not find relevant data in the document index or database — do not invent amounts, vendors, or filenames.
- When using passages, cite with **filename** and **document_id** when inferable from the excerpts (e.g. `invoice.pdf` (document_id 12)).
- Prefer SQL facts for numeric aggregates when both overlap with retrieval.
- Markdown answer.""",
            timeout=45,
        )
    )

    ans = syn[0] if syn else "(no LLM)"
    enriched_sources = []
    for r in state.get("reranked", [])[:10]:
        d = r.get("document") or {}
        enriched_sources.append(
            {
                "document_id": d.get("id"),
                "filename": d.get("filename"),
                "chunk_index": d.get("chunk_index"),
                "chunk_type": d.get("chunk_type"),
                "score": r.get("score"),
            }
        )

    return {
        "answer": ans.strip(),
        "sources": enriched_sources if state.get("use_rag") else [],
        "steps": [{"step": "synthesize", "detail": "final"}],
    }
