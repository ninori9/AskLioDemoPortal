from __future__ import annotations
import logging
from typing import List
from .contracts import PdfExtractorIn, PdfExtractorOut, ExtractedOrderLine
from .text_extraction import extract_text_from_pdf
from .prompt_templates import build_extraction_messages, build_extraction_messages_from_pdf, build_recovery_messages_from_pdf
from .internal_types import LLMExtractedProcurementData, LLMExtractedOrderLine
from app.agents.pdf_extractor.interface import AbstractPDFExtractor
from app.ai.base import AIClient
from app.agents.base import AgentError

_MIN_USEFUL_CHARS = 200

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

        # Step 1 — local text extraction
        result = extract_text_from_pdf(input_data.data)

        if result.success and (result.text or ""):
            logger.info("Text successfully extracted using %s", result.method)
            text_len = len(result.text)
            logger.debug("Extracted text length: %d", text_len)

            if text_len >= _MIN_USEFUL_CHARS:
                try:
                    messages = build_extraction_messages(result.text)
                    parsed, _meta = self._ai.complete_pydantic(
                        messages=messages,
                        response_model=LLMExtractedProcurementData,
                        model="gpt-4.1-2025-04-14"
                    )
                    llm_result: LLMExtractedProcurementData = parsed
                    if llm_result.isProcurementRequest is not True:
                        raise AgentError("PDF is not a valid procurement request")

                    if self._validate_numeric_consistency(llm_result) and self._has_required_fields(llm_result):
                        return self._return_out(llm_result, input_data.trace_id)

                    logger.warning(
                        "Text-layer parse incomplete/inconsistent → will try PDF (input_file) fallback. (%s)",
                        input_data.filename,
                    )
                except Exception as e:
                    logger.info("LLM on text-layer failed: %s", e)
                    # fall through to PDF fallback

            else:
                logger.warning("Text extracted but short (%d chars) → consider OCR later.", text_len)

        logger.warning("Local text extraction did not return results for %s.", input_data.filename)
        # Step 2 — LLM fallback on raw PDF (input_file)
        try:
            pdf_messages = build_extraction_messages_from_pdf(input_data)
            parsed_pdf, _meta_pdf = self._ai.complete_pydantic(
                messages=pdf_messages,
                response_model=LLMExtractedProcurementData,
                model="gpt-4.1-2025-04-14"
            )
            llm_pdf: LLMExtractedProcurementData = parsed_pdf
            logger.info("PDF extraction done.")
            if llm_pdf.isProcurementRequest is not True:
                raise AgentError("PDF is not a valid procurement request")

            if self._validate_numeric_consistency(llm_pdf) and self._has_required_fields(llm_pdf):
                return self._return_out(llm_pdf, input_data.trace_id)
            else:
                missing_fields = self._missing_fields_for_recovery(llm_pdf)
                logger.info(f"Missing fields {missing_fields}")
                if not missing_fields:
                    return self._return_out(llm_pdf, input_data.trace_id)
                fill_gaps = build_recovery_messages_from_pdf(
                    input_data=input_data,
                    missing_fields=missing_fields,
                    current_data=llm_pdf,
                )
                if not fill_gaps:
                    return self._return_out(llm_pdf, input_data.trace_id)
                recovered, _meta_pdf =  self._ai.complete_pydantic(
                    messages=fill_gaps,
                    response_model=LLMExtractedProcurementData,
                )
                merged = self._merge_missing_fields(base=llm_pdf, patch=recovered)
                return self._return_out(merged, input_data.trace_id)
        except Exception as e:
            logger.info("LLM on raw PDF failed: %s", e)
    
    
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
        
    def _merge_missing_fields(
        self,
        *,
        base: LLMExtractedProcurementData,
        patch: LLMExtractedProcurementData,
    ) -> LLMExtractedProcurementData:
        base.vendorName = base.vendorName or patch.vendorName
        base.vatNumber = base.vatNumber or patch.vatNumber
        if not base.orderLines or len(base.orderLines) == 0:
            base.orderLines = patch.orderLines or []
        return base
        
        
    def _has_required_fields(self, llm_result: LLMExtractedProcurementData) -> bool:
        """Define your ‘must-have’ core fields for acceptance."""
        return bool(
            llm_result
            and (llm_result.vendorName or "").strip()
            and (llm_result.vatNumber or "").strip()
            and llm_result.orderLines
            and len(llm_result.orderLines) > 0
        )
        
        
    def _return_out(self, llm_result: LLMExtractedProcurementData, trace_id: str) -> PdfExtractorOut:
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
            trace_id=trace_id,
        )
        
    def _missing_fields_for_recovery(self, r: LLMExtractedProcurementData) -> List[str]:
        missing: List[str] = []
        if not (r.vendorName or "").strip():
            missing.append("vendorName")
        if not (r.vatNumber or "").strip():
            missing.append("vatNumber")
        if not r.orderLines or len(r.orderLines) == 0:
            missing.append("orderLines")
        return missing