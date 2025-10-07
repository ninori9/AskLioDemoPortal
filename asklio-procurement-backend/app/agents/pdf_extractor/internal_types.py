from typing import Optional, List
from pydantic import BaseModel, Field

class LLMExtractedOrderLine(BaseModel):
    description: Optional[str] = None
    unit: Optional[str] = None
    quantity: Optional[float] = None
    unitPriceCents: Optional[int] = None
    totalPriceCents: Optional[int] = None


class LLMExtractedProcurementData(BaseModel):
    isProcurementRequest: bool = Field(
        ...,
        description="True if the document represents a procurement request or order-like document.",
    )
    title: Optional[str] = None
    vendorName: Optional[str] = None
    vatNumber: Optional[str] = None
    totalPriceCents: Optional[int] = None
    shippingCents: Optional[int] = None # shipping fees
    taxCents: Optional[int] = None # sum of all taxes (MwSt/USt)
    totalDiscountCents: Optional[int] = None
    orderLines: List[LLMExtractedOrderLine] = Field(default_factory=list)