"""
FastAPI application — Stage 8.

WHAT THIS FILE DOES RIGHT NOW:
    Defines the /score route, validates input against the fixed JSON contract,
    and returns HTTP 501 Not Implemented with a clear message — because the
    pipeline it would call (preprocessing -> feature extraction -> prediction
    -> explainability) does not exist yet. Stage 1 (ingestion) is done;
    Stages 4-7 are not.

WHAT THIS FILE DELIBERATELY DOES NOT DO:
    It does not fake a score, a risk band, or an explanation. Guardrail:
    "never invent facts, numbers, or results." A hardcoded response here would
    look like progress and would actually be a liability — it would have to be
    torn out, not extended, once the real pipeline exists, and could tempt a
    fabricated result into a demo before Stage 5/6/7 produce a real one.

HOW THIS GETS FILLED IN, STAGE BY STAGE:
    Stage 4 (feature extraction) -> replace `extract_features()` stub
    Stage 5+6 (model + calibration) -> replace `predict()` stub
    Stage 7 (explainability) -> replace `explain()` stub
    Each stub below is the exact seam where that stage's real code plugs in.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from src.api.schemas import ScoreRequest, ScoreResponse

app = FastAPI(
    title="Explainable Credibility Scoring Framework — API",
    description="Backend REST API for scoring online recruitment posting credibility.",
    version="0.1.0",
)


# ----------------------------------------------------------------------------
# Pipeline stubs — each raises NotImplementedError until its stage is built.
# Kept as separate functions (not inlined) so each can be swapped for real
# code independently, without touching the route handler below.
# ----------------------------------------------------------------------------

def preprocess(text: str) -> str:
    """Stage 1/4 seam: cleaning + normalisation ahead of feature extraction."""
    raise NotImplementedError("Stage 4 not yet built.")


def extract_features(clean_text: str, raw_text: str):
    """Stage 4 seam: E1-E4 evidence vector for one posting."""
    raise NotImplementedError("Stage 4 not yet built.")


def predict(features) -> float:
    """Stage 5/6 seam: trained, calibrated model -> probability in [0, 1]."""
    raise NotImplementedError("Stage 5/6 not yet built — no trained model exists.")


def explain(features, probability: float) -> dict:
    """Stage 7 seam: SHAP/LIME + rule messages -> the four explanation fields."""
    raise NotImplementedError("Stage 7 not yet built.")


# ----------------------------------------------------------------------------
# Route
# ----------------------------------------------------------------------------

@app.post("/score", response_model=ScoreResponse)
def score(request: ScoreRequest):
    if request.url:
        # build.md section 1: URL input is secondary and best-effort, and is
        # explicitly NOT the artefact's core. Not implemented at all yet.
        raise HTTPException(
            status_code=501,
            detail="URL input is not yet implemented. Supply 'text' instead — "
                   "it is the supported, primary input path."
        )

    try:
        clean = preprocess(request.text)
        features = extract_features(clean, request.text)
        probability = predict(features)
        explanation = explain(features, probability)
    except NotImplementedError as e:
        raise HTTPException(
            status_code=501,
            detail=f"Pipeline not yet complete: {e}"
        )

    # Unreachable until the four stubs above are replaced with real stage code.
    # Left here so the eventual wiring is visible in one place.
    return ScoreResponse(
        credibility_score=int(probability * 100),
        risk_band="Low",
        top_reasons=explanation["top_reasons"],
        suspicious_phrases=explanation["suspicious_phrases"],
        contradictions=explanation["contradictions"],
        verification_checklist=explanation["verification_checklist"],
    )


@app.get("/health")
def health():
    """Trivial liveness check — useful for confirming the server itself runs,
    independent of whether the pipeline behind /score is finished."""
    return {"status": "ok", "pipeline_complete": False}
