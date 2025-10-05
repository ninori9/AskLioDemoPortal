from __future__ import annotations

from typing import List, Optional
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.procurement_request import ProcurementRequest
from app.models.procurement_request_update import ProcurementRequestUpdate
from app.models.order_line import OrderLine
from app.models.commodity_group import CommodityGroup
from app.models.enums import RequestStatus
from app.models.user import User

from app.schemas.procurement import (
    ProcurementRequestCreate,
    ProcurementRequestUpdateIn,
    ProcurementRequestLiteOut,
    ProcurementRequestOut,
)
from app.services.mappers import to_lite_out, to_detail_out
from app.services.auth import ensure_manager


# =========================
# Internal Loaders (helpers)
# =========================

def _base_query_with_common_joins(db: Session):
    """
    Build a query for ProcurementRequest with the joins we need for list views:
    - commodity_group
    - created_by (including department)
    """
    return (
        db.query(ProcurementRequest)
        .options(
            joinedload(ProcurementRequest.commodity_group),
            joinedload(ProcurementRequest.created_by).joinedload(User.department),
        )
    )


def _load_request_with_details(db: Session, request_id: str) -> ProcurementRequest | None:
    """
    Load a single ProcurementRequest and all details needed for the detail view:
    - commodity_group
    - created_by (+ department)
    - order_lines
    """
    return (
        db.query(ProcurementRequest)
        .options(
            joinedload(ProcurementRequest.commodity_group),
            joinedload(ProcurementRequest.created_by).joinedload(User.department),
            joinedload(ProcurementRequest.order_lines),
        )
        .filter(ProcurementRequest.id == request_id)
        .first()
    )


def _load_audit_trail(db: Session, request_id: str) -> List[ProcurementRequestUpdate]:
    """
    Load audit trail entries for a request, ordered chronologically.
    Includes joined commodity groups to render deltas.
    """
    return (
        db.query(ProcurementRequestUpdate)
        .options(
            joinedload(ProcurementRequestUpdate.old_commodity_group),
            joinedload(ProcurementRequestUpdate.new_commodity_group),
            joinedload(ProcurementRequestUpdate.updated_by),
        )
        .filter(ProcurementRequestUpdate.requestID == request_id)
        .order_by(ProcurementRequestUpdate.updated_at.asc())
        .all()
    )


# =============
# Public Service
# =============

def list_requests(
    db: Session,
    status_filter: Optional[RequestStatus],
) -> List[ProcurementRequestLiteOut]:
    """
    Return a list of requests (optionally filtered by status), newest first.
    """
    query = _base_query_with_common_joins(db).order_by(ProcurementRequest.created_at.desc())
    if status_filter:
        query = query.filter(ProcurementRequest.status == status_filter)

    requests = query.all()
    return [to_lite_out(request) for request in requests]


def list_my_requests(
    db: Session,
    user: User,
    status_filter: Optional[RequestStatus],
    limit: int,
) -> List[ProcurementRequestLiteOut]:
    """
    Return the current user's recent requests (optionally filtered by status), newest first.
    """
    query = (
        _base_query_with_common_joins(db)
        .filter(ProcurementRequest.createdByUserID == user.id)
        .order_by(ProcurementRequest.created_at.desc())
    )
    if status_filter:
        query = query.filter(ProcurementRequest.status == status_filter)

    requests = query.limit(limit).all()
    return [to_lite_out(request) for request in requests]


