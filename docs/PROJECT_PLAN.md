# PROJECT_PLAN.md — Full Project Plan (Start to End)

_Compiled 2026-08-27, refreshed 2026-09-20 (scope-cut decisions, hardware correction,
checklist added). This is a DATED SNAPSHOT for the narrative and the guardrails, but
**Section 7.5 below is a live checklist — update it every time you finish something,
right when you finish it, not at the next big refresh.** `decisions.md`, `methodology.md`,
`sources.md` remain the detailed logs and are authoritative over this file on any specific
number. If a fact here conflicts with one of those three, or with `SKILL.md`'s standing
rules, THEY win — the narrative sections of this file are a convenience summary, never a
primary source. (`workplan.md` was retired 2026-09-20 in favour of this file, so there is
only one planning document now, not two.)_

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

**Deadline confirmed 2026-08-27: ~1 month from that date.** Exact date still to be confirmed
with the programme office, but pacing is now real, not open-ended.

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
| 2 | Independently collected contemporary postings | ~50–100 target (reduced 2026-09-20; 20–30 fraud / 30–50 legit), ~1-week checkpoint | Held-out temporal validation ONLY | 🟡 Legitimate-side sourcing verified and ready (Greenhouse/Lever/Arbeitnow/Adzuna, all confirmed free and accessible 2026-09-20); fraud-side sourcing not yet verified; zero postings collected |

Tier 2 is never used for training; the tiers are never merged. **Open problem (Decision
0.4, still unresolved):** if fraudulent Tier 2 postings arrive text-only (scam repositories)
while legitimate ones carry full structured fields (ATS/feed provenance), E3 would
separate the classes for collection-artefact reasons, not fraud reasons — and E4, the
actual contribution, might not fire on the fraud side at all. Must be resolved before
collection starts — this is exactly why fraud-side sourcing needs checking next, not just
legitimate-side.

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
DistilBERT (**fine-tuned**, decided 2026-09-20 — hardware is an RTX 3050 + 16GB RAM, not
"no GPU" as previously assumed) fused with the E2/E3/E4 structured vector. Rules-only
baseline **cut** (2026-09-20). Divergent architecture review **formally skipped**,
time-driven (2026-09-20) — committing to the original design as-is. 3 seeds (reduced from
5), one fixed split. **Done** = baseline and improved differ only in text representation +
structured features; identical class weighting; hyperparameters/threshold/calibrator
fitted on validation only; test set untouched.

**Stage 6 — Calibration.** Platt or isotonic, chosen on validation. Brier, ECE, reliability
curve reported. Anything that damages calibration is a cost, not a neutral choice.

**Stage 7 — Explainability.** SHAP only (LIME dropped, 2026-09-20) + rule-message
summaries. Comprehensiveness, sufficiency (deletion/insertion), rule-consistency —
computational only, no human participants.

**Stage 8 — API.** Skeleton done. Remaining work: replace the four stub functions in
`src/api/main.py` (`preprocess`, `extract_features`, `predict`, `explain`) with real
Stage 1/4/5-6/7 code, one at a time, without touching the route handler.

**Stage 8b — Demonstration.** 3 real postings, one genuinely ambiguous, no cherry-picking.
Proves the artefact works at all — proves nothing about how well. Never conflated with
Stage 9.

**Stage 9 — Evaluation.** Full metric set on the test set, used once. Ablation per
evidence category (no rules-only arm — cut). Tier 2 temporal transfer (T1/T2/T3 — see
`methodology.md`) at reduced scale (~50–100 postings), reported with wide confidence
intervals given the small sample. Thresholds agreed with supervisor **before** results are
seen — urgent given the deadline.

---

## 7.5 — LIVE CHECKLIST (update this every time you finish something)

> **How to use this section.** Tick a box the moment you finish that item — not at the next
> big review. This is the one part of this file that changes constantly; everything else
> above and below it is refreshed only at real milestones. Copy this whole file, replace it
> in both the Claude Project and the repo, same as always, whenever you tick something —
> or keep a local working copy and sync it every few items, your call, as long as it
> eventually lands in both places.

### Pre-work

- [x] Repository, environment, `.gitignore` set up and verified
- [x] Data audit run and corrected (3 bugs fixed: missingness, duplicate-count, C1–C6 definition)
- [x] Dataset strategy stress-tested against 4 external alternatives — rejected, two-tier plan reaffirmed
- [x] Hardware capability corrected (RTX 3050 + 16GB RAM, not "no GPU")
- [x] Scope-cut decisions made (rules-only cut, DistilBERT fine-tuned, Tier 2 reduced, 3 seeds, SHAP-only, architecture review skipped)
- [x] Decision 0.2 resolved (MD5 + title grouping)
- [x] Tier 2 legitimate-source APIs verified (Greenhouse, Lever, USAJOBS, Arbeitnow, Adzuna)
- [ ] Tier 2 fraud-source access verified
- [ ] Decision 0.3 resolved (label-conditional statistics in design)
- [ ] Tier 2 ethics approval status checked
- [ ] Success thresholds agreed with supervisor

