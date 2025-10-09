from __future__ import annotations
from typing import Dict, List, Tuple
import base64
from .internal_types import LLMExtractedProcurementData
import fitz


SYSTEM_PROMPT = (
    "You are a procurement document analyzer for Lio Technologies GmbH. You will analyze either the already extracted text fron a PDF or the PDF itself"
    "The PDF should be a vendor offer or other procurement-related document."

    "───────────────────────────────────────────────\n"
    "1. DETECTION\n"
    "───────────────────────────────────────────────\n"
    "Determine first whether the PDF / PDF text represents a procurement-related document "
    "(such as an offer, quote, invoice, order, or purchase request). "
    "If it is NOT such a document, set isProcurementRequest=false and leave all other fields empty.\n\n"

    "───────────────────────────────────────────────\n"
    "2. CORE FIELDS\n"
    "───────────────────────────────────────────────\n"
    "When it IS a procurement document, extract the following:\n"
    "- title: short descriptive heading or subject "
    "(e.g., 'Offer 1234', 'Invoice #A120', 'Purchase Order', "
    "or in German: 'Angebot', 'Rechnung', 'Bestellung').\n"
    "- vendorName: supplier or company issuing the document "
    "(EN: Supplier, Vendor, Issued by; DE: Lieferant, Anbieter, Firma).\n"
    "- vatNumber: supplier VAT or tax ID "
    "(EN: VAT ID, Tax ID; DE: USt-IdNr., Steuernummer), for example 'DE123456789'."
    "Important: This is not the IBAN or banking number — do not confuse this. "
"Only include a VAT/tax number if it is explicitly visible and clearly labeled as such. "
"If you are not fully certain that the number belongs to the vendor’s tax identification, leave it empty.\n\n"

    "───────────────────────────────────────────────\n"
    "3. ORDER LINE EXTRACTION\n"
    "───────────────────────────────────────────────\n"
    "Extract all listed products, services, or fees that appear as line items in the main body "
    "of the document (tables or itemized sections):\n"
    "- description: human-readable name or details of the item or service.\n"
    "- unit: unit of measure (EN: pcs, item, hour, license; DE: Stk., Std., Stück). Use '-' if not specified.\n"
    "- quantity: numeric quantity. Use 1 if only one item is shown and no quantity is indicated.\n"
    "- unitPriceCents: net unit price in integer cents AFTER any per-line discount.\n"
    "- totalPriceCents: quantity × unitPriceCents (net, after discount) in integer cents. "
    "If a line total is explicitly shown, prefer it.\n\n"
    "Rules:\n"
    "- Prefer the NET (pre-tax) values for line items.\n"
    "- If a per-line discount is shown (e.g., '100.00 - 10% = 90.00'), use the discounted amount.\n"
    "- DO NOT create separate lines for taxes or totals.\n"
    "- If shipping, delivery, or handling is already included as a normal line item, "
    "keep it as a line item and DO NOT fill the summary shippingCents.\n"
    "- If a document-level discount is already reflected as an order line, "
    "do not populate discountCents in the summary.\n"
    "- Alternatives/options — strict exclusion:\n"
    "  Exclude lines that are alternatives/options unless there is explicit evidence of selection. "
    "  Treat any of the following as an alternative marker (case-insensitive):\n"
    "    'Alternativ', 'Alt.', 'Alternative', 'Option', 'Optional', 'Variante', 'wahlweise', "
    "    'Alternative Position', 'Alternative:', '(Alt.)', '[Alt]'.\n"
    "  Also exclude lines under headings/sections labeled 'Alternative', 'Alternativ', 'Option', or similar. "
    "  Include an alternative ONLY if one of these is true:\n"
    "    • The document explicitly states it was selected/accepted (e.g., 'selected', 'gewählt', 'accepted', a checkmark).\n"
    "    • It has a nonzero quantity AND the totals reconciliation (see §7) requires this line to match the final total.\n"
    "  When uncertain, EXCLUDE the alternative.\n\n"

    "───────────────────────────────────────────────\n"
    "4. SUMMARY TOTALS\n"
    "───────────────────────────────────────────────\n"
    "Extract document-level totals if present:\n"
    "- totalPriceCents: final gross/payable total (EN: Total, Grand Total, Amount Due; DE: Endsumme, Gesamtsumme, Gesamtbetrag). "
    "Prefer the *final* total figure appearing at the end.\n"
    "- shippingCents: total shipping, delivery, freight, or handling charges "
    "(EN: Shipping, Delivery, Freight; DE: Versandkosten, Lieferung, Transport, Verpackung, Fracht) "
    "only if such costs are NOT already represented as line items.\n"
    "- taxCents: total VAT or sales tax (EN: VAT, Sales Tax; DE: MwSt., USt., Umsatzsteuer, Steuer).\n"
    "- discountCents: total document-level discount (EN: Discount, Rebate, Price Reduction; "
    "DE: Rabatt, Nachlass, Skonto) only if it is NOT already part of the line items.\n\n"

    "───────────────────────────────────────────────\n"
    "5. DOUBLE-COUNTING RULES (PRIORITY = LINE ITEMS)\n"
    "───────────────────────────────────────────────\n"
    "If shipping, delivery, freight, or handling appears as an order line, "
    "DO NOT also use this value for shippingCents — if no separate shipping price is given, leave it null.\n"
    "If a discount or rebate appears as a line item or per-line reduction, "
    "DO NOT also populate discountCents.\n"
    "Only use the summary fields when such charges exist solely in the summary section.\n\n"

    "───────────────────────────────────────────────\n"
    "6. NORMALIZATION RULES\n"
    "───────────────────────────────────────────────\n"
    "- Parse numbers using either comma or dot decimals and convert to integer cents "
    "(e.g., '1.234,56' or '1,234.56' → 123456).\n"
    "- Remove currency symbols and thousand separators.\n"
    "- Assume a single consistent currency across the document.\n"
    "- Ignore page or section subtotals (EN: Page Total; DE: Seitensumme); use only the final total.\n"
    "- If a field cannot be confidently extracted, leave it null — never invent or guess values.\n\n"

    "───────────────────────────────────────────────\n"
    "7. RECONCILIATION & VALIDATION\n"
    "───────────────────────────────────────────────\n"
    "After extraction, verify that all amounts are consistent:\n"
    "- computedTotal = sum(orderLines[].totalPriceCents) + (shippingCents or 0) + (taxCents or 0) - (discountCents or 0)\n"
    "- Compare computedTotal to totalPriceCents.\n"
    "- If the difference exceeds ±2 cents, re-examine potential double-counting or missed amounts.\n"
    "- Correction order when reconciling:\n"
    "  1) Remove/ignore any lines flagged as alternatives/options (per §3) first.\n"
    "  2) Prefer leaving optional summary fields (shippingCents, discountCents) empty rather than duplicating line items.\n"
    "  3) Only include an alternative line if its inclusion is explicitly evidenced OR necessary to match the final total.\n\n"
    
    "───────────────────────────────────────────────\n"
    "8. EXAMPLES \n"
    "───────────────────────────────────────────────\n"
    "- Per-line discount example:\n"
    "  'Price 100.00 less 10% = 90.00' → unitPriceCents=9000, totalPriceCents=9000.\n"
    "- Shipping included as a line:\n"
    "  'Item: Express delivery service — 25.00 EUR' → add as order line, shippingCents=null.\n"
    "- Shipping only in summary:\n"
    "  'Subtotal 1000.00  |  Shipping 25.00  |  Total 1025.00' → shippingCents=2500, no extra line item.\n\n"
)

