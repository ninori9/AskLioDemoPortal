from typing import List, Optional

from app.schemas.procurement import (
    ProcurementRequestLiteOut,
    ProcurementRequestOut,
    OrderLineOut,
    StatusUpdateOut,
)
from app.schemas.commodity_group import CommodityGroupOut
from app.models.procurement_request import ProcurementRequest
from app.models.procurement_request_update import ProcurementRequestUpdate
from app.models.order_line import OrderLine

# ---------- Small helpers ----------

def _to_commodity_group_out(orm_cg) -> CommodityGroupOut:
    """Map ORM CommodityGroup to API DTO."""
    return CommodityGroupOut.model_validate(orm_cg)


def _format_requestor_full_name(req: ProcurementRequest) -> str:
    """Return the 'Firstname Lastname' of the requestor, or an em dash if missing."""
    if req.created_by:
        return f"{req.created_by.firstname} {req.created_by.lastname}"
    return "—"


def _requestor_department_name(req: ProcurementRequest) -> str:
    """Return the requestor's department name, or an em dash if missing."""
    if req.created_by and req.created_by.department:
        return req.created_by.department.name
    return "—"


def _iso_datetime(dt) -> str:
    """Safely convert a datetime to ISO string (empty if None)."""
    return dt.isoformat() if dt else ""


# ---------- Public mappers (ORM -> DTO) ----------

def to_lite_out(request: ProcurementRequest) -> ProcurementRequestLiteOut:
    """
    Map a ProcurementRequest to its 'lite' DTO used in list views.
    Includes commodity group and requestor context.
    """
    commodity_group_out = _to_commodity_group_out(request.commodity_group)
    requestor_name = _format_requestor_full_name(request)
    requestor_department = _requestor_department_name(request)

    return ProcurementRequestLiteOut(
        id=request.id,
        title=request.title,
        commodityGroup=commodity_group_out,
        vendorName=request.vendorName,
        totalCostsCent=request.totalCosts,
        requestorName=requestor_name,
        requestorDepartment=requestor_department,
        status=request.status,
        createdAt=_iso_datetime(request.created_at),
    )


def _to_order_line_out(line: OrderLine) -> OrderLineOut:
    """Map an OrderLine ORM row to its DTO."""
    return OrderLineOut(
        id=line.id,
        description=line.description,
        unitPriceCents=line.unitPriceCents,
        quantity=line.quantity,
        unit=line.unit,
        totalPriceCents=line.totalPriceCents,
    )


def to_status_update_out(update: ProcurementRequestUpdate) -> StatusUpdateOut:
    """
    Map an audit update row to its DTO, including optional old/new commodity groups.
    """
    old_cg_out: Optional[CommodityGroupOut] = (
        _to_commodity_group_out(update.old_commodity_group) if update.old_commodity_group else None
    )
    new_cg_out: Optional[CommodityGroupOut] = (
        _to_commodity_group_out(update.new_commodity_group) if update.new_commodity_group else None
    )
    
    name = "—"
    if update.updated_by:
        first = getattr(update.updated_by, "firstname", "") or ""
        last  = getattr(update.updated_by, "lastname", "") or ""
        name = f"{first} {last}".strip() or "—"

    return StatusUpdateOut(
        id=update.id,
        oldState=update.oldStatus,
        newStatus=update.newStatus,
        oldCommodityGroup=old_cg_out,
        newCommodityGroup=new_cg_out,
        updatedAt=_iso_datetime(update.updated_at),
        updatedByName=name
    )


def to_detail_out(
    request: ProcurementRequest,
    updates: List[ProcurementRequestUpdate],
) -> ProcurementRequestOut:
    """
    Map a ProcurementRequest to its detailed DTO (used for the detail view).
    Includes commodity group, requestor context, order lines, and audit history.
    """
    commodity_group_out = _to_commodity_group_out(request.commodity_group)
    requestor_name = _format_requestor_full_name(request)
    requestor_department = _requestor_department_name(request)

    order_lines_out: List[OrderLineOut] = [
        _to_order_line_out(line) for line in (request.order_lines or [])
    ]
    history_out: List[StatusUpdateOut] = [to_status_update_out(u) for u in updates]

    return ProcurementRequestOut(
        id=request.id,
        title=request.title,
        commodityGroup=commodity_group_out,
        vendorName=request.vendorName,
        vatNumber=request.vatID,
        totalCostsCent=request.totalCosts,
        requestorName=requestor_name,
        requestorDepartment=requestor_department,
        orderLines=order_lines_out,
        status=request.status,
        updateHistory=history_out,
        createdAt=_iso_datetime(request.created_at),
        version=request.version or 1,
    )