### Stage 1 — Ingestion & preprocessing

- [x] Boolean encoding (t/f → 1/0) with fraud-count assertion
- [x] Contact/media token extraction before HTML stripping
- [x] `in_balanced_dataset` dropped
- [x] `salary_range` "0-0" treated as missing
- [x] Missingness flagged, never imputed
- [x] Tests written and passing (9/9), verified on 2 machines
- [x] Committed to repository

### Stage 2 — Evidence taxonomy + manual audit

- [x] Stratified 200-posting sample built (seed 42, unique normalised descriptions)
- [x] Worksheet generated (28 columns, mechanical fields pre-filled, judgement fields blank)
- [x] Coding scheme written in advance (`STAGE2_CODING_INSTRUCTIONS.md`)
- [x] Reproducibility verified on real machine
- [x] Committed to repository
- [ ] **Manual coding of 200 postings — not started (yours to do)**
- [ ] Per-category observability rate computed
- [ ] Per-rule agreement rate computed
- [ ] At least one signal revised/dropped based on audit findings, logged
- [ ] Results written into `methodology.md`

### Stage 3 — Leakage-controlled partitioning

- [ ] Title-based grouping key added alongside existing description MD5 hashing
- [ ] Group-aware stratified 70/15/15 split implemented
- [ ] Zero group overlap proven across train/validation/test
- [ ] Duplicate counts reported using the resolved grouping method
- [ ] Vectorisers/scalers/encoders fit on train only
- [ ] Seeds fixed and recorded (3, one fixed split)
- [ ] Results written into `methodology.md`

### Stage 4 — Multi-signal evidence extraction

- [ ] E1 features built (text/content cues)
- [ ] E2 features built (identity & contact cues)
- [ ] E3 features built (completeness flags + composite)
- [ ] E4 / C1–C6 real lexicons written (replacing every provisional pattern)
- [ ] C2 real location-matching logic built (first real attempt — not a backfilled proxy)
- [ ] Every feature tagged with its category for clean ablation
- [ ] All C1–C6 evaluable-coverage figures re-measured against real lexicons
- [ ] Decision 0.3 applied consistently once resolved

### Stage 5 — Model development

- [ ] TF-IDF + Logistic Regression baseline trained
- [ ] TF-IDF + Random Forest baseline trained
- [ ] DistilBERT fine-tuned on GPU, fused with E2/E3/E4 vector
- [ ] Identical class weighting confirmed on both baseline and improved model
- [ ] Hyperparameters/threshold fitted on validation only
- [ ] 3-seed repetition completed, mean ± SD reported
- [ ] Test set touched exactly once

### Stage 6 — Calibration

- [ ] Platt scaling tried
- [ ] Isotonic regression tried
- [ ] Calibrator selected on validation performance
- [ ] Brier score reported (before/after)
- [ ] ECE reported (before/after)
- [ ] Reliability curve produced
- [ ] Risk-band thresholds set

### Stage 7 — Explainability

- [ ] SHAP integrated over the fused feature set
- [ ] Rule-message summaries generated from C1–C6 flags
- [ ] Comprehensiveness (deletion test) measured
- [ ] Sufficiency (insertion test) measured
- [ ] Rule-consistency check run
- [ ] Random-attribution control compared against

### Stage 8 — API (real pipeline wiring)

- [x] FastAPI app, `/score` route, JSON schema built and tested (skeleton)
- [ ] `preprocess()` wired to real Stage 1 code
- [ ] `extract_features()` wired to real Stage 4 code
- [ ] `predict()` wired to real Stage 5/6 code
- [ ] `explain()` wired to real Stage 7 code
- [ ] End-to-end real request tested (no stubs remaining)

### Stage 8b — Demonstration

- [ ] Clear fraud example run and captured
- [ ] Clear legitimate example run and captured
- [ ] Genuinely ambiguous example run and captured (no cherry-picking)
- [ ] Results written into `methodology.md` — kept separate from Stage 9

### Stage 9 — Evaluation

- [ ] Full metric set computed on test set (used once)
- [ ] Leave-one-category-out ablation run (E1, E2, E3, E4, `has_company_logo`)
- [ ] Tier 2 temporal transfer (T1) run, if Tier 2 collection succeeded
- [ ] Tier 2 signal durability (T2) run, if Tier 2 collection succeeded
- [ ] Tier 2 domain adaptation (T3) run, if Tier 2 collection succeeded
- [ ] Source-probe leakage test run and reported regardless of outcome
- [ ] Results written into `methodology.md`

### Tier 2 collection (parallel track)

- [ ] Company slug list built for Greenhouse/Lever querying
- [ ] Legitimate postings collected (target 30–50)
- [ ] Fraud-source access verified
- [ ] Fraudulent postings collected (target 20–30)
- [ ] 1-week checkpoint evaluated — reduced collection continues, or qualitative-only fallback invoked
- [ ] Provenance recorded for every collected posting

