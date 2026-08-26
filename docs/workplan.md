# workplan.md — End-to-end development plan

_Drafted 2026-08-26. Ordered by DEPENDENCY, not calendar — no durations can be assigned
until `project.md` line 19 (Key deadlines) is filled in._

**How to read this.** Every phase has an ENTRY condition (what must be true before starting),
a BUILD (what you produce), a DONE test (how you know it's finished — not "it runs"), and a
GATE (the decision that must be logged in `decisions.md` before moving on). If a DONE test
can't be answered with a measured number or a written artefact, the phase is not done.

**The rule that makes this plan work:** never start a phase whose ENTRY condition is unmet.
Every guardrail violation in this kind of project comes from skipping an entry condition.

---

## PHASE 0 — Close the open loop (no code)

You are currently blocked on decisions, not on code. Four of them.

| # | Decision | Why it blocks |
|---|---|---|
| 0.1 | One definition of "evaluable" for C1–C6, applied to all six | The measured coverage table is unusable until this is fixed (C3 swings 80.6% → 12.2% depending on definition) |
| 0.2 | Near-duplicate grouping method, threshold declared in advance | Gates Stage 3 entirely |
| 0.3 | Whether label-conditional statistics may influence design | Gates whether C6 can be assessed for viability |
| 0.4 | Whether Tier 2 tests the full model or only its text component | Gates the entire Tier 2 collection strategy — see Parallel Track |

**Also in Phase 0:**
- Fill in `project.md` line 19 — key deadlines. Nothing can be scheduled without it.
- Correct the `decisions.md` error: the "English Teacher Abroad" cluster is **legitimate**
  (715 records, 0 fraudulent), not a fraudulent campaign. The decision survives; the example
  does not.
- Paste the measured audit figures into `methodology.md` → Data audit.
- Mark `sources.md` #4, #5, #7, #9 verified. Leave **#3 open** until 0.1 is resolved.
- Ask for an ADVERSARIAL pass on the Tier 2 plan.

**DONE:** all four decisions logged with options, reasoning, cost, revisit trigger, self-check.

---

## PHASE A — Foundation (Stages 1–3)

### Stage 1 — Ingestion & preprocessing
- **ENTRY:** Phase 0 complete.
- **BUILD:** Loader producing a clean dataframe. Map `t`/`f` → 1/0. Drop
  `in_balanced_dataset` (G6). Extract `#EMAIL_#`/`#PHONE_#`/`#URL_#` counts and link/image
  counts **before** stripping HTML (G7). Never impute — record missingness as flags (G8).
  Treat `salary_range == "0-0"` as missing.
- **DONE:** Reload reproduces the audit's measured numbers exactly (17,880 rows; 866 fraud;
  token counts 7,362 / 1,377 / 657 postings). If they don't match, the loader is wrong.
- **GATE:** none — this is settled.

### Stage 2 — Evidence taxonomy + manual audit (O1, RQ1)
- **ENTRY:** Stage 1 done.
- **BUILD:** Written definition of each category and each signal. Manual audit of a
  **stratified 200-posting sample** — does each signal actually appear, and does it mean what
  you claim?
- **DONE:** A completed audit sheet with per-signal presence rates, and at least one signal
  you *dropped or revised* because the audit contradicted you. An audit that changes nothing
  wasn't an audit.
- **RISK:** This is the stage students skip. It is the entire evidence for O1.

### Stage 3 — Leakage-controlled partitioning (G3, G4)
- **ENTRY:** Decision 0.2 logged.
- **BUILD:** Normalise → group → group-aware stratified split 70/15/15. All variants of one
  posting on one side. Fit nothing on test.
- **DONE:** Written proof of zero group overlap across boundaries; reported duplicate counts;
  per-split class counts; seeds fixed and recorded. Plus a written answer to: *does "5 seeds"
  mean 5 model initialisations on one fixed split, or 5 splits?* (One fixed split is the
  defensible reading given G4.)
- **GATE:** the seed question, logged.

---

## PARALLEL TRACK — Tier 2 collection (start at Phase A, not later)

This is your **longest-lead, highest-risk task** — your own files say so twice. It cannot be
serialised after Stage 9 or it will not exist.

- **ENTRY:** Decision 0.4 logged, plus an ADVERSARIAL pass.
- **BUILD:** 300–600 contemporary postings. Legitimate by provenance (ATS endpoints, official
  feeds); fraudulent from documented scam repositories where original text is reproduced.
