from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


# ---------- Inputs ----------
class PdfExtractorIn(BaseModel):
    """
    Input to the PDF extractor agent.
    - filename: original client filename (for logging/debugging)
    - content_type: should be 'application/pdf'
    - data: raw PDF file bytes
    - trace_id: optional correlation id for observability
    """
    filename: str
    content_type: str = Field(default="application/pdf")
    data: bytes
    trace_id: Optional[str] = None

    @field_validator("content_type")
    @classmethod
    def _ensure_pdf(cls, v: str) -> str:
        if v and v.lower() not in {"application/pdf", "application/x-pdf", "application/acrobat"}:
            # not hard-failing here; just normalize/allow, or raise if you prefer strictness
            return v
        return v


# ---------- Outputs (matches RequestDraftDto / OrderLineDto) ----------
class ExtractedOrderLine(BaseModel):
    description: str
    unitPriceCents: int
    quantity: float
    unit: str
    totalPriceCents: int


class PdfExtractorOut(BaseModel):
    """
    Result of the PDF extraction.
    Fields mirror the UI draft DTO. Any field can be omitted if not confidently extracted.
    """
    title: Optional[str] = None
    vendorName: Optional[str] = None
    vatNumber: Optional[str] = None
    totalPriceCents: Optional[int] = None
    shippingCents: Optional[int] = None # shipping fees
    taxCents: Optional[int] = None # sum of all taxes (MwSt/USt)
    totalDiscountCents: Optional[int] = None
    orderLines: List[ExtractedOrderLine] = Field(default_factory=list)
    trace_id: Optional[str] = None