### Write-up

- [x] Chapter 1 drafted
- [x] Chapter 2 drafted
- [x] Chapter 3 drafted
- [ ] Chapter 4 (Results) — cannot start until Stage 9 produces real measurements
- [ ] Chapter 5 drafted
- [ ] Chapter 6 drafted
- [ ] AI-use declaration written
- [ ] Research paper drafted

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
Transformers, SHAP (LIME removed from planned use, 2026-09-20), imbalanced-learn. Full
pinned list in `requirements.txt`. No paid data sources, single developer. **Hardware
corrected 2026-09-20:** RTX 3050 GPU + 16GB RAM (gaming laptop) — previously wrongly
recorded as "no dedicated GPU" throughout the project files since proposal stage; this
enables fine-tuning DistilBERT rather than using frozen embeddings. Git repository:
`credibility-scoring-framework` (private), environment and audit committed and verified in
two independent machines as of 2026-08-27.

---

## 10. Decision log — status as of 2026-09-20

| Decision | Status | Notes |
|---|---|---|
| Class weighting over SMOTE | ✅ Closed | `decisions.md`, 2026-08-07 |
| Two-tier dataset strategy | ✅ Closed, reaffirmed | `decisions.md`, 2026-08-07; stress-tested against 4 external alternatives 2026-08-27 |
| Tier 2 provenance labelling + source-leakage probe | ✅ Closed | `decisions.md`, 2026-08-07 |
| Drop `in_balanced_dataset` | ✅ Closed | `decisions.md`, 2026-08-07 |
| `decisions.md` correction (English Teacher Abroad cluster) | ✅ Applied | Corrected as an appended note, 2026-08-27; independently corroborated 2026-08-27 |
| **0.1** — C1–C6 evaluable-coverage definition | ✅ Closed | 2026-08-27 |
| **0.2** — near-duplicate grouping method | ✅ Closed | 2026-09-20 — MD5 + title-based secondary grouping key |
| **0.3** — label-conditional statistics in design | ❌ Open | Relevant at Stage 4 (C6 viability) — the one genuinely unresolved design question left |
| **0.4** — Tier 2 field symmetry (can E4 fire on fraud side?) | ❌ Open | Blocks full Tier 2 collection; legitimate-side sourcing verified regardless |
| Hardware constraint correction | ✅ Applied | 2026-09-20 — RTX 3050 + 16GB RAM, not "no GPU" |
| Rules-only baseline | ✅ Closed — CUT | 2026-09-20 |
| Frozen vs. fine-tuned DistilBERT | ✅ Closed — fine-tuned | 2026-09-20, enabled by hardware correction |
| Divergent architecture review | ✅ Closed — skipped, time-driven | 2026-09-20 |
| "5 seeds" definition + count | ✅ Closed — 3 seeds, fixed split | 2026-09-20 |
| Explainability method scope | ✅ Closed — SHAP only | 2026-09-20 |
| Tier 2 collection depth | ✅ Closed — reduced, ~50–100, 1-week checkpoint | 2026-09-20 |
| Tier 2 legitimate-source API access | ✅ Verified | 2026-09-20 — Greenhouse, Lever, USAJOBS, Arbeitnow, Adzuna confirmed; Indeed retirement reconfirmed |
| Tier 2 fraud-source access | ❌ Not yet checked | Next verification task |
| Success thresholds per objective | ❌ Open | Must be agreed with supervisor before Stage 9 — urgent |
| Tier 2 ethics approval status | ❌ Open | Check today |

---

## 11. Full dependency graph (updated 2026-09-20 — most blockers now cleared)

```
Data audit ✅
    │
Stage 1 ✅ ── Stage 8 skeleton ✅ (inert, wired in later)
    │
Stage 2 — sampling ✅, manual audit ⬜ (NEXT, yours)
    │
    ▼
Stage 3 (all blockers resolved — MD5+title grouping, 3-seed fixed split)
    │
    │   [Decision 0.3 — the one still-open design question] ──► (feeds into Stage 4)
    ▼
Stage 4
    │
    ▼
Stage 5 (all blockers resolved — fine-tuned DistilBERT, no rules-only arm,
         architecture review skipped by decision) ──► Stage 6 ──► Stage 7 (SHAP only)
                                                                        │
                                                                        ▼
                                                              Stage 8 (full) ──► Stage 8b
                                                                        │
Tier 2 [legit sourcing ✅ verified; fraud sourcing ⬜ next;             │
        Decision 0.4 still open] ═══════════════════════════════════► Stage 9 ──► Write-up
```

**Tier 2 sourcing should be running now, in parallel with Stage 2's manual audit** — it is
still the longest-lead task in the project, now scoped down and time-boxed with a 1-week
checkpoint, and joins the critical path only at Stage 9.

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
