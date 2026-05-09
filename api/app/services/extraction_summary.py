"""
Turn structured extracted_data into compact plain text for RAG indexing.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

_DEFAULT_MAX = 2000


def extraction_to_index_text(
    extracted_data: Optional[Dict[str, Any]],
    *,
    filename: str = "",
    document_id: Optional[int] = None,
    max_chars: int = _DEFAULT_MAX,
) -> str:
    """
    Bounded plain-text summary for embedding alongside raw_text.
    Omits empty extracted_data.
    """
    if not extracted_data:
        return ""

    parts: List[str] = []
    if document_id is not None:
        parts.append(f"document_id: {document_id}")
    if filename:
        parts.append(f"filename: {filename}")

    vendor = extracted_data.get("vendor")
    if vendor:
        parts.append(f"vendor: {vendor}")

    inv = extracted_data.get("invoice_number")
    if inv:
        parts.append(f"invoice_number: {inv}")

    total = extracted_data.get("total")
    if total is not None:
        parts.append(f"total: {total}")

    dates = extracted_data.get("dates")
    if dates and isinstance(dates, list):
        parts.append(f"dates: {', '.join(str(d) for d in dates[:8])}")
    elif dates:
        parts.append(f"dates: {dates}")

    amounts = extracted_data.get("amounts")
    if amounts and isinstance(amounts, list):
        preview = amounts[:12]
        parts.append(f"amounts: {preview}")

    line_items = extracted_data.get("line_items")
    if line_items and isinstance(line_items, list):
        for i, li in enumerate(line_items[:6]):
            if not isinstance(li, dict):
                continue
            desc = li.get("description", "")
            amt = li.get("amount", "")
            parts.append(f"line_{i + 1}: {desc} | {amt}")

    meta = extracted_data.get("meta")
    if isinstance(meta, dict) and meta:
        # Skip huge blobs; keep short keys
        safe = {k: meta[k] for k in list(meta.keys())[:12] if k not in ("raw", "parsed")}
        try:
            meta_s = json.dumps(safe, default=str, ensure_ascii=False)[:400]
            if meta_s:
                parts.append(f"meta: {meta_s}")
        except Exception:
            pass

    block = "\n".join(str(p) for p in parts if p)
    if len(block) > max_chars:
        block = block[: max_chars - 3] + "..."
    return block.strip()
