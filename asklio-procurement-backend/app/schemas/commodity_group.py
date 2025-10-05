from pydantic import BaseModel

class CommodityGroupOut(BaseModel):
    id: int
    category: str
    name: str
    class Config: from_attributes = True