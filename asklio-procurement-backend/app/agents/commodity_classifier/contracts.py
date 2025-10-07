from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field

CONTRACT_VERSION = "1.0"


class CommodityGroupRef(BaseModel):
    """Minimal, transport-friendly description of a commodity group."""
    id: int
    label: str
    category: Optional[str] = None


class CommodityClassifyIn(BaseModel):
    """
    Input to the commodity classifier.
    The agent receives *all* candidate commodity groups so it can rank/pick among them
    without coupling to persistence or internal models.
    """
    title: str
    vendor_name: str
    vat_id: Optional[str] = None
    order_lines_text: List[str] = Field(default_factory=list)
    available_commodity_groups: List[CommodityGroupRef] = Field(default_factory=list)
    # Trace & versioning
    trace_id: Optional[str] = None
    contract_version: str = CONTRACT_VERSION


class CommodityClassifyOut(BaseModel):
    """
    Output of the classifier.
    - suggested_commodity_group_id may be None if the agent abstains.
    - confidence is 0..1 for the chosen CG.
    """
    suggested_commodity_group_id: Optional[int]
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    trace_id: Optional[str] = None
    contract_version: str = CONTRACT_VERSION