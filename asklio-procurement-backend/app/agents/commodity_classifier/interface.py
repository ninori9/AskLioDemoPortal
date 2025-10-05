from ..base import Agent
from .contracts import CommodityClassifyIn, CommodityClassifyOut

class AbstractCommodityClassifier(Agent[CommodityClassifyIn, CommodityClassifyOut]):
    """Bind this agent to the commodity-classification contract."""
    name = "commodity_classifier"