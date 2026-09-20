# PROJECT_PLAN.md — Full Project Plan (Start to End)

_Compiled 2026-08-27, last refreshed 2026-08-27 (Stage 2 status corrected). This is a DATED
SNAPSHOT, not a live-synced file — refresh it at real milestones (a stage completing, a
decision closing), not every session. `workplan.md` remains the living, frequently-updated
status tracker; `decisions.md`, `methodology.md`, `sources.md` remain the detailed logs and
are authoritative over this file on any specific number. If a fact here conflicts with one
of those four files, or with `SKILL.md`'s standing rules, THEY win — this file is a
convenience summary, never a primary source._

---

## 1. What this is

**"An Explainable Credibility Scoring Framework for Online Recruitment Posts Using
Multi-Signal Evidence and Consistency Verification."**

BSc (Hons) Computing final-year individual project — Coventry University / NIBM, Colombo 7.
O.K. Samarasinghe — Coventry 16116041, NIBM COBSCCOMP242P-069.

Design Science Research. The deliverable is a **built and evaluated artefact** — a backend
credibility-scoring API — plus a dissertation and a research paper. Positioned in FEDS terms
as **ex post** (the built system is evaluated, not the design in advance) and predominantly
**artificial** (benchmark dataset, controlled conditions), with a **naturalistic** component
in the Tier 2 assessment.

**⚠️ `project.md` line 19 ("Key deadlines") is still `[FILL IN]`.** Nothing in this plan is
scheduled against a real date. Fill that in — it changes pacing, not scope.

---

## 2. The problem and the gap

