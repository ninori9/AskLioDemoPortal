from ..base import Agent
from .contracts import PdfExtractorIn, PdfExtractorOut

class AbstractPDFExtractor(Agent[PdfExtractorIn, PdfExtractorOut]):
    """Bind this agent to the PDF-extraction contract."""
    name = "pdf_extractor_agent"