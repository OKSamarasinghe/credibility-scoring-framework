# Explainable Credibility Scoring Framework for Online Recruitment Posts

BSc (Hons) Computing final-year individual project — Coventry University / NIBM.
O.K. Samarasinghe — Coventry 16116041, NIBM COBSCCOMP242P-069.

A backend REST API that scores the credibility of online recruitment postings using a
four-category evidence taxonomy (text/content cues, identity & contact cues, metadata
completeness, and text–metadata consistency verification), fused with a fine-tuned
DistilBERT text model. Output is a calibrated 0–100 credibility score, a risk band, and a
human-readable explanation generated from SHAP feature attributions and rule-based
consistency checks — never a bare number. Built as a Design Science Research artefact, with
a small frontend (**JobCred**) for manual testing and demonstration.

## Status

The artefact is **fully built, trained, evaluated, and verified end-to-end** — all 9
methodology stages (plus Stage 8b) are complete and committed, and the one-time test-set
evaluation (Stage 9) is closed: **no further model, feature, seed, or architecture change
is permitted for the rest of this project.** The DistilBERT+evidence fusion model beats
both baselines on validation F1 (0.671±0.030) and on test-set F1; full metrics, calibration,
ablation, and Tier 2 temporal-transfer results are in `docs/methodology.md`. A frontend
(`frontend/index.html`, served at `GET /`) is built and committed; its URL/screenshot
pre-fill features were tested live against 13 real job-posting sites (8 extracted cleanly,
4 correctly declined, 1 failed gracefully). Remaining work is the dissertation write-up (Chapters 4–6) — see
`docs/project.md` → "Where I am right now" for the live, detailed status, and
`docs/decisions.md` for the full reasoning behind every design choice made along the way.

## Repository structure

- `data/` — dataset documentation (raw EMSCAD data not stored — see `data/README.md`)
- `audit/` — data-quality audit script and measured results
- `src/` — pipeline code:
  - `ingestion/` — EMSCAD loading
  - `partitioning/` — leakage-controlled train/validation/test split
  - `features/` — E1–E4 multi-signal evidence extraction
  - `taxonomy_audit/` — C1–C6 consistency-rule validation
  - `models/` — baseline (TF-IDF+LogReg/RF) and DistilBERT+evidence fusion training
  - `calibration/` — isotonic/Platt score calibration
  - `explain/` — SHAP explainability
  - `evaluation/` — Stage 9 test-set evaluation, ablation, Tier 2 transfer
  - `api/` — FastAPI app (`main.py`), the real inference pipeline (`pipeline.py`),
    request/response schemas (`schemas.py`), and live smoke-test scripts
- `models/` — trained model artifacts (`.joblib` / `.pt`). **Gitignored due to size** (the
  DistilBERT state dicts alone are ~265MB each) — not present in a fresh clone; see Setup.
- `frontend/` — `index.html`, a self-contained static page (no build step), served by the
  API at `GET /`
- `docs/` — `project.md` (current state), `decisions.md` (every design decision and why),
  `methodology.md` (how each stage was run, with results), `sources.md` (claim-verification
  ledger), `PROJECT_PLAN.md` (day-by-day sprint plan)
- `notebooks/` — exploratory work
- `reports/` — evaluation outputs (JSON/CSV results from each stage)
- `tests/` — automated tests (`pytest`)

## Setup

Requires **Python 3.13** and, for the full model pipeline, an NVIDIA GPU with CUDA 12.4
(the project was built and trained against an RTX 3050 — CPU-only will work but training is
significantly slower; inference is fine on CPU).

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
```

**Dataset:** obtain the EMSCAD CSV (Vidros et al., 2017) and place it at
`data/raw/DataSet.csv` — not included in this repository. See `data/README.md`.

**Trained model artifacts:** `models/*.joblib` and `models/*.pt` are gitignored (too large
for the repository) and are **not** included in a fresh clone. To run the API you either
need these files copied in directly, or you need to re-run the training stages
(`src/models/`, `src/calibration/`) against the dataset above — see `docs/methodology.md`
for the exact stage-by-stage commands used to produce them originally.

**Optional — URL/screenshot pre-fill features** (`POST /extract-url`, `POST
/extract-image`, used by the frontend's "Fetch from URL" / "Extract from screenshot"
buttons): for OCR, install the Tesseract OCR binary separately (on Windows, the
[UB-Mannheim installer](https://github.com/UB-Mannheim/tesseract/wiki); the code already
handles the installer's default path not being added to `PATH`). These two routes are
convenience pre-fill helpers only — `POST /score` itself never depends on them.

**Run the API:**

```bash
uvicorn src.api.main:app --reload
```

Then open `http://127.0.0.1:8000/` for the frontend, or `http://127.0.0.1:8000/docs` for
the interactive API docs.

## API

| Route | Purpose |
|---|---|
| `GET /` | Serves the JobCred frontend |
| `GET /health` | Liveness check |
| `POST /score` | The core endpoint — scores a posting, returns `credibility_score` (0–100), `risk_band`, `top_reasons`, `suspicious_phrases`, `contradictions`, and `verification_checklist` |
| `POST /extract-url` | Best-effort text extraction from a job-posting URL, for pre-filling the form (checks `robots.txt`; does not call `/score`) |
| `POST /extract-image` | OCR text extraction from a screenshot, for pre-filling the form (does not call `/score`) |

See `src/api/schemas.py` for the full request/response contracts.

## Evidence taxonomy

| | Category | What it checks |
|---|---|---|
| **E1** | Text & content cues | Scam-style language — artificial urgency, guaranteed pay, requests to pay upfront |
| **E2** | Identity & contact cues | How the employer identifies itself — company profile, location specificity, contact channels |
| **E3** | Metadata completeness | Which standard structured fields are actually filled in |
| **E4** | Text–metadata consistency | Whether the free text and structured fields agree (C1–C6 rule checks) |

A fine-tuned DistilBERT model reads the posting text fused with these structured evidence
features; SHAP explains the structured-feature contributions, and C1–C6 rule evidence
explains any detected text/metadata mismatch directly.

## Tests

```bash
pytest tests/
```

51/51 tests passing as of the last full run (2026-10-08) — covers ingestion, feature
extraction, and partitioning.

## Documentation

This README is a quick orientation. For anything deeper:

- **`docs/project.md`** — current state, objectives, scope, and "Where I am right now"
- **`docs/decisions.md`** — every real design decision made, the options considered, and why
- **`docs/methodology.md`** — how each of the 9 stages (+8b) was run, with full results
- **`docs/sources.md`** — verification ledger for claims and figures
- **`docs/PROJECT_PLAN.md`** — the day-by-day sprint plan

## Author

Oshadha Samarasinghe — Coventry University (16116041), NIBM (COBSCCOMP242P-069)
BSc (Hons) Computing, Final Year Research Project.
