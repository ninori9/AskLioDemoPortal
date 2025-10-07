from __future__ import annotations
from typing import Iterable, Optional

MAX_CHARS = 2000

def _norm(s: Optional[str]) -> str:
    if not s:
        return ""
    return " ".join(s.strip().split())

def build_request_embedding_text(
    *,
    title: str,
    vendor_name: str,
    vat_id: Optional[str],
    order_lines_text: Iterable[str],
) -> str:
    """
    Canonical, embedding-friendly serialization for procurement requests.
    Pure function: safe to import anywhere.
    """
    title_s = _norm(title)
    vendor_s = _norm(vendor_name)
    vat_s = _norm(vat_id) or "-"

    norm_lines = [f"- {_norm(l)}" for l in (order_lines_text or []) if _norm(l)]

    txt = [
        f"TITLE: {title_s}",
        f"VENDOR: {vendor_s}",
        f"VAT: {vat_s}",
        "ORDER_LINES:",
        *(norm_lines if norm_lines else ["-"]),
    ]
    out = "\n".join(txt).strip()
    return (out[:MAX_CHARS] + " …") if len(out) > MAX_CHARS else out