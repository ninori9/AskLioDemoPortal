from sqlalchemy import Column, String, Integer, Enum, ForeignKey, DateTime, func, Float
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.models.enums import RequestStatus

class ProcurementRequest(Base):
    __tablename__ = "procurement_request"
    id = Column(String, primary_key=True)
    title = Column(String(200), nullable=False)
    vendorName = Column(String(200), nullable=False)
    vatID = Column(String(32), nullable=False)
    commodityGroupID = Column(Integer, ForeignKey("commodity_group.id"))
    commodityGroupConfidence = Column(Float, nullable=True)
    totalCosts = Column(Integer, nullable=False)  # cents
    status = Column(Enum(RequestStatus), nullable=False, default=RequestStatus.OPEN)
    
    createdByUserID = Column(Integer, ForeignKey("user.id"), nullable=False)
    created_by = relationship("User", foreign_keys=[createdByUserID])
    
    shippingCents = Column(Integer, nullable=True)
    taxCents = Column(Integer, nullable=True)
    discountCents = Column(Integer, nullable=True)

    commodity_group = relationship("CommodityGroup")
    order_lines = relationship("OrderLine", back_populates="request", cascade="all, delete-orphan")
    
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    version = Column(Integer, nullable=False, server_default="1")