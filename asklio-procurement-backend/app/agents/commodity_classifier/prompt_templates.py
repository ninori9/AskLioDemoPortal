from __future__ import annotations
from typing import Dict, List, Optional

from .contracts import CommodityGroupRef
from .internal_types import _FinalCandidate

SYSTEM_PROMPT = (
    "You are a procurement request classifier. Given a procurement request and a list of candidate "
    "commodity groups, evaluate how well each group fits the request.\n\n"
    "SCORING RULES:\n"
    "- Assign a calibrated score in [0,1] to each candidate id.\n"
    "- Only include ids with a score strictly greater than 0.0 in your output. "
    "All omitted ids are treated as score = 0.0.\n"
    "- Use the full range: strong matches near 0.8–1.0; weak-but-relevant matches near 0.1–0.3.\n"
    "- Avoid ties when possible; small deltas are acceptable.\n"
    "- If uncertain, prefer low scores over mid scores.\n\n"
    "EVIDENCE WEIGHTING (guideline):\n"
    "- ORDER LINES ≈ 60% importance (most predictive)\n"
    "- TITLE ≈ 30%\n"
    "- VENDOR ≈ 10% (only when it clearly signals a domain; e.g., Adobe → Software)\n\n"
    "CATEGORY CUES (examples, not rules):\n"
    "- Information Technology → Software: licenses, subscriptions, SaaS, named apps (Photoshop, Acrobat), activation keys.\n"
    "- Information Technology → Hardware: laptops, monitors, docks, peripherals, devices.\n"
    "- Information Technology → IT Services: setup/installation, integration, managed service, IT support/maintenance.\n"
    "- Marketing & Advertising → Advertising / Online Marketing: campaigns, banners, paid posts, ad buys.\n"
    "- Facility Management → Renovations / Maintenance / Cleaning: painting, flooring, repairs, janitorial.\n"
    "- Logistics → Courier/Postal/Delivery: shipping labels, parcel services, courier pickups.\n"
    "- Production → Machinery/Spare Parts: machines, line equipment, replacement parts.\n\n"
    "TIE-BREAKING:\n"
    "1) Favor groups explicitly named or strongly implied by ORDER LINES.\n"
    "2) If still close, prefer the more specific subcategory over broader categories.\n"
    "3) If still close, consider clear vendor-domain hints (e.g., Adobe → Software).\n\n"
    "Do not invent ids. Return only the subset of candidates with score > 0.0, "
    "and include a brief rationale summarizing your reasoning."
)

def _render_groups(groups: List[CommodityGroupRef]) -> str:
    """
    Render candidate commodity groups as:
      - [id] Category — Label
    This keeps the prompt readable and uses category to improve discrimination.
    """
    return "\n".join(f"- [{g.id}] {g.category} — {g.label}" for g in groups)


def _render_order_lines(order_lines: List[str]) -> str:
    if not order_lines:
        return "-"
    return "\n".join(order_lines)


def build_scoring_messages(
    *,
    title: str,
    vendor_name: str,
    vat_id: Optional[str],
    order_lines_text: List[str],
    groups: List[CommodityGroupRef],
) -> List[Dict[str, str]]:
    """
    Build the (system, user) messages for the commodity group scoring task.
    NOTE: We do NOT instruct the model to output JSON here because the caller uses
    structured outputs (Pydantic schema) to enforce the shape.
    """
    user_content = (
        f"REQUEST TITLE:\n{title}\n\n"
        f"VENDOR NAME:\n{vendor_name}\n\n"
        f"VENDOR VAT ID:\n{vat_id or '-'}\n\n"
        f"ORDER LINES:\n{_render_order_lines(order_lines_text)}\n\n"
        "CANDIDATE COMMODITY GROUPS (id • category — name):\n"
        f"{_render_groups(groups)}\n\n"
        "Score every listed id in [0,1] based on how well it matches this request, "
        "then briefly explain your reasoning."
    )

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
    

def build_rerank_messages(
    title: str,
    vendor: str,
    vat: str,
    lines: List[str],
    candidates: List["_FinalCandidate"],
):
    system = {
        "role": "system",
        "content": (
            "You are a procurement request classifier.\n\n"
            "Inputs:\n"
            "- One new procurement request (title, vendor, VAT ID, order lines).\n"
            "- Several candidate commodity groups; each provides:\n"
            "  • id (int), label (string), category (string)\n"
            "  • 1–2 historical example requests previously labeled with that group\n\n"
            "Task:\n"
            "- Select the single best-matching commodity group for the new request.\n"
            "- Provide a calibrated probability in [0,1] for your confidence.\n\n"
            "Judging principles:\n"
            "- Match primarily by semantic similarity between the new request and the candidate examples.\n"
            "- Use concrete cues in order lines and title (nouns, products, actions) to confirm or disconfirm a match.\n"
            "- Prefer specific subcategories over generic ones when evidence is similar.\n"
            "- If multiple candidates are plausible, pick the closest match but reflect uncertainty with a lower probability.\n"
            "- If evidence is strong, give a probability near 0.8–1.0."
            "- If evidence is weak overall, keep probability low (e.g., ≤ 0.3).\n"
            "- Do not invent ids. Probability must be within [0,1]."
        ),
    }


    # Format the user content clearly
    candidate_blocks = []
    for c in candidates:
        examples_formatted = (
            "\n".join([f"    • {ex}" for ex in c.examples]) if c.examples else "    (no examples)"
        )
        candidate_blocks.append(
            f"---\n"
            f"ID: {c.id}\n"
            f"LABEL: {c.label}\n"
            f"CATEGORY: {getattr(c, 'category', '-')}\n"
            f"PRIOR SCORE: {c.prior_score:.2f}\n"
            f"EXAMPLES:\n{examples_formatted}"
        )

    user_content = (
        f"REQUEST INFORMATION\n"
        f"--------------------\n"
        f"TITLE: {title}\n"
        f"VENDOR: {vendor}\n"
        f"VAT: {vat or '-'}\n"
        f"ORDER LINES:\n"
        + ("\n".join(f"  • {l}" for l in lines) if lines else "  (none)") + "\n\n"
        f"CANDIDATE COMMODITY GROUPS\n"
        f"---------------------------\n"
        + "\n\n".join(candidate_blocks)
    )

    user = {"role": "user", "content": user_content}

    return [system, user]