"""
FastAPI application — Stage 8.

WHAT THIS FILE DOES NOW (updated 2026-10-08)
    Defines the /score route and wires it to the REAL pipeline in `src/api/pipeline.py`:
    Stage 1 preprocessing -> Stage 4 feature extraction -> Stage 5/6 prediction+calibration
    -> Stage 7 explanation. No stage is faked; if a required model/calibrator file is
    missing, PipelineState raises on first use and the route surfaces that as a 503, not a
    fabricated score. See decisions.md, 2026-10-08, "Stage 8 wiring: API input contract
    resolved" for the request-schema decision and two deployment-time findings caught while
    wiring this (risk-band direction, E2 contact-token features being inert on live text).

HOW THIS WAS FILLED IN, STAGE BY STAGE
    Stage 4 (feature extraction) -> src.api.pipeline.build_posting_row / compute_features
    Stage 5+6 (model + calibration) -> src.api.pipeline.run_inference
    Stage 7 (explainability) -> src.api.pipeline.build_explanation
    Model/scaler/tokenizer/calibrator are loaded ONCE (PipelineState, lazy singleton) on the
    first request that needs them, not per-request -- the DistilBERT checkpoint alone is
    ~250MB, and reloading it per request would make /score unusably slow.
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from src.api.schemas import ScoreRequest, ScoreResponse
from src.api import pipeline

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"

app = FastAPI(
    title="Explainable Credibility Scoring Framework — API",
    description="Backend REST API for scoring online recruitment posting credibility.",
    version="0.2.0",
)


# ----------------------------------------------------------------------------
# Route
# ----------------------------------------------------------------------------

@app.post("/score", response_model=ScoreResponse)
def score(request: ScoreRequest):
    if request.url:
        # build.md/PROJECT_PLAN.md section 1: URL input is secondary and best-effort, and
        # is explicitly NOT the artefact's core. Not implemented at all yet.
        raise HTTPException(
            status_code=501,
            detail="URL input is not yet implemented. Supply 'text' instead — "
                   "it is the supported, primary input path."
        )

    try:
        state = pipeline.get_state()
    except RuntimeError as e:
        # A missing model/calibrator file is a server-not-ready problem, not a client
        # error, and not something to paper over with a fabricated score. Guardrail:
        # "never invent facts, numbers, or results."
        raise HTTPException(status_code=503, detail=f"Pipeline not ready: {e}")

    df_row = pipeline.build_posting_row(request)
    features_df, X_raw, X_scaled = pipeline.compute_features(df_row, state)
    inference = pipeline.run_inference(df_row, X_scaled, state)
    explanation = pipeline.build_explanation(
        features_df, X_raw, inference["pooled_embedding"], state
    )

    return ScoreResponse(
        credibility_score=inference["score"],
        risk_band=inference["risk_band"],
        top_reasons=explanation["top_reasons"],
        suspicious_phrases=explanation["suspicious_phrases"],
        contradictions=explanation["contradictions"],
        verification_checklist=explanation["verification_checklist"],
    )


@app.get("/", include_in_schema=False)
def serve_frontend():
    """Serves the manual-entry demo UI (frontend/index.html) at the bare root, which
    previously 404'd. Purely additive: a static HTML/CSS/JS page that calls POST /score
    on this same origin (no CORS setup needed, no new dependency, no change to any
    existing route, pipeline, or model code). The page never auto-extracts structured
    fields from pasted text -- every field the user doesn't fill in is left out of the
    request entirely, same genuinely-missing semantics ScoreRequest already defines.
    See decisions.md, 2026-10-09, "Minimal manual-entry frontend added" for why an
    auto-parsing frontend was deliberately rejected in favour of this."""
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Frontend not found.")
    return FileResponse(index_path)


@app.get("/health")
def health():
    """Liveness check. pipeline_loaded reflects whether the model/calibrator have been
    loaded yet (lazy on first /score call) — it is NOT a correctness check of the pipeline,
    just whether PipelineState has been constructed in this process."""
    return {"status": "ok", "pipeline_loaded": pipeline._STATE is not None}