def build_extraction_messages(extracted_text: str) -> List[Dict[str, str]]:
    """
    Build the (system, user) messages for the PDF-to-structured procurement request extraction.
    This message pair will be used with a structured-output model call that returns PdfExtractorOut.
    """
    user_content = (
        "Below is text extracted from a PDF document.\n\n"
        "Your task is to determine whether it represents a procurement request, "
        "and if so, extract all relevant procurement fields as described.\n\n"
        "DOCUMENT TEXT:\n"
        "--------------------\n"
        f"{extracted_text[:15000]}" # truncate for safety
    )

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
    
def build_extraction_messages_from_pdf(input_data: bytes) -> List[Dict]:
    """
    Builds OpenAI-style messages for direct PDF-based extraction
    (used when no valid text could be extracted locally).
    The PDF is embedded as a base64 data URI for ephemeral, non-persistent processing.
    """
    b64_data = base64.b64encode(input_data.data).decode("utf-8")

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": [
                {
                    "type": "input_file",
                    "filename": "potential_procurement_request.pdf",
                    "file_data": f"data:application/pdf;base64,{b64_data}",
                },
                {
                    "type": "input_text",
                    "text": (
                        "Please extract all procurement-related information (title, vendor, VAT number, and order lines) "
                        "following the described schema. If this is not a procurement request, set isProcurementRequest = false."
                    ),
                },
            ],
        },
    ]

