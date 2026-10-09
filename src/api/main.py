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

import io
import shutil
import urllib.parse
import urllib.robotparser
from pathlib import Path

import trafilatura
import pytesseract
from PIL import Image
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from src.api.schemas import ExtractResponse, ScoreRequest, ScoreResponse, UrlExtractRequest
from src.api import pipeline

# Locate the Tesseract OCR binary without relying on it being on PATH. The official
# UB-Mannheim Windows installer (the one the student's setup instructions point to) does
# NOT add itself to PATH by default, which is a well-known gotcha -- pytesseract then
# raises TesseractNotFoundError even though Tesseract is genuinely installed. Fall back to
# the installer's own default locations (both the 64-bit and 32-bit Program Files paths)
# before giving up; this costs nothing on Linux/Mac (shutil.which succeeds there and the
# fallback paths simply don't exist) and makes the Windows case work without the student
# having to edit their system PATH by hand.
if shutil.which("tesseract") is None:
    for _candidate in (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ):
        if Path(_candidate).exists():
            pytesseract.pytesseract.tesseract_cmd = _candidate
            break

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


# ----------------------------------------------------------------------------
# URL / screenshot text-extraction helpers (added 2026-10-09)
#
# WHAT THESE ARE: pure pre-fill conveniences. Both new routes below (/extract-url,
# /extract-image) only ever return extracted text for the frontend to drop into the
# EXISTING manual-entry `text` field, for the user to read and edit before they press
# the EXISTING submit button that calls /score. Neither route touches /score, pipeline.py,
# the trained model, ScoreRequest.text/url semantics, or Stage 9's closed test set in any
# way -- they add new, additive, non-ML endpoints only. See decisions.md, 2026-10-09,
# "URL and screenshot input added as pre-fill conveniences" for the full reasoning,
# including: why LinkedIn is excluded outright rather than relying on robots.txt alone,
# why a robots.txt check decides every other domain instead of a hardcoded allowlist, why
# pytesseract was chosen for OCR (tested directly against the student's own 8 example
# images before deciding), and an explicit note that the URL-fetch code's real-world
# behaviour was reasoned through and checked only via indirect signals (WebFetch against
# the same URLs) -- it was never executed end-to-end by Claude, because every fetch tool
# available to Claude in this session is itself blocked from reaching arbitrary external
# sites by its own outbound proxy. See src/api/live_url_extract_check.py for the
# standalone script that performs that real end-to-end check, which only the student's
# own machine (unrestricted network) can run.

# Sites excluded outright, regardless of robots.txt: ToS-prohibited and/or not practically
# fetchable as static HTML (LinkedIn job pages are rendered client-side; the posting is
# not present in the initial HTML trafilatura would see).
_EXTRACT_URL_EXCLUDED_DOMAINS = {
    "linkedin.com",
    # Added 2026-10-09 after real-world testing: its robots.txt disallows this path for at
    # least some crawlers (confirmed directly), but the generic robots.txt check below did
    # not reliably catch it, AND separately its pages don't extract cleanly (trafilatura
    # pulls account/navigation chrome, not the actual posting) -- excluded outright rather
    # than relying on a check that didn't hold up against the real site.
    "topjobs.lk",
}


def _extract_url_domain_excluded(netloc: str) -> bool:
    netloc = netloc.lower()
    return any(
        netloc == d or netloc.endswith("." + d) for d in _EXTRACT_URL_EXCLUDED_DOMAINS
    )


def _extract_url_robots_allowed(url: str) -> bool:
    """Checks the target site's robots.txt. Fails OPEN (returns True) only when robots.txt
    itself cannot be fetched/parsed at all -- an explicit Disallow is always honoured.
    This is what automatically excludes topjobs.lk without it needing to be hardcoded."""
    parsed = urllib.parse.urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    parser = urllib.robotparser.RobotFileParser()
    parser.set_url(robots_url)
    try:
        parser.read()
    except Exception:
        return True
    return parser.can_fetch("CredibilityScoringResearchBot/0.1", url)


@app.post("/extract-url", response_model=ExtractResponse)
def extract_url(request: UrlExtractRequest):
    """Best-effort text extraction from a job-posting URL. Returns extracted text/title
    for the user to review -- never auto-submitted. Does not implement or touch
    ScoreRequest.url (that /score-level stub, above, is unchanged and still returns 501)."""
    url = request.url.strip()
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise HTTPException(status_code=400, detail="Please provide a full http(s) URL.")

    if _extract_url_domain_excluded(parsed.netloc):
        raise HTTPException(
            status_code=422,
            detail=f"{parsed.netloc} cannot be fetched automatically (terms of service / "
                   "page is not plain HTML). Please copy the posting text and paste it "
                   "directly into the text box instead.",
        )

    try:
        robots_ok = _extract_url_robots_allowed(url)
    except Exception:
        robots_ok = True
    if not robots_ok:
        raise HTTPException(
            status_code=422,
            detail=f"{parsed.netloc}'s robots.txt disallows automated access to this page. "
                   "Please copy the posting text and paste it directly into the text box "
                   "instead.",
        )

    try:
        downloaded = trafilatura.fetch_url(url)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Could not reach that URL: {e}")

    if not downloaded:
        raise HTTPException(
            status_code=502,
            detail="Could not reach that URL, or the site blocked the request. Please "
                   "copy the posting text and paste it directly into the text box instead.",
        )

    text = trafilatura.extract(downloaded, favor_recall=True)
    title = None
    try:
        metadata = trafilatura.extract_metadata(downloaded)
        title = metadata.title if metadata else None
    except Exception:
        title = None

    if not text or not text.strip():
        raise HTTPException(
            status_code=422,
            detail="Reached the page but couldn't find extractable posting text on it. "
                   "Please copy the posting text and paste it directly into the text box "
                   "instead.",
        )

    cleaned = text.strip()
    _JS_PLACEHOLDER_PHRASES = (
        "enable javascript",
        "javascript is required",
        "please enable javascript",
        "requires javascript",
    )
    looks_like_real_content = (
        len(cleaned) >= 100
        and not any(p in cleaned.lower() for p in _JS_PLACEHOLDER_PHRASES)
    )
    if not looks_like_real_content:
        raise HTTPException(
            status_code=422,
            detail="Reached the page, but what came back doesn't look like real posting "
                   "text (too short, or the page needs JavaScript to render and this "
                   "fetch only sees the static HTML). Please copy the posting text and "
                   "paste it directly into the text box instead.",
        )

    return ExtractResponse(title=title, text=cleaned, source_url=url)


@app.post("/extract-image", response_model=ExtractResponse)
async def extract_image(file: UploadFile = File(...)):
    """OCR text extraction from an uploaded job-posting screenshot. Returns extracted text
    for the user to review -- never auto-submitted. Uses pytesseract + the system Tesseract
    binary; if Tesseract isn't installed on the machine running this server, fails with a
    clear 503 rather than a bare stack trace."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400, detail="Please upload an image file (PNG, JPG, etc)."
        )

    raw = await file.read()
    try:
        image = Image.open(io.BytesIO(raw))
        image.load()
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read that file as an image.")

    try:
        text = pytesseract.image_to_string(image)
    except pytesseract.TesseractNotFoundError:
        raise HTTPException(
            status_code=503,
            detail="OCR engine (Tesseract) is not installed on this server. See the setup "
                   "instructions to install it, then restart the server.",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR failed: {e}")

    if not text or not text.strip():
        raise HTTPException(
            status_code=422,
            detail="No readable text was found in that image. Try a clearer screenshot.",
        )

    return ExtractResponse(title=None, text=text.strip(), source_url=None)


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
