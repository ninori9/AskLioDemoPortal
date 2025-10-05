from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import get_current_user, require_api_key
from app.models.commodity_group import CommodityGroup
from app.schemas.commodity_group import CommodityGroupOut

router = APIRouter(
    prefix="/commodity-groups", 
    tags=["requests"], 
    dependencies=[Depends(get_current_user), Depends(require_api_key)]
)


@router.get("/all", response_model=list[CommodityGroupOut])
def list_commodity_groups(db: Session = Depends(get_db)):
    """
    Return all available commodity groups.
    """
    rows = db.query(CommodityGroup).order_by(CommodityGroup.category, CommodityGroup.name).all()
    return [CommodityGroupOut.model_validate(r) for r in rows]