- **THE UNSOLVED PROBLEM:** if fraudulent Tier 2 postings arrive as text-only while legitimate
  ones arrive with structured fields, then (a) E3 separates the classes for collection
  reasons, not fraud reasons, and (b) **E4 cannot fire on the fraud side at all**, so Tier 2
  cannot test your novelty. Solve this before collecting, not after.
- **DONE:** collected set + provenance log + source-leakage probe result + written statement
  of what Tier 2 can and cannot test.
- **FALLBACK (already logged):** report Tier 2 qualitatively and state the limitation openly.

---

## PHASE B — Signals (Stage 4) → O1, O3, RQ1

- **ENTRY:** Stages 2 and 3 done.
- **BUILD:** E1 (text/content cues), E2 (identity & contact), E3 (completeness flags +
  composite), E4 (C1–C6 flags + plain-language messages). **Every feature tagged with its
  category** so leave-one-category-out ablation is clean later (G9). Lexicons frozen before
  any Tier 2 scoring.
- **DONE:** measured firing rate AND coverage for each of C1–C6; documented overlaps
  (`location` → E2+E4; `salary_range` → E3+E4); feature-category map committed.
- **WATCH:** C6 may prove too thin to carry weight (7.6% evaluable, measured). Reporting it as
  a coverage limitation is a legitimate finding — decide before Stage 9, not after.

---

## PHASE C — Models & calibration (Stages 5–6) → O2, O3, O4, RQ2, RQ3

- **ENTRY:** Phase B done. **Plus two decisions still open in your files:**
  - the DIVERGENT architecture review (`project.md` next-action #2 — "before any model code")
  - the **rules-only baseline** question: does the transformer earn its complexity?
- **BUILD:** Baseline (TF-IDF + LogReg/RF). Improved (DistilBERT embeddings fused with
  E2/E3/E4 vector). Then calibration (Platt vs isotonic, chosen on validation).
- **DONE:** baseline and improved differ **only** in text representation + structured
  features. Class weighting identical in both (G1, G2). Hyperparameters, threshold and
  calibrator fitted on validation only (G4). Brier, ECE and reliability curve reported (G5).
  Results as mean ± SD across 5 seeds. **Test set untouched.**
- **GATE:** both entry decisions logged before any model code is written.

---

## PHASE D — Explanation & artefact (Stages 7, 8, 8b) → O4, RQ4

### Stage 7 — Explainability + fidelity
- **BUILD:** SHAP/LIME over the fused features + rule-message summaries.
- **DONE:** measured comprehensiveness, sufficiency (deletion/insertion), and
  rule-consistency. Computational only — no human participants (G12).

### Stage 8 — API
- **BUILD:** FastAPI `/score`. Raw text is the supported path; URL is best-effort secondary.
  Returns the full JSON contract.
- **DONE:** end-to-end run on an unseen posting returning a calibrated 0–100 score with
  reasons, contradictions and checklist.

### Stage 8b — Demonstration
- **DONE:** three real postings including one **genuinely ambiguous** case. This shows it
  works at all. It is **not** evaluation (G11) and no number from it may be reported as a
  result.

---

## PHASE E — Evaluation (Stage 9) → O5, RQ5

- **ENTRY:** success thresholds agreed **with your supervisor, in writing, before you look at
  test results** (G10). A threshold set afterwards is not a threshold.
- **BUILD:** full metric set on the held-out test set — used **once**. Leave-one-category-out
  ablation across E1–E4 (the external company-presence check is excluded). Temporal transfer
  on Tier 2 with confidence intervals.
- **DONE:** every RQ has a measured answer, including answers you didn't want.

---

## PHASE F — Write-up

- Chapters 1–3 and 5 can be drafted from your files during earlier phases.
- **Chapter 4 (Results) cannot be drafted until Phase E produces real measurements.**
- Prepare the **AI-use declaration** your programme requires.
- Final check: can you explain every choice, unaided, in your own words? If not, that part
  isn't finished.

---

## Dependency summary

```
PHASE 0  ──►  A(1,2,3)  ──►  B(4)  ──►  C(5,6)  ──►  D(7,8,8b)  ──►  E(9)  ──►  F
              │                                                        ▲
              └────────  PARALLEL: Tier 2 collection  ─────────────────┘
```

Tier 2 starts early and finishes late. Everything else is strictly serial.
