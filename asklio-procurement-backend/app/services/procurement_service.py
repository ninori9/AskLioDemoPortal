from __future__ import annotations

import logging
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
    RequestDraftOut,
    OrderLineDraftOut
)
from app.services.mappers import to_lite_out, to_detail_out
from app.services.auth import ensure_manager
from app.agents.registry import get_agent_registry
from app.ai.client import get_ai_client

# Agent contracts
from app.agents.commodity_classifier.contracts import CommodityClassifyIn, CommodityGroupRef
from app.agents.pdf_extractor.contracts import PdfExtractorOut, PdfExtractorIn

import app.weaviate.operations as wx
from app.weaviate.text_formatter import build_request_embedding_text 
from app.agents.base import AgentError

logger = logging.getLogger(__name__)


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
    # Build order lines & compute total in cents
    order_line_rows: list[OrderLine] = []
    total_price_cents: int = 0

    for line in body.orderLines:
        line_total_cents = line.unitPriceCents * line.quantity
        total_price_cents += line_total_cents

        order_line_rows.append(
            OrderLine(
                id=str(uuid4()),
                description=line.description,
                unitPriceCents=int(line.unitPriceCents),
                quantity=line.quantity,
                unit=line.unit,
                totalPriceCents=int(line_total_cents),
            )
        )
    
    # Auto-classify commodity group via agent
    try:
        # Build agent input
        order_lines_text = [
            f"{ol.quantity} x {ol.description} @ {ol.unitPriceCents/100:.2f} per {ol.unit}"
            for ol in body.orderLines
        ]
        # Provide all CGs as candidates
        cg_rows: list[CommodityGroup] = db.query(CommodityGroup).order_by(CommodityGroup.id.asc()).all()
        cg_refs = [
            CommodityGroupRef(id=int(cg.id), label=cg.name, category=cg.category)
            for cg in cg_rows
        ]
        agent_input = CommodityClassifyIn(
            title=body.title,
            vendor_name=body.vendorName,
            vat_id=body.vatID,
            order_lines_text=order_lines_text,
            available_commodity_groups=cg_refs,
            trace_id=str(uuid4()),
        )
        classifier = get_agent_registry().commodity_classifier
        agent_result = classifier.run(agent_input)
        chosen_cg_id = agent_result.suggested_commodity_group_id
        chosen_conf = agent_result.confidence or 0.0
        if chosen_cg_id is None:
            chosen_cg_id = cg_rows[0].id if cg_rows else None
            chosen_conf = 0.0
        if chosen_cg_id is None:
            raise HTTPException(status_code=500, detail="No commodity groups available for classification.")
    except AgentError as e:
        # Safe fall-back path: pick the first group with 0.0 confidence
        logger.exception("Commodity classifier failed; using fallback: %s", e)
        first_cg = db.query(CommodityGroup.id).order_by(CommodityGroup.id.asc()).first()
        if not first_cg:
            raise HTTPException(status_code=500, detail="No commodity groups available.")
        chosen_cg_id = int(first_cg[0])
        chosen_conf = 0.0
        
    shipping = int(body.shippingCents or 0)
    tax = int(body.taxCents or 0)
    discount = int(body.totalDiscountCents or 0)

    total_price_cents = int(total_price_cents + shipping + tax - discount)
    
    # Create request row
    new_request = ProcurementRequest(
        id=str(uuid4()),
        title=body.title,
        vendorName=body.vendorName,
        vatID=body.vatID,
        commodityGroupID=chosen_cg_id,
        commodityGroupConfidence=chosen_conf,
        totalCosts=total_price_cents,
        shippingCents=shipping,
        taxCents=tax,
        discountCents=discount,
        createdByUserID=user.id,
        order_lines=order_line_rows,
    )
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    
    # Index into Weaviate
    try:
        ai_client = get_ai_client()
        text = build_request_embedding_text(
            title=body.title,
            vendor_name=body.vendorName,
            vat_id=body.vatID,
            order_lines_text=[
                f"{ol.quantity} x {ol.description} @ {ol.unitPriceCents/100:.2f} per {ol.unit}"
                for ol in body.orderLines
            ],
        )
        request_embedding = ai_client.embed(text)
        wx.add(
            request_id=new_request.id,
            commodity_group=str(new_request.commodityGroupID),
            embedded_request_context=text,
            vector=request_embedding,
        )
    except Exception as e:
        logger.exception("Weaviate index failed for request %s: %s", new_request.id, e)

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
        procurement_request.commodityGroupConfidence = None
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
    
    # --- Keep Weaviate in sync if CG changed ---
    if (
        body.commodityGroupID is not None
        and body.commodityGroupID != previous_cg_id
    ):
        try:
            updated = wx.update_commodity_group(
                request_id=request_id,
                new_commodity_group=str(body.commodityGroupID),
            )
            logger.info(
                "Weaviate: updated %d objects for request_id=%s to CG=%s",
                updated, request_id, body.commodityGroupID
            )
        except Exception as e:
            # Do not fail the HTTP request if the vector update fails
            logger.exception(
                "Weaviate update_commodity_group failed for request_id=%s -> %s: %s",
                request_id, body.commodityGroupID, e
            )

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


def create_request_draft_from_pdf(
    data: bytes,
    *,
    filename: str = "potential_procurement_request.pdf",
    content_type: str = "application/pdf",
) -> RequestDraftOut:
    """
    Extract a draft procurement request from the uploaded PDF.
    """
    trace_id = str(uuid4())

    try:
        agent = get_agent_registry().pdf_extractor
        agent_input = PdfExtractorIn(
            filename=filename,
            content_type=content_type,
            data=data,
            trace_id=trace_id,
        )
        agent_out = agent.run(agent_input)

    except AgentError as e:
        # The extractor determined it's not a procurement request or failed parsing
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not extract a procurement request: {e}",
        )
    except Exception as e:
        # Any unexpected issue
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PDF extraction failed unexpectedly.",
        )

    # Map agent -> RequestDraftOut
    draft_lines = [
        OrderLineDraftOut(
            description=ol.description,
            unitPriceCents=ol.unitPriceCents,
            quantity=ol.quantity,
            unit=ol.unit,
            totalPriceCents=ol.totalPriceCents,
        )
        for ol in (agent_out.orderLines or [])
    ]

    return RequestDraftOut(
        title=agent_out.title,
        vendorName=agent_out.vendorName,
        vatNumber=agent_out.vatNumber,
        orderLines=draft_lines,
        totalPriceCents=agent_out.totalPriceCents,
        shippingCents=agent_out.shippingCents,
        taxCents=agent_out.taxCents,
        totalDiscountCents=agent_out.totalDiscountCents,
    )