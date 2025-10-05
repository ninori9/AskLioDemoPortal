from sqlalchemy.orm import DeclarativeBase
class Base(DeclarativeBase):
    pass

from app.models.user import User
from app.models.role import Role
from app.models.department import Department
from app.models.procurement_request import ProcurementRequest
from app.models.commodity_group import CommodityGroup 
from app.models.order_line import OrderLine 