def build_recovery_messages_from_pdf(
    input_data,
    *,
    missing_fields: List[str],
    current_data: LLMExtractedProcurementData,
) -> List[Dict]:
    """
    Image-based recovery pass for missing fields (vendorName, vatNumber, orderLines).
    - If orderLines are missing, render ALL pages; otherwise render first & last only.
    - Attach images using Responses API content parts: input_image + image_url:{url: dataURI}.
    """
    assert missing_fields, "missing_fields must not be empty."

    need_lines = "orderLines" in missing_fields
    images = (
        pdf_to_base64_images_all_pages(input_data.data, dpi=300)
        if need_lines
        else pdf_to_base64_images(input_data.data, dpi=300)
    )
    if not images:
        return []

    missing_str = ", ".join(missing_fields)

    system_prompt = (
        "You are a procurement document analyzer. You receive page images of a PDF and must fill ONLY the fields "
        "that were missing from a previous text-layer parse.\n\n"
        "The document should be a vendor offer.\n"
        "GUIDELINES:\n"
        "• Use any visible text on the provided images (e.g., low-contrast header/footer, logos, imprints, tables).\n"
        "• Prioritize reading the footer on the last page and the header on the first page if relevant information appears there.\n"
        "• Never guess; leave any value empty if you cannot find it confidently.\n"
        "• 'taxNumber' in this context refers to the vendor's VAT/tax identifier.\n"
        "• Return a complete LLMExtractedProcurementData object but only fill the missing fields; "
        "  keep already-known fields as they are (the caller will merge).\n\n"
        "FIELDS (RECOVERY TARGETS):\n"
        "• vendorName: Legal/brand name of the supplier issuing the document (logo/letterhead, footer/imprint, contact block). Do NOT return buyer name.\n"
        "• vatNumber: Vendor VAT/tax ID (e.g., 'USt-IdNr.', 'USt-ID', 'VAT No.', 'Tax ID', 'Steuernummer'). "
        "  Accept formats like DE + 9 digits or valid EU/local formats. Exclude IBAN/BIC, phone, order ids, HRB.\n\n"
        "ORDER LINE EXTRACTION (only if requested among missing fields):\n"
        "• description — human-readable item/service.\n"
        "• unit — e.g., pcs/item/hour/license (DE: Stk., Std., Stück). Use '-' if not specified.\n"
        "• quantity — numeric; use 1 if only a single item is shown and no quantity is indicated.\n"
        "• unitPriceCents — NET unit price in integer cents after any per-line discount.\n"
        "• totalPriceCents — NET line total in integer cents (prefer explicit line total; else quantity × unit).\n"
        "Rules: prefer NET values; if per-line discount is shown, use discounted amounts; do NOT create lines for taxes/totals; "
        "shipping as a normal line stays a line (don’t duplicate into shippingCents); exclude alternatives/options unless explicitly selected or needed to match the final total.\n"
        "Normalize numbers: remove currency symbols and thousands separators; accept comma/dot decimals.\n"
    )

    user_text = (
        "Current (possibly incomplete) parsed data:\n"
        f"{stringify_procurement_core(current_data)}\n\n"
        f"Missing fields to recover now: {missing_str}\n"
        "Read the attached images and recover ONLY the missing fields. "
        "Do not invent values. If a field cannot be found, leave it empty."
    )

    image_parts = [
        {"type": "input_image", "image_url": data_uri, "detail": "high"}  # detail is optional
        for (_filename, data_uri) in images
    ]

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": [{"type": "input_text", "text": user_text}, *image_parts]},
    ]


def stringify_procurement_core(p: LLMExtractedProcurementData) -> str:
    """
    Compact one-liner summary for recovery context (keeps the prompt small).
    """
    lines = []
    lines.append(f"isProcurementRequest: {p.isProcurementRequest}")
    lines.append(f"title: {p.title or ''}")
    lines.append(f"vendorName: {p.vendorName or ''}")
    lines.append(f"vatNumber: {p.vatNumber or ''}")
    lines.append(f"orderLines.count: {len(p.orderLines or [])}")
    return "\n".join(lines)


def pdf_to_base64_images(pdf_bytes: bytes, dpi: int = 264) -> List[Tuple[str, str]]:
    """
    Render the first and last page of a PDF into base64-encoded PNG data URIs.
    Fully in-memory; no filesystem writes.
    Returns: [(filename, data_uri), ...]
    """
    images: List[Tuple[str, str]] = []
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        if len(doc) == 0:
            return images

        pages_to_render = [0] if len(doc) == 1 else [0, len(doc) - 1]
        for i in pages_to_render:
            page = doc.load_page(i)
            pix = page.get_pixmap(dpi=dpi, alpha=False)
            png_bytes = pix.tobytes("png")
            b64 = base64.b64encode(png_bytes).decode("utf-8")
            data_uri = f"data:image/png;base64,{b64}"
            images.append((f"page-{i+1}.png", data_uri))
    return images

def pdf_to_base64_images_all_pages(pdf_bytes: bytes, dpi: int = 200) -> List[Tuple[str, str]]:
    images: List[Tuple[str, str]] = []
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for i in range(len(doc)):
            page = doc.load_page(i)
            pix = page.get_pixmap(dpi=dpi, alpha=False)
            png_bytes = pix.tobytes("png")
            b64 = base64.b64encode(png_bytes).decode("utf-8")
            data_uri = f"data:image/png;base64,{b64}"
            images.append((f"page-{i+1}.png", data_uri))
    return images