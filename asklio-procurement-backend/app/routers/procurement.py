from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_user, require_api_key
from app.models.user import User
from app.models.enums import RequestStatus

from app.schemas.procurement import (
    ProcurementRequestLiteOut, ProcurementRequestOut,
    ProcurementRequestCreate, ProcurementRequestUpdateIn
)
from app.services import procurement_service as svc

router = APIRouter(
    prefix="/procurement", 
    tags=["requests"], 
    dependencies=[Depends(get_current_user), Depends(require_api_key)]
)

@router.get("", response_model=List[ProcurementRequestLiteOut])
def list_requests(status: Optional[RequestStatus] = Query(default=None), db: Session = Depends(get_db)):
    return svc.list_requests(db, status)

@router.get("/mine", response_model=List[ProcurementRequestLiteOut])
def list_my_requests(
    status: Optional[RequestStatus] = Query(default=None),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return svc.list_my_requests(db, current_user, status, limit)

@router.post("", response_model=ProcurementRequestLiteOut, status_code=status.HTTP_201_CREATED)
def create_procurement_request(
    body: ProcurementRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return svc.create_request(db, body, current_user)

@router.patch("/{request_id}", response_model=ProcurementRequestLiteOut)
def update_procurement_request(
    request_id: str,
    body: ProcurementRequestUpdateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return svc.update_request(db, request_id, body, current_user)

@router.get("/{request_id}", response_model=ProcurementRequestOut)
def get_request_details(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return svc.get_request_details(db, request_id, current_user)