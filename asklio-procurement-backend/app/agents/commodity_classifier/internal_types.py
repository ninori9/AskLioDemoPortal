from typing import List, Dict, Any, Tuple, Optional, Type
from pydantic import BaseModel, Field

# ---------- Internal LLM schema ----------
class _ScoreItem(BaseModel):
    id: int
    score: float = Field(ge=0.0, le=1.0)


class _LLMScoring(BaseModel):
    scores: List[_ScoreItem] = Field(default_factory=list)
    rationale: str = ""
    
class _FinalCandidate(BaseModel):
    id: int
    label: str
    category: Optional[str]
    examples: List[str] = Field(default_factory=list)

class _FinalDecision(BaseModel):
    chosen_id: int
    probability: float = Field(ge=0.0, le=1.0)