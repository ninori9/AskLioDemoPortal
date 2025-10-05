from sqlalchemy import Column, String, Integer, Enum, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.models.enums import RequestStatus

class ProcurementRequestUpdate(Base):
    __tablename__ = "procurement_request_update"

    id = Column(String, primary_key=True)  # uuid
    requestID = Column(String, ForeignKey("procurement_request.id"), index=True, nullable=False)
    updatedByUserID = Column(Integer, ForeignKey("user.id"), nullable=False)

    # what changed (nullable fields = unchanged)
    oldStatus = Column(Enum(RequestStatus), nullable=True)
    newStatus = Column(Enum(RequestStatus), nullable=True)

    oldCommodityGroupID = Column(Integer, ForeignKey("commodity_group.id"), nullable=True)
    newCommodityGroupID = Column(Integer, ForeignKey("commodity_group.id"), nullable=True)

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # relations (handy for joins / DTOs)
    request = relationship("ProcurementRequest")
    updated_by = relationship("User", foreign_keys=[updatedByUserID])
    old_commodity_group = relationship("CommodityGroup", foreign_keys=[oldCommodityGroupID], lazy="joined")
    new_commodity_group = relationship("CommodityGroup", foreign_keys=[newCommodityGroupID], lazy="joined")