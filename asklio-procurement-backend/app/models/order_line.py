from sqlalchemy import Column, String, Integer, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.db.base import Base

class OrderLine(Base):
    __tablename__ = "order_line"
    id = Column(String, primary_key=True)  # uuid string
    description = Column(String(300), nullable=False)
    requestID = Column(String, ForeignKey("procurement_request.id"))
    unitPriceCents = Column(Integer, nullable=False)
    unit = Column(String(50), nullable=False)
    quantity = Column(Float, nullable=False, default=1)
    totalPriceCents = Column(Integer, nullable=False)
    request = relationship("ProcurementRequest", back_populates="order_lines")
