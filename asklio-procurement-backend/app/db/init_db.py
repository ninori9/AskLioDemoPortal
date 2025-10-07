
from __future__ import annotations
import json
import logging
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from app.core.security import get_password_hash
from app.models.user import User
from app.models.department import Department
from app.models.role import Role
from app.models.user_role import UserRole
from app.models.commodity_group import CommodityGroup
from app.models.procurement_request import ProcurementRequest
from app.models.order_line import OrderLine
from app.models.procurement_request_update import ProcurementRequestUpdate
from app.models.enums import RequestStatus
from app.weaviate.text_formatter import build_request_embedding_text
from app.ai.client import get_ai_client
import app.weaviate.operations as wx

logger = logging.getLogger(__name__)

def _get_or_create_role(db: Session, name: str) -> Role:
    role = db.query(Role).filter(Role.name == name).first()
    if role:
        return role
    role = Role(name=name)
    db.add(role)
    db.flush()
    logger.info("Created role: %s", name)
    return role

def _get_or_create_department(db: Session, name: str) -> Department:
    dep = db.query(Department).filter(Department.name == name).first()
    if dep:
        return dep
    dep = Department(name=name)
    db.add(dep)
    db.flush()
    logger.info("Created department: %s", name)
    return dep

def _ensure_user_roles(db: Session, user: User, role_names: list[str]) -> None:
    existing = {(ur.role.name if ur.role else None) for ur in (user.roles or [])}
    for rname in role_names:
        if rname in existing:
            continue
        role = _get_or_create_role(db, rname)
        db.add(UserRole(user_id=user.id, role_id=role.id))
        logger.info("Added role '%s' to user '%s'", rname, user.username)

def _get_or_create_user(
    db: Session,
    username: str,
    firstname: str,
    lastname: str,
    raw_password: str,
    department_name: str,
    role_names: list[str],
) -> User:
    user = db.query(User).filter(User.username == username).first()
    if user:
        _ensure_user_roles(db, user, role_names)
        logger.info("User exists: %s (ensured roles)", username)
        return user

    dep = _get_or_create_department(db, department_name)
    user = User(
        firstname=firstname,
        lastname=lastname,
        username=username,
        hashedPassword=get_password_hash(raw_password),
        department=dep,
    )
    db.add(user)
    db.flush()
    logger.info("Created user: %s (%s %s)", username, firstname, lastname)
    _ensure_user_roles(db, user, role_names)
    return user

def _seed_commodity_groups(db: Session) -> int:
    """
    Insert 50 predefined commodity groups (id 1..50).
    Returns number inserted on this run (0 if none).
    """
    json_path = Path(__file__).resolve().parent / "data" / "commodity_groups.json"
    with open(json_path, "r", encoding="utf-8") as f:
        items = json.load(f)

    existing_ids = {cid for (cid,) in db.query(CommodityGroup.id).all()}
    to_add = []
    for item in items:
        cid = int(item["id"])
        if cid in existing_ids:
            continue
        to_add.append(CommodityGroup(id=cid, category=item["category"], name=item["name"]))
    if to_add:
        db.add_all(to_add)
        logger.info("Inserted %d commodity groups", len(to_add))
    else:
        logger.info("Commodity groups already present; nothing to insert")
    return len(to_add)


def _safe_cg_id(db: Session, preferred_id: int) -> int:
    """Return preferred commodity group id if it exists, otherwise fall back to the first available."""
    exists = db.query(CommodityGroup.id).filter(CommodityGroup.id == preferred_id).first()
    if exists:
        return preferred_id
    first = db.query(CommodityGroup.id).order_by(CommodityGroup.id.asc()).first()
    return int(first[0]) if first else preferred_id


