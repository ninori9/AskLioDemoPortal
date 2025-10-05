from .interface import AbstractCommodityClassifier
from .contracts import CommodityClassifyIn, CommodityClassifyOut, AlternativeCG

class MockCommodityClassifier(AbstractCommodityClassifier):
    version = "1.0-mock"

    def run(self, payload: CommodityClassifyIn) -> CommodityClassifyOut:
        text = " ".join([payload.title, payload.vendor_name] + payload.order_lines_text).lower()
        if any(k in text for k in ["adobe", "license", "software"]):
            return CommodityClassifyOut(
                suggested_commodity_group_id=31,  # IT — Software
                confidence=0.86,
                alternatives=[AlternativeCG(id=30, label="IT Services", confidence=0.33)],
                rationale="Keyword heuristic matched {adobe|license|software}.",
                trace_id=payload.trace_id or self.new_trace_id(),
            )
        return CommodityClassifyOut(
            suggested_commodity_group_id=None,
            confidence=0.0,
            alternatives=[],
            rationale="No heuristic match.",
            trace_id=payload.trace_id or self.new_trace_id(),
        )