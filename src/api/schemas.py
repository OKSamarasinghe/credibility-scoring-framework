"""
Request/response schemas for the /score endpoint.

Contract was originally text/URL-only. Expanded 2026-10-08 (decisions.md, "Stage 8 wiring:
API input contract resolved") after finding `extract_all()` (Stage 4) needs ~10 EMSCAD-shaped
structured fields that cannot be recovered from pasted prose -- without them, E3 (metadata
completeness) and E4 (text-metadata consistency, the project's actual contribution) are
permanently dark on every live request. This reconciles schemas.py with what
`Framework_Explanation_Walkthrough.docx` (Step 1) already specified: "raw posting text with
any structured fields the caller can supply." Do not change field names/types without
updating that decisions.md entry and PROJECT_PLAN.md/project.md's Input description first.
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field, model_validator


class ScoreRequest(BaseModel):
    """
    Input contract: raw text is the supported, primary path. URL is secondary and
    best-effort (not yet implemented). Any of the structured EMSCAD-shaped fields below
    are OPTIONAL -- a field left out is treated exactly like a missing field in EMSCAD
    (Stage 1's own missingness semantics, reused unchanged for live requests). This is
    not a workaround: E3's completeness score and most of E4's C1-C6 rules are defined
    entirely in terms of whether these fields are present, so "optional, honestly missing
    if not supplied" is the correct behaviour, not a simplification.
    """
    text: Optional[str] = Field(
        default=None,
        description="Raw job posting body text (maps to EMSCAD's 'description' field). "
                    "Primary supported input."
    )
    url: Optional[str] = Field(
        default=None,
        description="Job posting URL. Secondary, best-effort — only for sources "
                    "whose terms allow automated retrieval. Not yet implemented."
    )

    # --- Optional structured fields (Framework_Explanation_Walkthrough.docx, Step 1) ---
    title: Optional[str] = Field(default=None, description="Job title.")
    company_profile: Optional[str] = Field(
        default=None, description="Employer's own description of itself, if provided."
    )
    requirements: Optional[str] = Field(default=None, description="Requirements section text.")
    benefits: Optional[str] = Field(default=None, description="Benefits section text.")
    location: Optional[str] = Field(
        default=None,
        description='Posting location as "Country, Region, City" (as many parts as known, '
                    'left to right) — matches EMSCAD\'s location format, which C2 and E2 '
                    "location-specificity both key off."
    )
    telecommuting: Optional[bool] = Field(
        default=None,
        description="Whether the posting is explicitly marked remote/telecommuting. "
                    "If not supplied, treated as False (on-site) -- see decisions.md "
                    "2026-10-08 for why this default can produce a spurious C1 flag if the "
                    "posting text itself describes remote work and the caller just didn't say."
    )
    has_company_logo: Optional[bool] = Field(
        default=None,
        description="Whether the platform shows a company logo on this posting. If not "
                    "supplied, treated as genuinely missing (unlike EMSCAD, where this is "
                    "never missing), which lowers the E3 completeness score honestly rather "
                    "than guessing."
    )
    has_questions: Optional[bool] = Field(
        default=None,
        description="Whether the posting includes screening questions. Same missing-if-"
                    "unsupplied behaviour as has_company_logo."
    )
    department: Optional[str] = Field(default=None, description="Hiring department, if known.")
    salary_range: Optional[str] = Field(
        default=None,
        description='Salary range as "LOW-HIGH" (e.g. "50000-65000"), matching EMSCAD\'s '
                    "format. A value that doesn't parse this way is treated as not evaluable "
                    "for C6, not an error."
    )
    employment_type: Optional[str] = Field(
        default=None, description='e.g. "Full-time", "Part-time", "Contract".'
    )
    required_experience: Optional[str] = Field(
        default=None, description='e.g. "Entry level", "Mid-Senior level".'
    )
    required_education: Optional[str] = Field(
        default=None, description='e.g. "Bachelor\'s Degree", "High School or equivalent".'
    )
    industry: Optional[str] = Field(default=None, description="Industry category, if known.")
    function: Optional[str] = Field(default=None, description="Job function category, if known.")

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
