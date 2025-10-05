from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from app.schemas.commodity_group import CommodityGroupOut
from app.models.enums import RequestStatus

# ---------- Inputs ----------
class OrderLineIn(BaseModel):
    description: str = Field(min_length=1, max_length=300)
    unitPriceCents: int = Field(gt=0)
    quantity: int = Field(ge=1)
    unit: str = Field(min_length=1, max_length=50)

    @field_validator("unitPriceCents")
    @classmethod
    def _positive_cents(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("unitPriceCents must be > 0")
        return v

class ProcurementRequestCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    vendorName: str = Field(min_length=1, max_length=200)
    vatID: str = Field(min_length=2, max_length=32)
    commodityGroupID: int
    orderLines: List[OrderLineIn]

class ProcurementRequestUpdateIn(BaseModel):
    version: int = Field(ge=1)
    status: Optional[RequestStatus] = None
    commodityGroupID: Optional[int] = None

# ---------- Outputs ----------
class ProcurementRequestLiteOut(BaseModel):
    id: str
    title: str
    commodityGroup: CommodityGroupOut
    vendorName: str
    totalCostsCent: int
    requestorName: str
    requestorDepartment: str
    status: RequestStatus
    createdAt: str
    
class OrderLineOut(BaseModel):
    id: str
    description: str
    unitPriceCents: int
    quantity: int
    unit: str
    totalPriceCents: int

class StatusUpdateOut(BaseModel):
    id: str
    oldState: Optional[RequestStatus] = None
    newStatus: Optional[RequestStatus] = None
    oldCommodityGroup: Optional[CommodityGroupOut] = None
    newCommodityGroup: Optional[CommodityGroupOut] = None
    updatedAt: str
    updatedByName: str

class ProcurementRequestOut(BaseModel):
    id: str
    title: str
    commodityGroup: CommodityGroupOut
    vendorName: str
    vatNumber: str
    totalCostsCent: int
    requestorName: str
    requestorDepartment: str
    orderLines: List[OrderLineOut]
    status: RequestStatus
    updateHistory: List[StatusUpdateOut]
    createdAt: str
    version: int