def create_request(
    db: Session,
    body: ProcurementRequestCreate,
    user: User,
) -> ProcurementRequestLiteOut:
    """
    Create a new request with order lines, compute totals, and return the lite DTO.
    """
    # Validate commodity group
    commodity_group = (
        db.query(CommodityGroup).filter(CommodityGroup.id == body.commodityGroupID).first()
    )
    if not commodity_group:
        raise HTTPException(status_code=404, detail="Commodity group not found")

    # Build order lines & compute total in cents
    total_cost_cents = 0
    order_line_rows: list[OrderLine] = []

    for line in body.orderLines:
        line_total_cents = line.unitPriceCents * line.quantity
        total_cost_cents += line_total_cents

        order_line_rows.append(
            OrderLine(
                id=str(uuid4()),
                description=line.description,
                unitPriceCents=line.unitPriceCents,
                quantity=line.quantity,
                unit=line.unit,
                totalPriceCents=line_total_cents,
            )
        )

    # Create request row
    new_request = ProcurementRequest(
        id=str(uuid4()),
        title=body.title,
        vendorName=body.vendorName,
        vatID=body.vatID,
        commodityGroupID=body.commodityGroupID,
        totalCosts=total_cost_cents,
        createdByUserID=user.id,
        order_lines=order_line_rows,
    )
    db.add(new_request)
    db.commit()
    db.refresh(new_request)

    return to_lite_out(new_request)


def update_request(
    db: Session,
    request_id: str,
    body: ProcurementRequestUpdateIn,
    user: User,
) -> ProcurementRequestLiteOut:
    """
    Update status and/or commodity group (Managers only).
    Writes an audit entry only if something changed.
    Uses optimistic concurrency via `version`.
    """
    ensure_manager(user)  # authorization

    # Require at least one change
    if body.status is None and body.commodityGroupID is None:
        raise HTTPException(status_code=400, detail="No changes provided")

    procurement_request = (
        _base_query_with_common_joins(db).filter(ProcurementRequest.id == request_id).first()
    )
    if not procurement_request:
        raise HTTPException(status_code=404, detail="Request not found")

    # Optimistic concurrency
    procurement_request.version = procurement_request.version or 1
    if body.version != procurement_request.version:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Version mismatch. Current version is {procurement_request.version}",
        )

    # Validate commodity group if provided
    if body.commodityGroupID is not None:
        cg_exists = (
            db.query(CommodityGroup.id)
            .filter(CommodityGroup.id == body.commodityGroupID)
            .first()
        )
        if not cg_exists:
            raise HTTPException(status_code=404, detail="Commodity group not found")

    # Compute deltas
    previous_status = procurement_request.status
    previous_cg_id = procurement_request.commodityGroupID

    did_change = False

    if body.status is not None and body.status != procurement_request.status:
        procurement_request.status = body.status
        did_change = True

    if (
        body.commodityGroupID is not None
        and body.commodityGroupID != procurement_request.commodityGroupID
    ):
        procurement_request.commodityGroupID = body.commodityGroupID
        did_change = True

    # Nothing changed => return current projection (no audit row)
    if not did_change:
        return to_lite_out(procurement_request)

    # Append audit row with the fields that actually changed
    audit_row = ProcurementRequestUpdate(
        id=str(uuid4()),
        requestID=procurement_request.id,
        updatedByUserID=user.id,
        oldStatus=previous_status if body.status is not None else None,
        newStatus=procurement_request.status if body.status is not None else None,
        oldCommodityGroupID=previous_cg_id if body.commodityGroupID is not None else None,
        newCommodityGroupID=procurement_request.commodityGroupID
        if body.commodityGroupID is not None
        else None,
    )
    db.add(audit_row)

    # Bump version & persist
    procurement_request.version = (procurement_request.version or 1) + 1
    db.add(procurement_request)
    db.commit()
    db.refresh(procurement_request)

    return to_lite_out(procurement_request)


def get_request_details(
    db: Session,
    request_id: str,
    user: User,
) -> ProcurementRequestOut:
    """
    Return full details (including order lines & audit trail) for a single request.
    """
    procurement_request = _load_request_with_details(db, request_id)
    if not procurement_request:
        raise HTTPException(status_code=404, detail="Request not found")

    audit_entries = _load_audit_trail(db, request_id)
    return to_detail_out(procurement_request, audit_entries)