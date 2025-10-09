from dataclasses import dataclass
from functools import lru_cache
from app.ai.client import get_ai_client
from app.agents.pdf_extractor.pdf_extractor import PDFTextExtractor
from app.agents.commodity_classifier.commodity_classifier import LLMCommodityClassifier
from app.agents.pdf_extractor.pdf_extractor import AbstractPDFExtractor
from app.agents.commodity_classifier.interface import AbstractCommodityClassifier

@dataclass
class AgentRegistry:
    commodity_classifier: AbstractCommodityClassifier
    pdf_extractor: AbstractPDFExtractor

@lru_cache(maxsize=1)
def get_agent_registry() -> AgentRegistry:
    return AgentRegistry(
        commodity_classifier=LLMCommodityClassifier(ai_client=get_ai_client()),
        pdf_extractor=PDFTextExtractor(ai_client=get_ai_client())
    )