from __future__ import annotations
import logging
from typing import List
from .contracts import PdfExtractorIn, PdfExtractorOut, ExtractedOrderLine
from .text_extraction import extract_text_from_pdf
from .prompt_templates import build_extraction_messages, build_extraction_messages_from_pdf
from .internal_types import LLMExtractedProcurementData, LLMExtractedOrderLine
from app.agents.pdf_extractor.interface import AbstractPDFExtractor
from app.ai.base import AIClient
from app.agents.base import AgentError

logger = logging.getLogger(__name__)

class PDFTextExtractor(AbstractPDFExtractor):
    """
    Minimal, deterministic flow:
      1) Extract text using PDF text extractor libraries
      2) Fallback to LLM based PDF text extraction
      3) Parse result to expected output
    """
    name = "pdf_text_extractor"
    version = "1.0"
    
    def __init__(
        self,
        ai_client: AIClient,
        *,
        temperature: float = 0.1,
        max_output_tokens: int = 2000,
    ):
        self._ai = ai_client
        self._temperature = temperature
        self._max_tokens = max_output_tokens
    
    def run(self, input_data: PdfExtractorIn) -> PdfExtractorOut:
        logger.info("Starting PDF extraction: %s", input_data.filename)

        # Step 1 — local extraction
        result = extract_text_from_pdf(input_data.data)
        if result.success and result.text:
            logger.info("Text successfully extracted using %s", result.method)
            logger.info("Extracted text %s", result.text)
            
            messages = build_extraction_messages(result.text)
            
            # Structured LLM call
            try:
                parsed, _meta = self._ai.complete_pydantic(
                    messages=messages,
                    response_model=LLMExtractedProcurementData,
                    temperature=self._temperature,
                    max_output_tokens=self._max_tokens,
                )
                llm_result: LLMExtractedProcurementData = parsed
            except Exception as e:
                raise AgentError(f"AI model error during extraction of PDF content: {e}")
            
            # Validate whether the document is a valid request
            if llm_result.isProcurementRequest != True:
                raise AgentError(f"PDF is not a valid procurement request: {e}")
            
            # Validate whether the data has numeric consistency
            consistent = self._validate_numeric_consistency(llm_result)
            if consistent:
                order_lines = self._parse_llm_order_lines(llm_result.orderLines)
            
                return PdfExtractorOut(
                    title=llm_result.title,
                    vendorName=llm_result.vendorName,
                    vatNumber=llm_result.vatNumber,
                    totalPriceCents=llm_result.totalPriceCents,
                    totalDiscountCents=llm_result.totalDiscountCents,
                    shippingCents=llm_result.shippingCents,
                    taxCents=llm_result.taxCents,
                    orderLines=order_lines,
                    trace_id=input_data.trace_id,
                )
            
            logger.warning(
                    "Inconsistent totals detected for %s — falling back to full LLM PDF parsing",
                    input_data.filename
                )

        logger.warning(
            "Local text extraction failed or returned insufficient text for %s; will use LLM fallback",
            input_data.filename,
        )

        # Step 2 — LLM fallback (scanned / OCR-heavy PDFs / wrong totals)
        messages = build_extraction_messages_from_pdf(input_data)
        try:
            parsed, _meta = self._ai.complete_pydantic(
                messages=messages,
                response_model=LLMExtractedProcurementData,
                temperature=self._temperature,
                max_output_tokens=self._max_tokens,
            )
            
            llm_result: LLMExtractedProcurementData = parsed
        except Exception as e:
            raise AgentError(f"AI model error during extraction of PDF file: {e}")
        
        if llm_result.isProcurementRequest != True:
            raise AgentError("PDF is not a valid procurement request")
        
        order_lines = self._parse_llm_order_lines(llm_result.orderLines)
        
        return PdfExtractorOut(
            title=llm_result.title,
            vendorName=llm_result.vendorName,
            vatNumber=llm_result.vatNumber,
            orderLines=order_lines,
            totalPriceCents=llm_result.totalPriceCents,
            totalDiscountCents=llm_result.totalDiscountCents,
            shippingCents=llm_result.shippingCents,
            taxCents=llm_result.taxCents,
            trace_id=input_data.trace_id,
        )
    
    def _parse_llm_order_lines(self, input_order_lines: List[LLMExtractedOrderLine]) -> List[ExtractedOrderLine]:
        order_lines = []
        for i, ol in enumerate(input_order_lines or []):
            order_lines.append(
                ExtractedOrderLine(
                    description=ol.description or "",
                    unit=ol.unit or "",
                    unitPriceCents=int(ol.unitPriceCents or 0),
                    quantity=ol.quantity,
                    totalPriceCents=int(ol.totalPriceCents or 0),
                )
            )
        return order_lines
    
    def _validate_numeric_consistency(self, llm_result: LLMExtractedProcurementData) -> bool:
        """Check whether extracted totals are consistent within a small tolerance."""
        try:
            lines_total = sum(
                int(l.totalPriceCents or 0) for l in (llm_result.orderLines or [])
            )
            shipping = int(llm_result.shippingCents or 0)
            tax = int(llm_result.taxCents or 0)
            discount = int(llm_result.totalDiscountCents or 0)
            total = int(llm_result.totalPriceCents or 0)

            computed = lines_total + shipping + tax - discount
            diff = abs(computed - total)

            if diff > 2:  # > 2 cents mismatch
                logger.warning(
                    "LLM extraction mismatch: computed=%s, declared=%s (Δ=%s). "
                    "Lines=%s, ship=%s, tax=%s, disc=%s",
                    computed, total, diff, lines_total, shipping, tax, discount
                )
                return False
            return True
        except Exception as e:
            logger.warning("Numeric consistency check failed: %s", e)
            return False