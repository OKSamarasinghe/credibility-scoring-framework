"""
Request/response schemas for the /score endpoint.

Contract is fixed by build.md section 1 — do not change field names or types
without updating that spec first, since it's what the dissertation describes.
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field, model_validator


class ScoreRequest(BaseModel):
    """
    Input contract: raw text is the supported, primary path. URL is secondary
    and best-effort (build.md section 1) — NOT the artefact's core input method.
    Exactly one of the two must be supplied.
    """
    text: Optional[str] = Field(
        default=None,
        description="Raw job posting text. Primary supported input."
    )
    url: Optional[str] = Field(
        default=None,
        description="Job posting URL. Secondary, best-effort — only for sources "
                    "whose terms allow automated retrieval. Not yet implemented."
    )

    @model_validator(mode="after")
    def exactly_one_input(self):
        if not self.text and not self.url:
            raise ValueError("Provide either 'text' or 'url'.")
        if self.text and self.url:
            raise ValueError("Provide only one of 'text' or 'url', not both.")
        return self


class Contradiction(BaseModel):
    rule: str          # e.g. "C1"
    field: str          # e.g. "telecommuting"
    detail: str          # human-readable description of the contradiction


class ScoreResponse(BaseModel):
    credibility_score: int = Field(ge=0, le=100, description="Calibrated 0-100 score, higher = more credible")
    risk_band: Literal["High", "Medium", "Low"]
    top_reasons: List[str]
    suspicious_phrases: List[str]
    contradictions: List[Contradiction]
    verification_checklist: List[str]
