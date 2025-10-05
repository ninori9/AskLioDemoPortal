from sqlalchemy import Column, String, Integer
from app.db.base import Base

class CommodityGroup(Base):
    __tablename__ = "commodity_group"
    id = Column(Integer, primary_key=True)
    category = Column(String(120), nullable=False)
    name = Column(String(120), nullable=False)