def _seed_requests(db: Session) -> int:
    """
    Insert a handful of sample procurement requests with order lines and a couple of audit updates.
    Idempotent: does nothing if any requests already exist.
    """
    already = db.query(ProcurementRequest.id).limit(1).first()
    if already:
        logger.info("Procurement requests already present; skipping sample data.")
        return 0

    # Resolve users (createdByUserID)
    peter = db.query(User).filter(User.username == "peter.procurement").first()
    randy = db.query(User).filter(User.username == "randy.requestor").first()
    jane  = db.query(User).filter(User.username == "jane.smith").first()
    maxm  = db.query(User).filter(User.username == "max.mueller").first()

    # Guard: if users are missing for some reason, stop seeding requests
    if not all([peter, randy, jane, maxm]):
        logger.warning("Users missing; cannot seed procurement requests.")
        return 0

    now = datetime.now(timezone.utc)

    # Choose CG ids (fall back if the canonical ones are missing)
    cg_software    = _safe_cg_id(db, 31)  # Information Technology → Software
    cg_hardware    = _safe_cg_id(db, 29)  # Information Technology → Hardware
    cg_marketing   = _safe_cg_id(db, 36)  # Marketing & Advertising → Advertising
    cg_consulting  = _safe_cg_id(db, 4)   # General Services → Consulting
    cg_facilities  = _safe_cg_id(db, 14)  # Facility Management → Renovations

    def make_request(
        title: str,
        vendor: str,
        vat: str,
        cg_id: int,
        creator: User,
        status: RequestStatus,
        lines: list[dict],
        created_at: datetime,
        shipping_cents: int = 0,
        tax_cents: int = 0,
        discount_cents: int = 0,
    ) -> ProcurementRequest:
        req_id = str(uuid4())
        line_rows: list[OrderLine] = []
        total = 0
        for l in lines:
            unit_cents = int(l["unitPriceCents"])
            qty = int(l["quantity"])
            line_total = unit_cents * qty
            total += line_total
            line_rows.append(
                OrderLine(
                    id=str(uuid4()),
                    description=l["description"],
                    unitPriceCents=unit_cents,
                    quantity=qty,
                    unit=l.get("unit", "pcs"),
                    totalPriceCents=line_total,
                    requestID=req_id,  # set FK upfront to be explicit
                )
            )
        grand_total = total + int(shipping_cents) + int(tax_cents) - int(discount_cents)
        return ProcurementRequest(
            id=req_id,
            title=title,
            vendorName=vendor,
            vatID=vat,
            commodityGroupID=cg_id,
            totalCosts=grand_total,
            shippingCents=shipping_cents or 0,
            taxCents=tax_cents or 0,
            discountCents=discount_cents or 0,
            status=status,
            createdByUserID=creator.id,
            order_lines=line_rows,
            created_at=created_at,
            version=1,
        )

    requests: list[ProcurementRequest] = [
        # No shipping/tax/discount
        make_request(
            title="Adobe Creative Cloud Licenses 10 seats",
            vendor="Adobe Systems",
            vat="DE123456789",
            cg_id=cg_software,
            creator=jane,
            status=RequestStatus.OPEN,
            created_at=now,
            lines=[
                {"description": "Adobe All Apps license", "unitPriceCents": 4999, "quantity": 10, "unit": "licenses"},
            ],
            shipping_cents=0,
            tax_cents=0,
            discount_cents=0,
        ),

        # Shipping + tax (e.g., 29.90 shipping, VAT 19% over lines+shipping simplified as fixed number here)
        make_request(
            title="MacBook Pro 14 inch (2 units)",
            vendor="Apple",
            vat="DE111222333",
            cg_id=cg_hardware,
            creator=randy,
            status=RequestStatus.OPEN,
            created_at=now,
            lines=[
                {"description": "MacBook Pro 14'' M3, 16GB/512GB", "unitPriceCents": 199900, "quantity": 2, "unit": "units"},
                {"description": "USB-C Docking Station", "unitPriceCents": 12999, "quantity": 2, "unit": "units"},
            ],
            shipping_cents=2990,  # 29.90
            tax_cents=80278,      # example VAT figure in cents
            discount_cents=0,
        ),

        # Discount only
        make_request(
            title="Website Launch Advertising Package",
            vendor="AdCo GmbH",
            vat="DE987654321",
            cg_id=cg_marketing,
            creator=maxm,
            status=RequestStatus.IN_PROGRESS,
            created_at=now,
            lines=[
                {"description": "Banner campaign (2 weeks)", "unitPriceCents": 350000, "quantity": 1, "unit": "package"},
                {"description": "Sponsored posts (5)", "unitPriceCents": 45000, "quantity": 5, "unit": "posts"},
            ],
            shipping_cents=0,
            tax_cents=0,
            discount_cents=25000,  # 250.00 discount
        ),

        # Tax only
        make_request(
            title="Process Optimization Consulting",
            vendor="Lean Experts AG",
            vat="DE222333444",
            cg_id=cg_consulting,
            creator=peter,
            status=RequestStatus.OPEN,
            created_at=now,
            lines=[
                {"description": "Consulting day rate", "unitPriceCents": 120000, "quantity": 5, "unit": "days"},
            ],
            shipping_cents=0,
            tax_cents=114000,  # sample tax figure
            discount_cents=0,
        ),

        # Shipping + discount
        make_request(
            title="Office Renovation Phase 1",
            vendor="BuildWell GmbH",
            vat="DE333444555",
            cg_id=cg_facilities,
            creator=peter,
            status=RequestStatus.CLOSED,
            created_at=now,
            lines=[
                {"description": "Painting (floor 3)", "unitPriceCents": 250000, "quantity": 1, "unit": "job"},
                {"description": "Carpet replacement", "unitPriceCents": 180000, "quantity": 1, "unit": "job"},
            ],
            shipping_cents=15000,
            tax_cents=0,
            discount_cents=20000,
        ),
    ]

    db.add_all(requests)
    db.flush()  # ensure IDs persisted for audit rows
    

    # Add requests to Weaviate vector DB and add two illustrative audit update
    if requests:
        _index_seed_requests_in_weaviate(requests)
        
        # Marketing request status moved to InProgress by Peter
        r1 = requests[0]
        db.add(
            ProcurementRequestUpdate(
                id=str(uuid4()),
                requestID=r1.id,
                updatedByUserID=peter.id,
                oldStatus=RequestStatus.OPEN,
                newStatus=RequestStatus.IN_PROGRESS,
                oldCommodityGroupID=None,
                newCommodityGroupID=None,
                updated_at=now,
            )
        )
        r1.status = RequestStatus.IN_PROGRESS
        r1.version = (r1.version or 1) + 1

    logger.info("Inserted %d procurement requests (with lines + audit updates).", len(requests))
    return len(requests)