Four gaps identified from a ten-study literature review (2017–2026): limited user-facing
explainability; underuse of structured multi-signal evidence; **absence of explicit
text–metadata consistency verification** (the empty column — no reviewed system checks
whether a posting's structured fields contradict its own free text); and binary
fake/real output that gives weak practical decision support.

**The research contribution is consistency verification (E4).** Everything else in the
taxonomy exists to support and contextualise that contribution, not to compete with it.

---

## 3. Objectives and research questions

| ID | Objective | Maps to |
|---|---|---|
| O1 | Define and validate a four-category evidence taxonomy, validated by manual audit | RQ1 |
| O2 | Develop and benchmark a TF-IDF baseline under leakage-controlled evaluation | RQ2 |
| O3 | Combine transformer text representation with structured evidence + consistency flags; quantify the change under matched conditions | RQ3 |
| O4 | Deliver a backend API converting calibrated probabilities into a 0–100 score with verified explanations | RQ4 |
| O5 | Evaluate with full metric set, per-category ablation, and temporal generalisability on contemporary postings | RQ5 |

**Rule held throughout:** no objective or RQ states its own expected result. O3 quantifies
a change; it does not presuppose the change is positive.

---

## 4. The artefact — what gets built

A backend REST API (**FastAPI**) exposing a **`/score`** endpoint.

- **Input:** raw job-posting text (primary, supported path) or a posting URL (secondary,
  best-effort, only where terms allow automated retrieval).
- **Pipeline, executed end-to-end per request:** preprocessing → feature extraction →
  prediction → explainability.
- **Output — single JSON object:**

```json
{
  "credibility_score": 0-100,
  "risk_band": "High | Medium | Low",
  "top_reasons": ["...", "..."],
  "suspicious_phrases": ["..."],
  "contradictions": [{"rule": "C1", "field": "telecommuting", "detail": "on-site vs remote"}],
  "verification_checklist": ["..."]
}
```

The score is a **calibrated probability mapped to 0–100** — never a raw model output.

**Current build status:** the FastAPI app, `/score` route, and the exact request/response
schema above are built and tested (`src/api/main.py`, `src/api/schemas.py`). Every pipeline
stage is an honest stub — raises a clear "not yet built" error rather than inventing a
result. Zero fabricated data anywhere in the running system.

---

## 5. Evidence taxonomy — the four measured categories

| ID | Category | What it reads |
|---|---|---|
| E1 | Text / Content Cues | wording, phrasing, suspicious phrases (title, description, requirements, benefits) |
| E2 | Identity & Contact Cues | employer identity, off-platform contact pressure (company_profile, location, token counts) |
| E3 | Metadata Completeness | presence flags across 9 structured fields + composite score |
| E4 | Text–Metadata Consistency **(the novelty)** | C1–C6 comparing fields against text |

The external company-presence check is **API-only, qualitative, and explicitly not a fifth
measured category** — excluded from ablation and all quantitative evaluation.

### Consistency rules C1–C6, with current measured status (2026-08-27)

| Rule | Compares | Field cov. (verified) | Evaluable cov. | Status |
|---|---|---|---|---|
| C1 | telecommuting vs description | 100.0% | 10.5% | 🟡 Provisional pattern |
| C2 | location vs description | 88.4% | not measured | ❌ Deferred to Stage 4 |
| C3 | employment_type vs description | 80.6% | 12.2% | 🟡 Provisional pattern |
| C4 | required_experience vs description | 60.6% | 30.2% | 🟡 Provisional pattern |
| C5 | required_education vs description | 54.7% | 27.8% | 🟡 Provisional pattern |
| C6 | salary_range vs description | 15.2% | 7.6% | 🟡 Provisional pattern |

**Aggregate:** 56.7% of postings evaluable by at least one rule; mean 0.88 of 6 rules
evaluable per posting. All "evaluable" figures use placeholder patterns and must be
re-measured once Stage 4 writes the real lexicons. Full detail: `sources.md` #3.

---

## 6. Datasets — two tiers, never merged

| Tier | Dataset | Size | Role | Status |
|---|---|---|---|---|
| 1 | EMSCAD (Vidros et al., 2017) | 17,880 (866 fraud / 4.84%) | ALL training, tuning, calibration, ablation | ✅ Audited, ingestion built and tested |
| 2 | Independently collected contemporary postings | 300–600 target | Held-out temporal validation ONLY | ❌ Not started — biggest schedule risk |

Tier 2 is never used for training; the tiers are never merged. **Open problem (Decision
0.4, unresolved):** if fraudulent Tier 2 postings arrive text-only (scam repositories)
while legitimate ones carry full structured fields (ATS/feed provenance), E3 would
separate the classes for collection-artefact reasons, not fraud reasons — and E4, the
actual contribution, might not fire on the fraud side at all. Must be resolved before
collection starts.

---

## 7. Full methodology — all nine stages plus 8b

| Stage | Activity | Objective | Status | Entry condition |
|---|---|---|---|---|
| — | Data audit | grounds Stage 1 | ✅ Done, corrected twice, verified 2 environments | — |
| 1 | Ingestion & preprocessing | Foundation | ✅ Done, 9/9 tests, verified 2 machines | — |
| 2 | Evidence taxonomy + manual audit (200 postings) | O1 | 🟡 Sampling script + worksheet built and tested; manual coding of 200 postings not yet done | Stage 1 done |
| 3 | Leakage-controlled partitioning (70/15/15) | O2,O3,O5 | ⬜ Blocked | Decision 0.2 |
| 4 | Multi-signal evidence extraction (E1–E4) | O1,O3 | ⬜ Not started | Stages 2+3 done; Decision 0.3 |
| 5 | Model development (baseline + improved) | O2,O3 | ⬜ Not started | Stage 4 done; architecture review + rules-only-baseline decision |
| 6 | Probability calibration + score mapping | O4 | ⬜ Not started | Stage 5 done |
| 7 | Explainability layer + fidelity testing | O4 | ⬜ Not started | Stage 6 done |
| 8 | API build (FastAPI `/score`) | O4 | 🟡 Skeleton built and tested; real wiring pending | Stage 7 for full completion |
| 8b | Demonstration (3 postings, one ambiguous) | O4 | ⬜ Not started | Stage 8 complete |
| 9 | Evaluation, ablation, temporal transfer | O5 | ⬜ Not started | Stages 1–8b done; thresholds agreed with supervisor first |

### Stage-by-stage detail

**Stage 2 — Evidence taxonomy + manual audit.** Stratified 200-posting sample (100
fraud/100 legit), fixed seed, drawn from unique normalised descriptions (avoids
duplicate-campaign inflation of agreement rates). Per posting: which categories are
observable; does each automated rule agree with manual judgement. **Done** = a completed
audit sheet, and at least one signal revised or dropped because the audit contradicted an
assumption.

**Stage 3 — Partitioning.** Group-aware, stratified, 70/15/15. All variants of one posting
on one side. Vectorisers/scalers/encoders fit on train only. **Done** = zero group overlap
proven, duplicate counts reported, seeds fixed, and the "5 seeds = 5 inits on 1 split, or 5
splits?" question (currently open) resolved.

**Stage 4 — Evidence extraction.** E1–E4 built, every feature tagged with its category for
clean leave-one-category-out ablation. Real C1–C6 lexicons written here — replacing every
provisional pattern in the table above, and building genuine location-matching logic for
C2 (deferred, not yet attempted at all). **Done** = every evaluable-coverage figure
re-measured against real lexicons, not assumed to match the provisional numbers.

**Stage 5 — Models.** Baseline: TF-IDF + Logistic Regression / Random Forest. Improved:
DistilBERT text embeddings fused with the E2/E3/E4 structured vector. Pending: rules-only
baseline (does the transformer earn its complexity?) and frozen-vs-fine-tuned DistilBERT
(no GPU available). **Done** = baseline and improved differ only in text representation +
structured features; identical class weighting; hyperparameters/threshold/calibrator
fitted on validation only; test set untouched.

**Stage 6 — Calibration.** Platt or isotonic, chosen on validation. Brier, ECE, reliability
curve reported. Anything that damages calibration is a cost, not a neutral choice.

**Stage 7 — Explainability.** SHAP/LIME + rule-message summaries. Comprehensiveness,
sufficiency (deletion/insertion), rule-consistency — computational only, no human
participants.

**Stage 8 — API.** Skeleton done. Remaining work: replace the four stub functions in
`src/api/main.py` (`preprocess`, `extract_features`, `predict`, `explain`) with real
Stage 1/4/5-6/7 code, one at a time, without touching the route handler.

**Stage 8b — Demonstration.** 3 real postings, one genuinely ambiguous, no cherry-picking.
Proves the artefact works at all — proves nothing about how well. Never conflated with
Stage 9.

**Stage 9 — Evaluation.** Full metric set on the test set, used once. Ablation per
evidence category. Tier 2 temporal transfer (renamed T1/T2/T3 — see `methodology.md`) with
confidence intervals. Thresholds agreed with supervisor **before** results are seen.

---

## 8. The twelve guardrails (build.md §5) — hold these as hard constraints throughout

1. Controlled comparison — baseline/improved differ only in text + structured features.
2. Class weighting is primary; SMOTE is a supplementary baseline-only arm, fitted inside
   training folds only.
3. Leakage control — duplicates never span train/test; vectorisers fit on train only.
4. 70/15/15 split; hyperparameters/threshold/calibrator on validation only; test used once.
5. Calibration mandatory — Brier, ECE, reliability curve.
6. Drop `in_balanced_dataset`.
7. Extract contact/media tokens **before** stripping HTML.
8. Never impute missing structured fields — missingness is the E3 signal.
9. Feature-level ablation, category-tagged, overlaps reported.
10. Thresholds set before seeing test results.
11. Demonstration ≠ evaluation.
12. Explanation faithfulness tested, not assumed — computational only.

---

## 9. Environment

Python 3.13.9, FastAPI, pandas 3.0.5, scikit-learn, PyTorch 2.13.0+cpu, Hugging Face
Transformers, SHAP, LIME, imbalanced-learn. Full pinned list in `requirements.txt`. No paid
data sources, no dedicated GPU, single developer. Git repository:
`credibility-scoring-framework` (private), environment and audit committed and verified in
two independent machines as of 2026-08-27.

---

## 10. Decision log — status as of 2026-08-27

| Decision | Status | Notes |
|---|---|---|
| Class weighting over SMOTE | ✅ Closed | `decisions.md`, 2026-08-07 |
| Two-tier dataset strategy | ✅ Closed | `decisions.md`, 2026-08-07 |
| Tier 2 provenance labelling + source-leakage probe | ✅ Closed | `decisions.md`, 2026-08-07 |
| Drop `in_balanced_dataset` | ✅ Closed | `decisions.md`, 2026-08-07 |
| **0.1** — C1–C6 evaluable-coverage definition | ✅ Closed | 2026-08-27 |
| **0.2** — near-duplicate grouping method | ❌ Open | Blocks Stage 3 |
| **0.3** — label-conditional statistics in design | ❌ Open | Relevant at Stage 4 (C6 viability) |
| **0.4** — Tier 2 field symmetry (can E4 fire on fraud side?) | ❌ Open | Blocks Tier 2 collection |
| Architecture review (rules-only baseline) | ❌ Open | Blocks Stage 5 |
| Frozen vs. fine-tuned DistilBERT | ❌ Open | Blocks Stage 5 |
| "5 seeds" definition | ❌ Open | Blocks Stage 3 |
| `decisions.md` correction (English Teacher Abroad cluster) | ❌ Not yet applied | Cluster is legitimate, not fraudulent, in current text |

---

## 11. Full dependency graph

```
Data audit ✅
    │
Stage 1 ✅ ── Stage 8 skeleton ✅ (inert, wired in later)
    │
Stage 2 (NEXT)
    │
    ├──► [Decision 0.2, "5 seeds"] ──► Stage 3
    │                                     │
    │              [Decision 0.3] ───────►│
    │                                     ▼
    │                                 Stage 4
    │                                     │
    │        [Architecture review, frozen/fine-tune] ──► Stage 5 ──► Stage 6 ──► Stage 7
    │                                                                              │
    │                                                                              ▼
    │                                                                    Stage 8 (full) ──► Stage 8b
    │                                                                              │
[Decision 0.4] ──► Tier 2 collection ═══════════════════════════════════════════► Stage 9 ──► Write-up
```

**Tier 2 should start now, in parallel with Stage 2** — it is the longest-lead task in the
project and joins the critical path only at Stage 9, but collection itself takes far
longer than any single stage above it.

---

## 12. Evaluation plan (Stage 9 detail)

| Objective | Metric(s) | Threshold |
|---|---|---|
| O1 | Per-category observability; per-rule agreement | **[TO SET]** — provisional ≥80%/rule |
| O2 | Precision, Recall, F1, PR-AUC, ROC-AUC | **[TO SET]** |
| O3 | Δ F1, Δ PR-AUC vs. baseline | No directional threshold — objective is to quantify |
| O4 | Comprehensiveness, sufficiency, rule-consistency, Brier, ECE | **[TO SET]** |
| O5 | Full metric set + per-category Δ; Tier 2 transfer | **[TO SET]** |

All thresholds agreed with supervisor before Stage 9 results are seen.

---

## 13. Write-up

Chapters 1, 2, 3, 5 draftable progressively from `decisions.md` and this file. **Chapter 4
(Results) cannot be drafted until Stage 9 produces real measurements.** AI-use declaration
required at write-up — reminder standing per project rules.

---

## 14. What "done" looks like, end to end

- All nine stages + 8b complete, each meeting its own stated definition of done.
- Every open decision in Section 10 closed and logged.
- Tier 2 collected, Decision 0.4's field-symmetry problem resolved one way or the other.
- `/score` runs the full real pipeline on a real request — no stubs remaining in
  `src/api/main.py`.
- Every RQ has a measured answer in Chapter 4, including any that don't confirm what was
  hoped — a rigorous negative or null result is a complete answer, a favourable guess is not.
- Dissertation, research paper, and AI-use declaration submitted.
