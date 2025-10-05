from pydantic import BaseModel, Field
from typing import List, Optional

CONTRACT_VERSION = "1.0"

class CommodityClassifyIn(BaseModel):
    title: str
    vendor_name: str
    vat_id: Optional[str] = None
    order_lines_text: List[str] = Field(default_factory=list)
    trace_id: Optional[str] = None
    contract_version: str = CONTRACT_VERSION

class AlternativeCG(BaseModel):
    id: int
    label: str
    confidence: float

class CommodityClassifyOut(BaseModel):
    suggested_commodity_group_id: Optional[int]
    confidence: float
    alternatives: List[AlternativeCG] = Field(default_factory=list)
    rationale: str = ""
    trace_id: str
    contract_version: str = CONTRACT_VERSION