def _index_seed_requests_in_weaviate(requests: list[ProcurementRequest]) -> int:
    """
    Try to embed and insert each seeded request into Weaviate.
    Skips quietly if embeddings aren't available (e.g., no OPENAI_API_KEY).
    Returns #successfully indexed.
    """
    try:
        ai_client = get_ai_client()
    except Exception as e:
        logger.warning("AI client unavailable; skipping Weaviate indexing for seeds: %s", e)
        return 0

    inserted = 0
    for r in requests:
        # Build the same text your agent will build for queries
        lines = [
            f"{ol.quantity} x {ol.description} @ {ol.unitPriceCents/100:.2f} per {ol.unit}"
            for ol in (r.order_lines or [])
        ]
        text = build_request_embedding_text(
            title=r.title,
            vendor_name=r.vendorName,
            vat_id=r.vatID,
            order_lines_text=lines,
        )

        try:
            vec = ai_client.embed(text)
        except Exception as e:
            logger.warning("Embed failed for request %s; skipping: %s", r.id, e)
            continue

        try:
            wx.add(
                request_id=r.id,
                commodity_group=str(r.commodityGroupID) if r.commodityGroupID is not None else "",
                embedded_request_context=text,
                vector=vec,
            )
            inserted += 1
        except Exception as e:
            logger.warning("Weaviate insert failed for request %s: %s", r.id, e)

    if inserted:
        logger.info("Indexed %d seeded requests into Weaviate.", inserted)
    else:
        logger.info("No seeded requests were indexed into Weaviate.")
    return inserted


def init_db(db: Session) -> None:
    """
    Idempotent. Safe to call on every startup.
    """
    inserted = False

    # Roles
    for r in ("Manager", "Requestor"):
        if not db.query(Role).filter(Role.name == r).first():
            db.add(Role(name=r))
            inserted = True
            logger.info("Seeded role: %s", r)

    # Users (+ departments)
    users_spec = [
        ("peter.procurement", "Peter", "Procurement", "Procurement", ["Manager"]),
        ("randy.requestor",   "Randy", "Requestor",   "HR",          ["Requestor"]),
        ("jane.smith",        "Jane",  "Smith",       "Creative Marketing", ["Requestor"]),
        ("max.mueller",       "Max",   "Müller",      "Accounting",  ["Manager", "Requestor"]),
    ]
    for uname, first, last, dept, roles in users_spec:
        before = db.query(User).filter(User.username == uname).first() is None
        _get_or_create_user(
            db=db,
            username=uname,
            firstname=first,
            lastname=last,
            raw_password="test123",
            department_name=dept,
            role_names=roles,
        )
        if before:
            inserted = True

    # Commodity groups
    added = _seed_commodity_groups(db)
    if added > 0:
        inserted = True
        
    added_requests = _seed_requests(db)
    if added_requests > 0:
        inserted = True

    if inserted:
        db.commit()
        logger.info("Initial seed committed (roles/users/commodity groups/requests).")

    else:
        logger.info("Seed skipped (already up-to-date).")