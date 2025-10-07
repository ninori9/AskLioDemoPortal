from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_user, require_api_key
from app.models.user import User
from app.models.enums import RequestStatus

from app.schemas.procurement import (
    ProcurementRequestLiteOut, ProcurementRequestOut,
    ProcurementRequestCreate, ProcurementRequestUpdateIn,
    RequestDraftOut
)
from app.services import procurement_service as svc


MAX_PDF_SIZE_MB = 5
MAX_PDF_BYTES = MAX_PDF_SIZE_MB * 1024 * 1024

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


@router.post("/from-pdf", response_model=RequestDraftOut, status_code=status.HTTP_200_OK)
async def extract_request_draft_from_pdf(
    file: UploadFile = File(...),
) -> RequestDraftOut:
    # Basic file guard
    ct = (file.content_type or "").lower()
    if not ct.startswith("application/pdf"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported content type: {file.content_type}. Expected application/pdf.",
        )

    try:
        data = await file.read()
        if not data:
            raise HTTPException(status_code=400, detail="Empty file uploaded.")
        if len(data) > MAX_PDF_BYTES:
            raise HTTPException(
                status_code=413,  # Payload Too Large
                detail=f"PDF exceeds maximum allowed size of {MAX_PDF_SIZE_MB} MB.",
            )
    except Exception as e:
        raise HTTPException(status_code=400, detail="Could not read uploaded file.")
    
    result = svc.create_request_draft_from_pdf(
        data,
        filename=file.filename or "upload.pdf",
        content_type=ct or "application/pdf",
    )
    return result