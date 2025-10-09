from __future__ import annotations
import logging
from typing import List, Dict, Optional
from .interface import AbstractCommodityClassifier
from .contracts import (
    CommodityClassifyIn,
    CommodityClassifyOut,
    CONTRACT_VERSION,
)
from app.ai.base import AIClient
from app.agents.base import AgentError
from app.agents.commodity_classifier.prompt_templates import build_scoring_messages, build_rerank_messages
from app.weaviate import operations as wx
from app.weaviate.text_formatter import build_request_embedding_text
from app.agents.commodity_classifier.internal_types import _FinalCandidate, _FinalDecision, _LLMScoring, _ScoreItem

logger = logging.getLogger(__name__)

# ---------- Small utilities ----------
def _normalize_text(s: Optional[str]) -> str:
    if not s:
        return ""
    return " ".join(s.strip().split())


# ---------- Implementation ----------
class LLMCommodityClassifier(AbstractCommodityClassifier):
    """
    Minimal, deterministic flow:
      1) Normalize inputs.
      2) Ask LLM to return scores for provided commodity group ids.
      3) Retrieve examples for the top 3 groups using embeddings.
      4) Ask LLM to return scores based on this past data
    """

    def __init__(
        self,
        ai_client: AIClient,
        *,
        temperature: float = 0.1,
        max_output_tokens: int = 2000,
        top_n_alternatives: int = 3,
    ):
        self._ai = ai_client
        self._temperature = temperature
        self._max_tokens = max_output_tokens
        self._top_n_alts = top_n_alternatives

    def run(self, inp: CommodityClassifyIn) -> CommodityClassifyOut:
        # Guard: must have candidate groups
        if not inp.available_commodity_groups:
            raise AgentError("No valid commodity groups provided.")

        # 1) Normalize
        title = _normalize_text(inp.title)
        vendor = _normalize_text(inp.vendor_name)
        vat = _normalize_text(inp.vat_id)
        lines = [_normalize_text(x) for x in (inp.order_lines_text or [])]

        groups = inp.available_commodity_groups
        groups_by_id = {g.id: g for g in groups}

        # 2) Build messages (centralized in prompt_templates)
        messages = build_scoring_messages(
            title=title,
            vendor_name=vendor,
            vat_id=vat,
            order_lines_text=lines,
            groups=groups,
        )

        # 3) Structured LLM call
        try:
            parsed, _meta = self._ai.complete_pydantic(
                messages=messages,
                response_model=_LLMScoring,
                model="gpt-4.1-2025-04-14"
            )
            llm_result: _LLMScoring = parsed
        except Exception as e:
            # Surface a consistent agent error up the stack
            raise AgentError(f"AI model error during scoring of commodity groups: {e}")

        # Sanity: filter to known ids only, clamp scores
        known_scores = [
            _ScoreItem(id=s.id, score=max(0.0, min(1.0, s.score)))
            for s in llm_result.scores
            if s.id in groups_by_id
        ]
        if not known_scores:
            raise AgentError("LLM returned no valid scores for provided commodity groups.")

        # 4) Embedding step: Use examples to get more reliable result
        sorted_scores = sorted(known_scores, key=lambda x: x.score, reverse=True)
        TOP_CAND = min(3, len(sorted_scores))
        top_ids: List[int] = [s.id for s in sorted_scores[:TOP_CAND]]

        # One embedding for the query
        query_text = build_request_embedding_text(
            title=title,
            vendor_name=vendor,
            vat_id=vat,
            order_lines_text=lines,
        )

        try:
            query_vec = self._ai.embed(query_text)
        except Exception as e:
            logger.exception("Embedding failed; skipping retrieval: %s", e)
            query_vec = None

        # Gather evidence for each top candidate
        evidence_map: Dict[int, List[str]] = {}
        all_have_examples = True

        if query_vec is None:
            all_have_examples = False
        else:
            for gid in top_ids:
                try:
                    hits = wx.search_similar(
                        vector=query_vec, 
                        top_k=2, 
                        commodity_group_id=str(gid)
                    )
                except Exception as e:
                    logger.exception("Weaviate search failed for gid=%s: %s", gid, e)
                    hits = []
                examples = [
                    h.get("embeddedRequestContext", "")
                    for h in hits
                    if h.get("embeddedRequestContext")
                ]
                evidence_map[gid] = examples
                if len(examples) == 0:
                    all_have_examples = False

        # If ANY of the top candidates lacks examples, skip the retrieval re-rank completely
        if not all_have_examples:
            evidence_map = {} 
        
        if all_have_examples and evidence_map:
            # Build candidate payloads with examples
            candidates = []
            for gid in top_ids:
                g = groups_by_id[gid]
                candidates.append(_FinalCandidate(
                    id=gid,
                    label=g.label,
                    category=g.category,
                    examples=evidence_map.get(gid, [])[:2],
                ))

            messages = build_rerank_messages(title, vendor, vat, lines, candidates)

            try:
                final_decision, _meta = self._ai.complete_pydantic(
                    messages=messages,
                    response_model=_FinalDecision,
                    model="gpt-4.1-2025-04-14"
                )
                llm_decision: _FinalDecision = final_decision
                chosen_id = llm_decision.chosen_id
                prob = llm_decision.probability
                # Safety: if the model picked an id that isn't in our top_ids, fall back
                if chosen_id not in {c.id for c in candidates}:
                    chosen_id = top_ids[0]
                    prob = next(s.score for s in sorted_scores if s.id == chosen_id)
            except Exception as e:
                logger.exception("Re-rank failed; falling back to first-pass: %s", e)
                chosen_id = top_ids[0]
                prob = next(s.score for s in sorted_scores if s.id == chosen_id)
        else:
            # No retrieval step: first-pass winner
            chosen_id = top_ids[0]
            prob = next(s.score for s in sorted_scores if s.id == chosen_id)

        return CommodityClassifyOut(
            suggested_commodity_group_id=chosen_id,
            confidence=prob,
            trace_id=inp.trace_id,
            contract_version=CONTRACT_VERSION,
        )