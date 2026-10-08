# methodology.md — How I'm Doing This (and the Evaluation Plan)

_Last updated: 2026-10-08_

> Companion to `Research_Methodology_Final.docx` (the formal, supervisor-facing version).
> This file is the **working** version: it tracks what I am *actually* doing, records results
> as they arrive, and accumulates into my methodology chapter. Where the two disagree, this
> file is the truth and the .docx needs updating.

---

## Approach in one paragraph

This research follows a Design Science Research approach (Hevner et al., 2004; Peffers et
al., 2007): I design, build and evaluate a purposeful artefact — an explainable credibility
scoring API for online recruitment posts — and the act of designing, demonstrating and
evaluating it produces the knowledge contribution. Evaluation strategy is positioned using
the FEDS framework (Venable, Pries-Heje & Baskerville) as **ex post** (the built system is
evaluated, not the design in advance) and predominantly **artificial** (benchmark dataset
under controlled conditions), with a **naturalistic** component in the Tier 2 assessment on
independently collected contemporary postings.

> ⚠️ Full references for Hevner et al., Peffers et al., and Venable/Pries-Heje/Baskerville
> are not yet confirmed — see `sources.md` #1, #2, #8. Do not cite these from memory in any
> submitted document.

> ⚠️ **Deadline confirmed 2026-08-27: ~1 month away.** Scope-cut decisions were made
> 2026-09-20 — see `decisions.md`. This file now reflects the resolved scope: 3 seeds
> (not 5), SHAP only (not SHAP+LIME), no rules-only baseline, Tier 2 reduced to ~50–100
> postings. Hardware was also corrected 2026-09-20: RTX 3050 + 16GB RAM, not "no GPU" —
> DistilBERT will be fine-tuned, not frozen.

---

## How each DSR step is being carried out

### Step 1 — Problem identification

Established during the proposal stage through literature review of ten studies (2017–2026).
Four gaps identified: limited user-facing explainability; underuse of structured multi-signal
evidence; absence of explicit text–metadata consistency verification; and binary output that
provides weak practical decision support. Problem statement is maintained in `project.md`.

### Step 2 — Define solution objectives

Five objectives, finalised 2026-08-07, each mapped to exactly one research question and one
deliverable. Full statements in `Research_Objectives_and_Questions_Final.docx`. Constraint
held throughout: no objective states its expected result (see `decisions.md`, 2026-08-07).

### Step 3 — Design and development

Nine implementation stages (below). Design decisions and their rationale are recorded in
`decisions.md`, which is the primary evidence for this step.

**Status, 2026-10-08:** data audit complete and corrected twice; Stage 1 complete and
tested; **Stage 2 complete — 200/200 posting manual audit coded by hand (commit
`57da423`), results below**; **Stage 3 complete — group-aware 70/15/15 split run and
verified (commit `9a5379b`), results below**; **Stage 4 complete — E1–E4 extraction built
and run on the full corpus (n=17,880), 33/33 new tests passing, results below**; Stage 8
skeleton (API routing/schema, no real pipeline yet) complete and tested. Stages 5–7, 9 not
started.

### Step 4 — Demonstration

Before formal evaluation, the API will be demonstrated end-to-end on a small set of real
postings to establish proof of life. The demonstration set will deliberately include:

- at least one clearly fraudulent posting,
- at least one clearly legitimate posting,
- **at least one genuinely ambiguous posting** — no cherry-picking the easy cases.

For each, the full JSON response is captured (`credibility_score`, `risk_band`,
`top_reasons`, `suspicious_phrases`, `contradictions`, `verification_checklist`) along with
the input.

**Demonstration proves the artefact works at all. It proves nothing about how well.**
That is Step 5's job, and the two are reported separately. This is Stage 8b in the
implementation table below.

### Step 5 — Evaluation

Full plan below. Designed to be hard to pass, not easy.

### Step 6 — Communication

Dissertation plus research paper. Drafted from `decisions.md` and this file rather than
from scratch. Chapters 1–3 already drafted in `Research_Thesis_Draft.md`. AI-use
declaration to be included — see `project.md` open questions.

---

## Implementation stages

| Stage | Activity | Objective | Status (2026-08-27) |
|---|---|---|---|
| — | Data audit | grounds Stage 1 | ✅ Complete, corrected twice, verified in 2 environments |
| 1 | Data ingestion & preprocessing | Foundation | ✅ Complete, 9/9 tests passing, verified twice |
| 2 | Evidence taxonomy definition & manual audit | O1 | ✅ Complete, 2026-10-08 — 200/200 postings coded by hand; see Taxonomy validation (O1) below |
| 3 | Leakage-controlled data partitioning | O2, O3, O5 | ✅ Complete, 2026-10-08 — group-aware 70/15/15 split, 9/9 tests passing, zero group overlap; see Partition summary below |
| 4 | Multi-signal evidence extraction | O1, O3 | ✅ Complete, 2026-10-08 — E1-E4 built and run on full corpus; 4 precision bugs found & fixed; see Stage 4 extraction results below |
| 5 | Model development (baseline & improved) | O2, O3 | ⬜ Not started — all blocking decisions resolved 2026-09-20 (fine-tuned DistilBERT, no rules-only arm, architecture review skipped by decision) |
| 6 | Probability calibration & score mapping | O4 | ⬜ Not started |
| 7 | Explainability layer & fidelity evaluation | O4 | ⬜ Not started — scope: SHAP only, LIME dropped, decided 2026-09-20 |
| 8 | API development | O4 | 🟡 Skeleton complete and tested (routing, schema validation, zero fabricated data); real pipeline wiring pending Stages 4–7 |
| **8b** | **Demonstration** | O4 | ⬜ Not started |
| 9 | Evaluation, ablation & generalisability | O5 | ⬜ Not started |

### Stage 1 critical ordering constraints

1. Map `t`/`f` string literals to integers **on load**; assert fraud count = 866 before
   proceeding. _(Encoding claim VERIFIED — see `sources.md` #4. Confirmed: all five boolean
   columns are `t`/`f`, zero nulls, fraud count exactly 866.)_
2. Drop `in_balanced_dataset`. _(Confirmed present in the real CSV — dropped in the Stage 1
   loader.)_
3. **Extract `#EMAIL_#` / `#PHONE_#` / `#URL_#` tokens, image refs and link counts BEFORE
   stripping HTML.** Reversing this destroys the whole E2 feature group. _(All three token
   types confirmed present — see Results below. Implemented correctly in Stage 1.)_
4. Treat `salary_range` value `"0-0"` as missing. _(Confirmed: 142 records carry this
   placeholder. Implemented in Stage 1.)_
5. Flag missingness per field; never impute. _(Implemented in Stage 1 — a dtype-handling bug
   in the missingness check was found and fixed during testing.)_

---

## Evidence taxonomy (O1)

| ID | Category | Signals |
|---|---|---|
| E1 | Text / Content Cues | TF-IDF weights (baseline); contextual embeddings (improved); suspicious-phrase lexicon matches |
| E2 | Identity & Contact Cues | company_profile presence/length; location specificity; contact/email/URL token counts |
| E3 | Metadata Completeness | presence flags across 9 structured fields + composite score |
| E4 | Text–Metadata Consistency | rules C1–C6 + aggregate contradiction count |

### Consistency rule set (C1–C6) — the novelty

> ⚠️ **Definitional note (2026-08-27):** "evaluable coverage" means both operands the rule
> compares are present, so the rule could actually attempt a comparison — not merely that
> some text exists nearby. An earlier version of this audit applied that standard
> inconsistently (strict for C4–C6, loose for C1–C3), which understated the gap between
> field coverage and real coverage. All six rules now use one consistent standard. See
> `sources.md` #3 and `decisions.md` (Decision 0.1, 2026-08-27) for full detail.

| ID | Rule | Trigger | Field coverage (measured) | Evaluable coverage (measured) | Status |
|---|---|---|---|---|---|
| C1 | Remote / on-site | `telecommuting` conflicts with remote/on-site language in description | **100.0%** | **0.50%** | ✅ Final, Stage 4 — real lexicon |
| C2 | Location mismatch | location field absent from text while a different location is named | **98.1%** | **6.92%** | ✅ Final, Stage 4 — first real location matcher (cue-phrase gated) |
| C3 | Employment type | `employment_type` conflicts with working-arrangement language | **80.6%** | **15.17%** | ✅ Final, Stage 4 — real lexicon |
| C4 | Experience level | `required_experience` conflicts with "N+ years" extracted from text | **60.6%** | **20.56%** | ✅ Final, Stage 4 — real lexicon |
| C5 | Education | `required_education` conflicts with qualification statements | **54.7%** | **15.32%** | ✅ Final, Stage 4 — real lexicon |
| C6 | Salary | description figures fall outside parsed `salary_range` | **15.25%** | **1.22%** | ✅ Final, Stage 4 — real lexicon; see unit-ambiguity note below |

**Aggregate (measured, full corpus n=17,880, 2026-10-08, final Stage 4 lexicons):**
postings evaluable by at least one rule: **7,625 (42.65%)**. Mean rules evaluable per
posting: **0.597 of 6**. Contradiction rate per evaluable rule: C1 50.00%; C2 9.61%; C3
10.84%; C4 2.20%; C5 4.93%; C6 23.74%. Postings with at least one contradiction: **709
(3.97%)**. Full breakdown in `reports/stage4_coverage_report.json`.

**Why evaluable coverage dropped sharply from the provisional estimates above** (e.g. C1
10.5% → 0.50%, C3 12.2% → 15.17% is close but C4/C5 roughly halved): the provisional
patterns from the August audit counted a rule as "evaluable" far more loosely than the
real Stage 4 lexicons do. The real lexicons require an unambiguous signal, not merely a
topic mention — e.g. C1 now requires a genuine remote/on-site position claim, not any
mention of "work from home" (see the precision-bug note below). Lower evaluable coverage
with a stricter, more defensible definition of "evaluable" is the expected and intended
outcome of replacing placeholder patterns with real ones, not a regression.

**C2, Stage 4 (2026-10-08) — no longer deferred:** the real location matcher only
counts a place name found via an explicit cue phrase ("based in X", "relocate to X",
"location: X", ...) against a modest hardcoded gazetteer (~75 major cities, ~55 ISO
country names, US states) — never a blind scan of the whole posting, which would
false-positive constantly (a company_profile naming other offices or eligibility
clauses — "Canada/US passport holders only" — is not a claim about where *this* job is).
This is a genuine but partial implementation: the gazetteer is not exhaustive, so a real
place-name mismatch written with a city or country outside the lexicon is silently
under-counted as "not evaluable" rather than wrongly flagged — the limitation is biased
toward under-claiming, not over-claiming, which is the safer direction for a coverage
figure reported as a finding.

**C1, C3–C6, Stage 4 (2026-10-08) — real lexicons, final.** The provisional
placeholder patterns from the August audit have been fully replaced; see "Stage 4 multi-signal
evidence extraction" below for the design approach, the four precision bugs found during
full-corpus validation and fixed before any figure above was reported, and the
methodological safeguard taken against tuning these lexicons to the Stage 2 audit sample.

**What this means for E4 as a whole:** the original field-coverage estimates (used since
2026-08-07) implied E4 was observable on nearly every posting. The final, measured picture
(full corpus, real lexicons) is that well under half the corpus (42.65%) can be evaluated
by even one rule, and on average under one rule per posting (0.597 of 6) can fire at all —
lower than even the provisional August estimate (56.7% / 0.88 of 6), because the real
lexicons require an unambiguous signal rather than a loose topic mention. This is a real
and significant finding about the practical reach of the consistency-verification
contribution — not a data-quality failure, but something the dissertation must state
plainly and account for, rather than let either the original optimistic estimate or the
provisional August figure stand as final.

### Taxonomy validation (O1)

Manual audit of 200 stratified EMSCAD postings (100 fraudulent / 100 legitimate), fixed
seed (42), drawn from **unique normalised descriptions only** — added 2026-08-27, to avoid
near-duplicate campaigns inflating the apparent agreement rate. Records per posting: which
categories are observable; whether each automated rule agrees with manual judgement.

**Sampling script status:** built and tested (`sample_for_manual_audit.py`), reproducibility
confirmed (identical output across repeated runs and across two separate environments).

**Manual coding status: complete, 2026-10-08.** All 200 postings coded by hand, single
coder (the student), blind to the ground-truth fraud label by default (per
`STAGE2_CODING_INSTRUCTIONS.md`). Worksheet committed at `57da423`. A data-integrity issue
in the worksheet was found and corrected twice during this process without altering any
manual judgement already entered — see `decisions.md`, 2026-10-07 and 2026-10-08, and
"What the audit made me revise" below.

**Observability rates (E1–E4), measured on the 200-posting sample:**

| Category | Y — observable | PARTIAL | N — not observable |
|---|---|---|---|
| E1 Text / content cues | 89.0% (178/200) | 10.0% (20/200) | 1.0% (2/200) |
| E2 Identity & contact cues | 74.0% (148/200) | 23.0% (46/200) | 3.0% (6/200) |
| E3 Metadata completeness | 49.0% (98/200) | 30.5% (61/200) | 20.5% (41/200) |
| E4 Text–metadata consistency | 54.5% (109/200) | 26.5% (53/200) | 19.0% (38/200) |

**Field coverage and agreement rate (C1–C6), measured on the 200-posting sample:**

Agreement rate = the student's `_manual_contradiction_MANUAL` judgement vs. the pre-filled
`_pattern_evaluable_REFERENCE_ONLY` placeholder-pattern flag, computed only among rows where
the field is present **and** the manual answer is Y or N (NA excluded — the automated flag
has no NA category to match against). Per `STAGE2_CODING_INSTRUCTIONS.md`, this is **a
preview of Stage 4, not the final rule-consistency check**: the pattern flags are still
placeholder regexes written for audit purposes, not the frozen Stage 4 lexicons.

| Rule | Field coverage (this sample) | Agreement rate (MANUAL vs. placeholder pattern) | Disagreements |
|---|---|---|---|
| C1 Remote / on-site | 100.0% (200/200) | 86.9% (173/199) | 26 |
| C2 Location | 84.5% (169/200) | not measured — no automated baseline (deferred to Stage 4) | — |
| C3 Employment type | 79.5% (159/200) | 82.9% (131/158) | 27 |
| C4 Experience level | 57.0% (114/200) | 65.2% (73/112) | 39 |
| C5 Education | 54.0% (108/200) | 54.5% (55/101) | 46 |
| C6 Salary | 26.5% (53/200) | 73.6% (39/53) | 14 |

Every disagreement is logged verbatim (sample ID, manual answer, pattern flag, the
student's own `notes_MANUAL` text) in `reports/stage2_disagreements_for_review.txt` — raw
material for the "catalogue of disagreements and causes" write-up; the causal analysis
itself is the student's own interpretive work and is not generated here.

This sample's field-coverage figures sit close to, but are not identical to, the
full-corpus (n=17,880) figures in the Consistency rule set table above — e.g. C6 is 26.5%
in this 200-posting sample vs. 15.2% across the full corpus. That gap is expected sampling
variance from drawing 200 postings, not a contradiction between the two measurements; the
full-corpus figures remain the authoritative ones for any claim about EMSCAD as a whole, and
the 200-sample figures are specific to what the human coder could evaluate.

**What the audit made me revise (per `STAGE2_CODING_INSTRUCTIONS.md`'s requirement to name
at least one such thing):** the sampling/pre-fill script's field-presence logic had a real
NaN-handling bug — a blank cell's `str(NaN)` is the non-empty string `"nan"`, which passed a
`!= ""` presence check — that wrongly marked C3/C4/C5 as present on fields that were
genuinely blank. This was caught **twice**: once while coding S001, before the fix was
applied worksheet-wide (2026-10-07); and a second time, after all 200 postings were coded,
when the worksheet file itself was found to have partially reverted to the pre-fix state
between two git commits, for a reason not yet confirmed (see `decisions.md`, 2026-10-08).
Both times the fix was a non-destructive recomputation of only the `field_present` flags
against the raw CSV, resetting to `NA` only the handful of `_MANUAL` answers that had
actually been given in response to a question that should never have been asked (10 of 200
postings, in the second incident) — never a wholesale regeneration of the worksheet, and
never a re-judgement of any answer that was genuinely asked. This is treated as a real
finding about the project's own tooling, not noise: the manual, human-in-the-loop audit
caught a defect that a purely automated pipeline would have propagated silently into every
downstream measurement.

**Reported:** per-category observability rate (above); per-rule field coverage and
agreement rate (above); catalogue of disagreements (`reports/stage2_disagreements_for_review.txt`).

**Limitation:** single coder, so no inter-rater reliability statistic. Coding scheme
defined in advance and applied consistently. Stated in limitations.
---

## Evaluation plan

### Metrics per objective

| Objective | Metric(s) | Data / conditions | Baseline | Success threshold |
|---|---|---|---|---|
| O1 Taxonomy | Per-category observability; per-rule agreement rate | 200-posting stratified audit sample | Manual judgement as reference | **[TO SET]** — provisional: ≥80% agreement per rule |
| O2 Baseline | Precision, Recall, F1 (fraud), PR-AUC, ROC-AUC | EMSCAD test partition, leakage-controlled | Published EMSCAD results (expect mine lower — leakage control) | **[TO SET]** — provisional: F1 within a stated margin of published, *or* a documented explanation of the gap |
| O3 Multi-signal | Δ F1 (fraud), Δ PR-AUC vs. baseline | Identical partition, identical class weighting | The O2 baseline | **[TO SET]** — note: objective is to *quantify*, so no directional threshold required |
| O4 Explainability | Comprehensiveness, sufficiency, rule-consistency; Brier, ECE | Test partition predictions | Random-attribution control | **[TO SET]** — provisional: 100% rule-consistency; fidelity above random control |
| O5 Evaluation | Full metric set + per-category Δ; Tier 2 transfer | EMSCAD + Tier 2 | Text-only model; EMSCAD-only performance | **[TO SET]** |

> **Thresholds must be agreed with supervisor BEFORE results are seen.** A threshold set
> after seeing results is not a threshold. **Now urgent given the confirmed ~1 month
> deadline — schedule this conversation immediately.**

### Strategy (FEDS positioning)

- **Ex post** — the built artefact is evaluated, not the design in advance.
- **Artificial** — primary evaluation on a benchmark dataset under controlled conditions.
- **Naturalistic component** — Tier 2 assessment on independently collected contemporary
  postings. **Status, 2026-09-20: reduced-scope collection decided** — target ~50–100
  postings (20–30 verified fraud, 30–50 legitimate), sourcing started, ~1-week checkpoint;
  qualitative-only fallback triggers automatically if the checkpoint is missed. See
  `decisions.md`, 2026-09-20.

### Baselines

1. **TF-IDF + Logistic Regression / Random Forest** — the O2 baseline.
2. **Published EMSCAD results** — external comparison, with the leakage-control caveat.
3. ~~Rules-only model~~ — **cut, 2026-09-20** (see `decisions.md`). Stage 9's
   leave-one-category-out ablation covers a related question without a separate arm.
4. **Random-attribution control** — for explanation fidelity.

### Ablation protocol

Each of the four evidence categories removed in turn; model retrained and re-evaluated
under identical conditions. Δ F1 and Δ PR-AUC reported per category.

- Executed at **feature level** using Stage 4 category tags, not field level — `location`
  contributes to both E2 and E4, `salary_range` to both E3 and E4. Overlaps reported
  alongside results.
- **Additional targeted ablation:** remove `has_company_logo`. This field may be unusually
  predictive within EMSCAD for reasons of dataset construction rather than durable fraud
  signal _(claim unverified — see `sources.md` #6)_. Performance sustained without it is a
  stronger result than performance with it.

### Tier 2 experiments

> ⚠️ **Renamed 2026-08-27** to avoid notation collision with the evidence taxonomy (E1–E4
> above refers to evidence categories; these experiments now use T1–T3).

> ⚠️ **Dataset strategy stress-tested, 2026-08-27:** four externally-suggested alternative
> "second datasets" were checked against their primary sources and all found to be EMSCAD
> derivatives, unsuitable as Tier 2. See `decisions.md`, 2026-08-27.
>
> ⚠️ **Scope decided, 2026-09-20:** the plan below runs at reduced scale (~50–100 postings,
> not the original 300–600), with a firm ~1-week collection checkpoint. If T1–T3 end up
> running on a smaller Tier 2 than originally planned, report that plainly — do not let the
> experiment table below imply a scale that wasn't achieved.

| ID | Experiment | What it tests |
|---|---|---|
| T1 | Temporal transfer — EMSCAD-trained model evaluated on Tier 2 | Does an EMSCAD-trained framework still work in 2026? |
| T2 | Signal durability — ablation repeated on Tier 2, profiles compared across eras | **Central hypothesis:** do consistency signals transfer better than lexical cues? |
| T3 | Domain adaptation — fine-tune on a Tier 2 portion, evaluate on remainder | Is the framework maintainable? |

Plus the **source-probe leakage test** (classifier predicts collection source, not label).
Near-perfect probe accuracy indicates residual leakage requiring further normalisation.
Result reported regardless of outcome.

> ⚠️ **Open problem, not yet solved (Decision 0.4):** if fraudulent Tier 2 postings arrive
> as text-only (from scam repositories/advisories) while legitimate postings arrive with
> full structured fields (from ATS/feed provenance), then E3 would separate the classes for
> collection-artefact reasons rather than fraud reasons, and E4 — the actual contribution —
> could not fire on the fraud side at all. This must be resolved before Tier 2 collection
> begins, not discovered afterward. Fallback if unresolved, or if collection proves
> infeasible in the time remaining: report Tier 2 qualitatively and state the limitation
> openly.

### Reproducibility

- All seeds fixed and recorded; every experiment repeated across **3 seeds** (reduced from
  5, decided 2026-09-20 given the deadline — see `decisions.md`), reported as mean ± SD.
- **"3 seeds" means 3 model initialisations against one fixed train/validation/test split**
  — resolved 2026-09-20. This is the only reading compatible with the "test set used once"
  guardrail; it does not mean 3 different splits.
- Environment specs, library versions, model configs version-controlled with the code.
  (Environment established 2026-08-26/27: Python 3.13.9, pandas 3.0.5, PyTorch 2.13.0+cpu,
  Transformers 5.16.1 — full pinned list in `requirements.txt`. **Hardware corrected
  2026-09-20:** RTX 3050 GPU + 16GB RAM — DistilBERT is fine-tuned, not frozen, as a
  result.)
- Tier 2 results reported with confidence intervals given the small sample — now expected
  to be wide, given the reduced ~50–100 posting collection target (see below).

---

## Known threats to validity

| Category | Threat | Mitigation |
|---|---|---|
| Internal | Duplicate postings spanning train/test | Content-hash group-aware partitioning (Decision 0.2, resolved); verified zero overlap across train/val/test, 2026-10-08 — see Partition summary. **One group (3 rows) is label-impure** — an identical posting appears with inconsistent fraud labels in EMSCAD itself; handled by majority-label, disclosed not hidden |
| Internal | `has_company_logo` may encode dataset construction | Targeted ablation; results with and without |
| Internal | Tier 2 provenance labelling → model learns source not fraud | Normalisation, source-dependent feature exclusion, reported source probe |
| Internal | **E4 evaluable on only 42.65% of postings, 0.597 rules/posting on average (final, Stage 4)** | State plainly in Results and Limitations; do not let the original field-coverage estimate or the provisional August figure (56.7% / 0.88) stand uncorrected anywhere in the dissertation |
| External | EMSCAD is 2012–2014, predates AI-assisted fraud | Tier 2 temporal assessment, reported as a primary result — **at risk given the deadline** |
| External | English-language only | Stated scope boundary; multilingual as future work |
| External | Anonymisation destroys email domain | Token counts used instead; unavailable feature documented |
| Construct | Binary labels vs. graded score output | Calibration + Brier, ECE, reliability curve |
| Construct | Explanations may be plausible but unfaithful | Comprehensiveness/sufficiency + rule-consistency check |
| Conclusion | Single-split noise (~130 fraud posts in test) | Five-seed repetition, mean ± SD — **seed count is a scope-cut candidate** |
| Conclusion | Single-coder taxonomy audit | Pre-defined coding scheme; limitation acknowledged |

---

## Results (fill in as they come)

### Data audit — 2026-08-27

_Measured on `DataSet.csv` (the real EMSCAD original, 17,880 rows × 18 columns, no `job_id`
column — confirmed not the reduced Kaggle derivative). Script: `audit/emscad_audit_fixed.py`.
Reproduced identically in two independent environments — sandbox pandas, and the project
venv on pandas 3.0.5 / Python 3.13.9 — same results both times._

- Total records: **17,880**
- Fraudulent / legitimate: **866 / 17,014** (4.84% / 95.16%) — matches published figures exactly
- Boolean encoding confirmed as `t`/`f`: **yes**, all five boolean columns, zero nulls
- `in_balanced_dataset` present and dropped: **yes, present — dropped in Stage 1**

**Missingness per field** (bug fixed 2026-08-27 — original audit script double-counted
every missing value; figures below are corrected):

| Field | Present | Missing | Missing % |
|---|---|---|---|
| title | 17,880 | 0 | 0.0% |
| location | 17,534 | 346 | 1.9% |
| department | 6,327 | 11,553 | 64.6% |
| salary_range | 2,868 | 15,012 | 84.0% |
| company_profile | 14,572 | 3,308 | 18.5% |
| description | 17,880 | 0 | 0.0% |
| requirements | 15,191 | 2,689 | 15.0% |
| benefits | 10,684 | 7,196 | 40.2% |
| telecommuting | 17,880 | 0 | 0.0% |
| has_company_logo | 17,880 | 0 | 0.0% |
| has_questions | 17,880 | 0 | 0.0% |
| employment_type | 14,409 | 3,471 | 19.4% |
| required_experience | 10,830 | 7,050 | 39.4% |
| required_education | 9,775 | 8,105 | 45.3% |
| industry | 12,977 | 4,903 | 27.4% |
| function | 11,425 | 6,455 | 36.1% |

**Salary quality:** present 2,868 (16.0%); literal `"0-0"` placeholder 142; numeric
parseable 2,867; **usable (parseable, not `"0-0"`): 2,725 (15.2%)** — the real ceiling for C6.

**Duplicates** (bug fixed 2026-08-27 — original figure was `n − n_unique`, the *excess*
count, not true group membership; corrected in both the overall and per-class figures):

- Unique descriptions, normalised: 14,375 (vs 15,095 exact-raw — normalising finds more)
- **Records sitting in a duplicate group: 4,762 (26.6% of the corpus)**
- Duplicate groups (size > 1): 1,257; largest group: 417 records
- Fraudulent records in a duplicate group: **349 of 866 (40.3%)**
- Legitimate records in a duplicate group: **4,412 of 17,014 (25.9%)**
- The fraud class is substantially more duplicated than the legitimate class — strong
  independent justification for the group-aware split.
- **Correction (see `decisions.md`, 2026-08-27):** the "English Teacher Abroad" cluster
  previously cited as an example of a duplicated *fraudulent* campaign is in fact 100%
  legitimate — independently corroborated by a third-party dataset derived from the same
  source (the Internship-Job-Scam-Dataset row preview). The decision itself still stands on
  independent grounds.
- **Open — near-duplicate grouping method (Decision 0.2, not yet made):** exact-normalised
  MD5 hashing fragments genuine campaigns (the "English Teacher Abroad" campaign, 715
  records, splits across 15 separate hash groups). A cheap first-12-token proxy was tested
  for comparison but not adopted — it merges 48.9% of the corpus, likely over-merging
  unrelated postings.

**Contact tokens (E2):** all three placeholder token types present and confirmed —
`#URL_#` 7,362 postings (41.2%), `#EMAIL_#` 1,377 postings (7.7%), `#PHONE_#` 657 postings
(3.7%). No other placeholder token types exist in the corpus. E2 stands as designed — this
was the single highest-impact unknown in the audit. Token-by-class rates (descriptive only):
EMAIL 20.1% fraud vs 7.1% legit (ratio 2.84); PHONE 9.2% vs 3.4% (ratio 2.72); URL 42.4% vs
41.1% (ratio 1.03 — not discriminative).

**Location parseability (drives C2):** location present 98.1%; country component usable
98.1%; city component usable 88.4%.

**Measured coverage C1–C6 (final, Stage 4, 2026-10-08):** see the Consistency rule set
table above (Evidence taxonomy section) — field coverage fully verified for all six rules;
evaluable coverage now final for all six, including C2 (real location matcher, no longer
deferred). Aggregate: 42.65% of postings evaluable by at least one rule; mean 0.597 rules
evaluable per posting; see "Stage 4 multi-signal evidence extraction" below for the full
results log.

### Stage 2 manual audit (O1) — 2026-10-08

_Measured on `reports/stage2_manual_audit_worksheet.csv` (200 stratified EMSCAD postings,
single coder, commit `57da423`, corrected in place for the field-presence bug — see
`decisions.md`, 2026-10-07 and 2026-10-08). Full tables and discussion in "Taxonomy
validation (O1)" above; this entry is the dated results-log counterpart to that writeup, in
the format used for every other measurement in this section._

- Observability (Y/PARTIAL/N): E1 89.0%/10.0%/1.0%; E2 74.0%/23.0%/3.0%; E3
  49.0%/30.5%/20.5%; E4 54.5%/26.5%/19.0%.
- Field coverage: C1 100.0%; C2 84.5%; C3 79.5%; C4 57.0%; C5 54.0%; C6 26.5%.
- Agreement rate (MANUAL vs. placeholder-pattern `REFERENCE_ONLY` flag, among rows with the
  field present and a Y/N manual answer): C1 86.9% (173/199); C2 not measured; C3 82.9%
  (131/158); C4 65.2% (73/112); C5 54.5% (55/101); C6 73.6% (39/53).
- Disagreements logged: C1 26, C3 27, C4 39, C5 46, C6 14 — raw list in
  `reports/stage2_disagreements_for_review.txt`; causal write-up still to be done (by the
  student, not fabricated here).
- **Revised/dropped signal:** the field-presence pre-fill bug (NaN → `"nan"` string
  defeating a `!= ""` check), caught twice — see "What the audit made me revise" above.

### Partition summary — 2026-10-08

_Measured by running `src.partitioning.split_data` against `DataSet.csv` (commit
`9a5379b`). 9/9 tests in `tests/test_split_data.py` passing. Re-run in this session's
verification environment (Python 3.10.12, pandas 2.3.3) and compared byte-for-byte
against `reports/stage3_split_summary.json` already committed at `9a5379b` (produced in
the pinned project venv) — **identical output, confirming reproducibility across two
independent environments**, the same standard already applied to the data audit. This is
pure deterministic grouping/allocation (MD5 hashing + a seeded `numpy` permutation, no
model training), so an exact match is the expected and required result, not a loose
approximation._

- **Grouping (description-hash only, Decision 0.2):** 17,880 rows → 14,375 groups; 1,257
  groups of size > 1; **4,762 records (26.63%) in a duplicate group**; largest group 417
  — matches the original August data-audit figures exactly (cross-validates both
  measurements independently).
- **Train / validation / test sizes:** 12,516 / 2,682 / 2,682 (70.0% / 15.0% / 15.0% —
  within 0.01 of every target fraction).
- **Fraud count per partition:** 606 / 130 / 130 (866 total — fully conserved, matches
  the audited corpus total exactly).
- **Fraud rate per partition:** 4.84% / 4.85% / 4.85% — closely tracks the corpus-wide
  4.84%, despite the split allocating whole groups rather than individual rows.
- **Duplicate groups spanning partitions: 0 of 1,257 — verified, not assumed**
  (`verify_split()`'s `zero_group_overlap` check).
- **Near-duplicate grouping method used:** description-hash only (Decision 0.2, resolved
  2026-10-06 after the title-hash union was tried and found to over-merge — see
  `decisions.md`).
- **Finding — one impure group (3 rows), inspected not just counted:** group 7712 holds
  three postings (ids 9138, 11889, 15236) with **byte-for-byte identical description
  text** (a "Workable" company boilerplate, 2,106 characters, confirmed identical, not
  merely near-duplicate) but **inconsistent EMSCAD fraud labels** — one marked
  fraudulent, two legitimate. This is label noise already present in EMSCAD itself, not
  an artefact of the grouping or splitting code. The greedy allocator assigns the whole
  group by majority label (legitimate, 2 of 3), so the one fraud-labelled row travels
  with the legitimate majority — a very small, disclosed deviation (3 of 17,880 rows,
  0.017%) rather than a hidden one. Worth one sentence in the dissertation's limitations,
  not more: 1,256 of 1,257 duplicate groups are label-pure.

### Stage 4 multi-signal evidence extraction (O1, O3) — 2026-10-08

_Measured by running `src.features.extract_features.extract_all()` against the full
EMSCAD corpus (`data/raw/DataSet.csv`, n=17,880) via its own `__main__` driver, which
writes `reports/stage4_coverage_report.json` (committed alongside the module and tests —
pending the student's commit). 33/33 new tests in `tests/test_extract_features.py`
passing; 51/51 across the whole suite (no regression in Stages 1 or 3)._

**What was built:** E1 (a 6-group suspicious-phrase lexicon: advance-fee, unrealistic
earnings, off-platform contact, urgency/pressure, personal-info requests, vague
employer), E2 (company_profile presence/length, location specificity, the Stage 1
contact-token counts carried through, tagged E2_), E3 (9-field presence + equal-weighted
completeness score), and E4 — real C1–C6 lexicons replacing every provisional pattern
from the August audit, including the first real C2 location matcher.

**Methodological safeguard taken (delegated decision, student's instruction "do the best
and most suitable way... take the best decision carefully"):** the 200-posting Stage 2
disagreement notes (`reports/stage2_disagreements_for_review.txt`) are the only
human-labelled signal this project has about these rules. Tuning the new lexicons
row-by-row against that sample until they agreed with it would have been circular — the
same failure mode the project's own guardrail names directly ("a threshold set after
seeing results is not a threshold"). Each rule was instead designed on general linguistic
principle, using the disagreement notes only as qualitative inspiration for *categories*
of failure (e.g. "topic mention vs. genuine claim"), never as a row-by-row tuning target.
No lexicon decision in this module was made by checking its effect on the 200-posting
sample.

**Four precision bugs found and fixed during full-corpus validation, before any figure
above was reported** (same discipline as the C2/C4 fixes already in the module's inline
notes from first authoring) — in each case the fix is a general linguistic distinction
checked against the actual matched text, not a fit to the Stage 2 audit sample:

1. **C1 — "work from home" perk vs. position claim.** The bare phrase fired on
   flexible-working *perks* ("ability to occasionally work from home", "work from home
   Wednesdays") as often as on genuine remote-position claims. 197 of 223 first-pass C1
   "contradictions" (88%) traced to this one phrase. Fixed by requiring a position-
   asserting cue near the phrase and excluding a nearby perk/conditional cue.
2. **C1 — negation ignored.** "This is **not** a remote position" still matched the
   literal phrase "remote position" and was flagged as contradicting the field even
   though the text and field actually agreed. Fixed with a general negation check applied
   to every C1 phrase match, not patched per-phrase.
3. **C6 — "k" (thousands) unresolved, and a dead salary-context gate.** "$95k – $105k"
   parsed as the literal numbers 95 and 105, so a figure that exactly matched the field
   range was reported as "far outside" it. Separately, `_SALARY_WORD_RE` (meant to
   require a $ figure to sit near explicit salary/pay language) was defined but never
   actually wired into the matching logic, so unrelated dollar figures in the same
   posting (a travel/interview reimbursement, a product cost mentioned in ad copy) were
   compared against `salary_range` and flagged as contradictions. Both fixed; the
   context gate is now load-bearing rather than dead code.
4. **C3 — "short-term"/"fixed-term" too polysemous.** 95 of 252 "Temporary"-signal
   contradictions traced to "short-term disability" / "long-term disability" — standard
   US benefits-plan boilerplate with nothing to do with the advertised role's employment
   type. A related shape: bare "seasonal" matched even when describing *other* staff
   mentioned in the posting ("...80 full-time staff and 200 seasonal workers...") rather
   than the advertised role. Fixed by dropping the polysemous bare phrases and requiring
   "seasonal" to be followed by a role-noun.

C1's evaluable/contradiction counts fell from 362/223 (pre-fix) to 90/45 (final) as a
direct result of fix 1–2; C6 from 242/142 to 219/52 as a result of fix 3; C3 from
17.49%-of-evaluable contradictions to 10.84% as a result of fix 4. The final figures in
the Consistency rule set table above are post-fix.

**Data-quality finding, not a code bug — `salary_range` unit ambiguity.** Of 2,725
postings with a parseable `salary_range`, 280 (10.3%) have a low bound under 1,000 (174
under 50) — almost certainly a mix of literal annual-dollar figures, unmarked
"thousands"-shorthand (a field literally reading "135-165" meaning $135k–$165k), and
genuine hourly rates, with no unit indicator in the field itself to tell them apart.
Guessing the unit would itself be an invented assumption, so this was left undecided
rather than "fixed" with a heuristic. This is additional empirical support for Decision
0.3's existing preference for a presence/structure check over numeric comparison in C6 —
the numeric-escalation path is inherently noisier than the rest of C6 for a reason
outside this module's control.

**Two inconsistency patterns found outside C1–C6, logged as future work only (delegated
decision):** the Stage 2 audit surfaced (a) a title-vs-body role mismatch (the advertised
job title doesn't match the role described in the body text) and (b) a
company_profile-vs-description employer mismatch (the company described in the profile
differs from the employer implied in the description). Both are real patterns worth
naming in the dissertation's limitations/future-work section, but neither became a new
rule this stage: C1–C6 is the taxonomy already defined and partially validated against
the 200-posting sample, and extending it now — after seeing these two cases — would be
exactly the kind of post-hoc, result-driven scope change the project's guardrails warn
against ("no objective or research question may presuppose its own result" is the
nearest-in-spirit guardrail, applied here to scope rather than a threshold). See
`decisions.md` for the full decision record.

**C2 gazetteer limitation (restated from the table note above):** ~75 major cities, ~55
ISO country names, and US states — not exhaustive. A genuine location mismatch written
with a place outside this list is under-counted as "not evaluable," not wrongly flagged —
the safer direction for a reported coverage figure.

### Baseline results (O2) — 2026-10-08

_Measured by `src.models.train_baseline` against `data/interim/stage3_split.csv`
(Stage 3's leakage-controlled split, seed 42). Evaluated on **validation only** — test
stays untouched until Stage 9's one-time evaluation. Text input: title+description+
requirements+benefits (same scope as Stage 4's E1 lexicon). `class_weight="balanced"`
on both models, identically (Decision, 2026-08-07) — no SMOTE. 3 seeds (0/1/2), mean ± SD.
Run on the student's own pinned venv (not this project's sandbox), ~8s/seed LogReg,
~4s/seed RF. Full per-seed detail: `reports/stage5_baseline_results.json`._

| Model | Precision | Recall | F1 (fraud) | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|
| TF-IDF + LogReg | 0.464 ± ~0 | 0.692 ± ~0 | 0.556 ± 0 | 0.655 ± 0 | 0.931 ± 0 |
| TF-IDF + RF | 0.881 ± 0.009 | 0.362 ± 0 | 0.513 ± 0.002 | 0.682 ± 0.003 | 0.940 ± 0.003 |

**Reading this, not just reporting it:** LogReg and RF trade off very differently at the
default 0.5 threshold — LogReg catches more fraud (69.2% recall) at the cost of more false
positives (46.4% precision); RF is the reverse (88.1% precision, 36.2% recall). Neither
number is "the" baseline result on its own; which one a risk-band threshold should resemble
is a Stage 6 calibration question, not decided here. SD is ~0 for LogReg (the `lbfgs`
solver is close to deterministic given fixed data) and small for RF (genuine seed
sensitivity, as expected). These are the numbers the improved model (O3) must beat to
justify the added complexity of DistilBERT + structured evidence.

### Multi-signal results (O3) — 2026-10-08

_Measured by `src.models.train_distilbert` against the same `data/interim/stage3_split.csv`
split and validation set the baselines used. 3 seeds (0/1/2), 5 epochs each — 5 was not
assumed; it came from a 6-epoch probe (seed 0) whose validation F1 peaked at epoch 4 and
fell at epoch 5 while train loss kept dropping, the standard overfitting signature (full
curve and reasoning in `decisions.md`, 2026-10-08). Each seed's checkpoint is from
whichever epoch had that run's best validation F1 — not necessarily its last epoch.
Structured evidence vector: all 46 E1–E4 features (see Stage 4), concatenated with
DistilBERT's [CLS] embedding before a small MLP head. `pos_weight` in `BCEWithLogitsLoss`
for class imbalance — the loss-level analogue of the baselines' `class_weight="balanced"`,
not a numerically identical formula (see `decisions.md`, 2026-10-08, for why the two
can't be made identical). Full per-seed detail: `reports/stage5_distilbert_timing.json`._

| Model | Precision | Recall | F1 (fraud) | PR-AUC | ROC-AUC | Δ F1 vs. baseline |
|---|---|---|---|---|---|---|
| TF-IDF + LogReg (baseline) | 0.464 | 0.692 | 0.556 | 0.655 | 0.931 | — |
| TF-IDF + RF (baseline) | 0.881 | 0.362 | 0.513 | 0.682 | 0.940 | — |
| DistilBERT + structured evidence | 0.634 ± 0.050 | 0.713 ± 0.004 | **0.671 ± 0.030** | 0.710 ± 0.018 | 0.934 ± 0.008 | +0.115 vs. LogReg, +0.158 vs. RF |

**Reading this, not just reporting it:** the multi-signal model's F1 and PR-AUC clearly
exceed both baselines, and its precision/recall sit in between LogReg's (high recall, low
precision) and RF's (high precision, low recall) rather than reproducing either extreme —
a more usable operating point for a credibility *score*, not just a classifier. ROC-AUC,
by contrast, is roughly level with both baselines (0.934 vs. 0.931 / 0.940): the gain this
run shows is concentrated in F1/PR-AUC, not a uniform lift across every metric, and
Chapter 4 should say that plainly rather than imply the improvement is across the board.
This was not a selected best-of-3 — all 3 pre-committed seeds (2026-09-20 decision) are
reported above as run, not cherry-picked.

**Ablation seed count, now closed (was conditional since 2026-10-06):** 1 seed per
leave-one-category-out arm (E1, E2, E3, E4, `has_company_logo`), not 3, decided from the
measured ~324.5s/epoch timing above — 3-seed ablation would cost ~6.75 GPU-hours, which
does not fit Day 4 alongside Stage 9's full test evaluation, Tier 2 transfer test,
source-probe leakage test, Stage 7's SHAP, and Stage 8's API wiring. Full reasoning and
what this costs (no per-arm variance estimate) in `decisions.md`, 2026-10-08.

### Final test-set evaluation (O2/O3) — Stage 9, 2026-10-08

_Measured by `src.evaluation.stage9_test_eval` on the 2,682-row EMSCAD test split (130
fraud) — touched for the first time here, per the one-time-evaluation design logged in
`decisions.md`, 2026-10-08, "Stage 9 design decisions." Baseline seed 0 loaded from the
exact Stage 5 checkpoint; seeds 1–2 refit on train only (Decision 3, same file). All 3
DistilBERT+evidence checkpoints are Stage 5's originals, inference only, not retrained.
Full per-seed detail: `reports/stage9_test_results.json`._

| Model | Split | Precision | Recall | F1 (fraud) | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|---|
| TF-IDF + LogReg | validation | 0.464 | 0.692 | 0.556 | 0.655 | 0.931 |
| TF-IDF + LogReg | **test** | 0.522 | 0.738 | 0.611 ± 0.000 | 0.653 ± 0.000 | 0.929 ± 0.000 |
| TF-IDF + RF | validation | 0.881 | 0.362 | 0.513 | 0.682 | 0.940 |
| TF-IDF + RF | **test** | 0.918 ± 0.026 | 0.400 ± 0.008 | 0.557 ± 0.011 | 0.719 ± 0.010 | 0.942 ± 0.002 |
| DistilBERT + structured | validation | 0.634 ± 0.050 | 0.713 ± 0.004 | 0.671 ± 0.030 | 0.710 ± 0.018 | 0.934 ± 0.008 |
| DistilBERT + structured | **test** | 0.594 ± 0.057 | 0.710 ± 0.024 | 0.645 ± 0.031 | 0.713 ± 0.022 | 0.943 ± 0.010 |

_(All ± figures on the test rows are sample SD across the 3 reported seeds, recomputed
directly from `reports/stage9_test_results.json`'s per-seed precision/recall values — the
script's own `mean_sd` dict only aggregates the 5 metrics `_metrics()` returns in one call
each, so P/R SD was calculated separately here rather than copied from a field that doesn't
exist in the JSON.)_

**Δ vs. baseline (test, means):** vs. LogReg: ΔF1 = **+0.034**, ΔPR-AUC = **+0.060**. vs.
RF: ΔF1 = **+0.088**, ΔPR-AUC = **−0.006**.

**Reading this, not averaging it away:**

- **Every model's test numbers sit close to its validation numbers** — no model's
  performance collapsed moving from validation to test, which is the result I'd want to
  see given that only validation was used for every design choice (epochs, seed count,
  checkpoint selection) up to this point. That consistency is itself informative: it's
  evidence against validation-set overfitting in the model-selection decisions made on
  Day 3, not just a result in its own right.
- **F1: the multi-signal model wins outright, on both baselines, on test.** +0.034 over
  LogReg, +0.088 over RF — a reproduction of the validation-side result (+0.115 / +0.158
  there), smaller in absolute terms on test but in the same direction for both baselines.
  This is the central O3 claim and it holds.
- **PR-AUC: the win over LogReg holds (+0.060); the win over RF does not.** On validation,
  the multi-signal model led RF on PR-AUC by +0.028. On test, that reverses to **−0.006**
  — RF's test PR-AUC (0.719) is marginally *higher* than the multi-signal model's (0.713).
  This is not being smoothed into "roughly comparable" — it is a real reversal of a
  validation-side result, and Chapter 4 states it as what it is: on this specific metric,
  against this specific baseline, the improved model does not demonstrate an advantage on
  test. RF's own PR-AUC moved more between splits (0.682 → 0.719) than the multi-signal
  model's did (0.710 → 0.713), which is consistent with — though does not on its own prove
  — ordinary single-split noise at a 130-fraud test size (Known Threats to Validity already
  names "single-split noise (~130 fraud posts in test)" as a conclusion-validity threat,
  which is exactly what this looks like).
- **ROC-AUC does not discriminate between these three models on either split** — all six
  values (3 models × 2 splits) sit inside a narrow 0.929–0.943 band. The story this project
  tells about O3 has to be an F1/precision-recall-trade-off story, not a ROC-AUC story; the
  Stage 5 validation write-up already said this, and test confirms it rather than
  complicating it.
- **The operating-point shape repeats on test:** LogReg stays high-recall/low-precision
  (0.522 P / 0.738 R), RF stays high-precision/low-recall (0.918 P / 0.400 R), and the
  multi-signal model again sits between them (0.594 P / 0.710 R) rather than reproducing
  either extreme — the same "more usable as a graded score" shape validation showed, now
  confirmed out-of-sample.
- **Per Decision 2 (`decisions.md`, 2026-10-08):** these numbers are now seen. No further
  change to the model architecture, feature set, or seed choice is permitted for the rest
  of this project, including in response to the RF PR-AUC result above.

### Calibration (O4) — 2026-10-08

_Measured by `src.calibration.calibrate` against the seed-0 DistilBERT+evidence model's
raw output on validation (n=2682, 130 fraud) — the same model and split Stage 5 reports.
Platt scaling fit on the raw pre-sigmoid logit; isotonic regression fit on the raw
post-sigmoid probability; both evaluated against the raw (uncalibrated) output. Fit AND
evaluated on validation only, per the project's "calibrator on validation, test used once"
guardrail — the numbers below are what SELECTED the calibrator, not the final citable
calibration result (that comes from Stage 9's one-time test-set run of whichever
calibrator was picked here)._

| Calibrator | Brier | ECE |
|---|---|---|
| None (raw) | 0.0275 | 0.0231 |
| Platt | 0.0212 | 0.0050 |
| **Isotonic (selected)** | **0.0199** | **~0.0000** |

**Calibrator selected: isotonic** — lowest on both Brier and ECE, no disagreement between
the two criteria. The reliability curve (`reports/stage6_reliability_curve.png`) shows the
raw model is genuinely overconfident: predicted probabilities sit visibly below the
diagonal through the mid-range, then jump sharply only in the 0.9–1.0 bin. Both
calibrators correct this; isotonic tracks the diagonal most closely.

**A necessary caveat on the ECE≈0.000 figure:** isotonic regression is flexible enough
(effectively many degrees of freedom) that it can closely trace the empirical calibration
curve of the exact data it was fit on — several of its reliability bins match mean
confidence to actual fraction-positive to 3+ decimal places, which is expected of a method
with this much flexibility, not evidence the model is perfectly calibrated in general. The
preference for isotonic over Platt is still real (it also wins on Brier, a less gameable
metric), but this specific ECE number is a validation-set selection statistic, not the
model's true, generalizable calibration error. **The honest, citable calibration result
is whatever Stage 9 reports when this same frozen isotonic calibrator is applied once to
the untouched test set** — not this number.

**Risk bands (provisional):** Low 0–33, Medium 34–66, High 67–100, applied to the
calibrated 0–100 score. Simple terciles, not validated against an external standard —
`PROJECT_PLAN.md` already records evaluation thresholds as open pending supervisor input;
revisit if a contact window opens before submission.

Calibrated-**fraud-probability** summary on validation: mean 4.8, range [0.0, 95.7] —
consistent with the true ~4.8% fraud base rate, a reasonable sign the calibration isn't
systematically shifted. **Correction, 2026-10-08:** this number is calibrated P(fraudulent),
not the API's `credibility_score` — the two are complements
(`credibility_score = (1 − calibrated P(fraud)) × 100`). An earlier version of this sentence
called it "the calibrated score" without that distinction, which `src/api/pipeline.py`
briefly inherited as a real bug (Stage 8 smoke test scored an obvious scam posting 71/100
"Low risk") before being caught and fixed the same day — see decisions.md, 2026-10-08,
"Stage 8 smoke test caught an inverted credibility score." Nothing about the calibration
itself (Brier/ECE, which calibrator won) changes; only this label.

### Explanation fidelity (O4) — 2026-10-08

**Sample:** validation split, all fraud postings (130) + an equal-sized random sample of
validation legitimate postings (130) = 260 total. Not prevalence-representative by design
(decisions.md) — oversampled the minority class for statistical power on the fidelity
tests, which is a statistic about the explanations, not about the dataset.

**Method:** SHAP (`KernelExplainer`, `nsamples=3000`, `l1_reg=0`) over the 46 structured
E1–E4 features, holding each posting's own DistilBERT [CLS] embedding fixed and varying
only the structured vector through the model's MLP head (`FusedModel.head`) — never
re-running DistilBERT per coalition sample. Runtime: 26.9s total / 0.10s per posting on
the seed-0 model (fast, because only the MLP head is evaluated per coalition, not the full
transformer).

SHAP and the fidelity tests explain the model's raw **logit** (pre-sigmoid), not the
post-sigmoid probability. A first run in probability space produced a positive but tiny
SHAP-vs-random gap (comprehensiveness ~0.002) — traced to most postings' predicted
probability sitting in the saturated, near-zero part of the sigmoid, which compresses any
feature's measurable effect regardless of explanation quality. Switching to logit space
(unsaturated) is a measurement correction, not a re-run for a better-looking number — full
reasoning in `decisions.md`, 2026-10-08.

**Comprehensiveness / sufficiency, SHAP vs. a random-ranking control (10 reps/posting), in
logit units:**

| k (of 46 features) | SHAP comprehensiveness | Random comprehensiveness | Gap | SHAP \|sufficiency\| | Random \|sufficiency\| |
|---|---|---|---|---|---|
| 2 | 0.0390 | 0.0023 | +0.0367 | 0.0388 | 0.0660 |
| 5 | 0.0457 | 0.0055 | +0.0402 | 0.0203 | 0.0615 |
| 10 | 0.0451 | 0.0106 | +0.0345 | 0.0110 | 0.0541 |
| 15 | 0.0417 | 0.0149 | +0.0267 | 0.0079 | 0.0464 |
| 23 | 0.0430 | 0.0231 | +0.0199 | 0.0022 | 0.0346 |

At every k, SHAP's ranking removes more predictive signal when its top features are
deleted (comprehensiveness) and preserves the prediction far better when only its top
features are kept (sufficiency) than a random ranking does — a consistent fidelity signal,
not an artefact of one favourable k.

**Rule-consistency:** 100% (14/14 postings with ≥1 fired C1–C6 contradiction had that
rule's feature inside SHAP's top-ranked features), identical at top-5, top-10, and top-15
— 95% Wilson CI [0.785, 1.000] at every k (n=14; a perfect mean from a small n is weaker
evidence than "100%" suggests on its own, hence the CI). The result being identical at
top-5 and top-15 is itself informative: a fired contradiction flag's feature lands inside
the very top 5 of 46 features every time, not just inside a looser top-15 cutoff.

**Limitation, stated plainly:** sparse binary features — most postings have
`C{i}_contradiction = 0`, so the rare posting where one fires sits far from its
background/mean value — structurally tend to receive large SHAP attributions on that
basis alone, independent of whether the model's prediction genuinely depends on that rule
versus any other rare deviation. The 100% rule-consistency figure is consistent with the
model substantively relying on the C1–C6 rules, but this script cannot separate that from
the structural effect; Chapter 5 should carry this caveat rather than present
rule-consistency as unqualified proof the model "uses" the rules.

**Not run on the test split, anywhere** — see decisions.md for why validation was used for
this stage instead of a test subsample.

### Ablation (O5) — Stage 9, 2026-10-08

_Measured by `src.evaluation.stage9_ablation` — 5 arms, 1 seed each (seed 0), 5 epochs
each, checkpointed on best VALIDATION F1, evaluated ONCE on test. Compared against the
full model's seed-0 test result specifically (Decision 4, `decisions.md`), not the 3-seed
mean. Total run time ~2.4 hours (5 arms × ~1770–1810s). Full per-epoch detail:
`reports/stage9_ablation_results.json`. Checkpoints saved:
`models/stage9_ablation_{arm}_seed0.*`._

| Removed category | F1 | Δ F1 | PR-AUC | Δ PR-AUC |
|---|---|---|---|---|
| None (full model, seed 0) | 0.6449 | — | 0.6881 | — |
| − E1 Text | 0.6055 | **−0.0394** | 0.7063 | +0.0182 |
| − E2 Identity | 0.6149 | **−0.0300** | 0.7068 | +0.0187 |
| − E3 Completeness | 0.6228 | **−0.0221** | 0.7135 | +0.0254 |
| − E4 Consistency | 0.6090 | **−0.0359** | 0.6937 | +0.0056 |
| − `has_company_logo` | 0.6768 | **+0.0319** | 0.7159 | +0.0278 |

**Reading this, with the limitation this result sits on stated up front, not buried:**

- **No per-arm variance estimate exists.** This was a disclosed, accepted cost when the
  ablation seed count was closed at 1 (not 3) per arm, 2026-10-06/08 — a GPU-time decision,
  not a methodological ideal. It matters here specifically: DistilBERT fine-tuning on this
  setup is not bit-exact reproducible even at a fixed seed value (`decisions.md`, Stage 5
  epoch-count entry — cuDNN/attention kernels aren't forced deterministic), so every number
  in this table carries ordinary run-to-run training noise on top of whatever the removed
  category's real effect is, and there is no second run for any arm to check how much of
  either delta is noise.
- **F1 points the expected direction for all four evidence categories.** Removing any one
  of E1-E4 lowers F1 (−0.022 to −0.039) — consistent with "each category contributes
  something," the basic claim multi-signal evidence needs to support. Ranked by F1 drop:
  **E1 (text/lexicon) > E4 (consistency) > E2 (identity) > E3 (completeness)** — in this
  single-seed run, the suspicious-phrase lexicon mattered most to F1 and metadata
  completeness mattered least. With no per-arm variance estimate, this ranking is reported
  as what this run showed, not as a precise, statistically separated ordering.
- **PR-AUC points the opposite direction for all four — every single arm's PR-AUC is
  higher than the full model's**, including E4 at a near-zero +0.0056. This is the pattern
  most at risk of being over-read: F1 (fixed 0.5 threshold) and PR-AUC (threshold-free,
  integrates the whole precision-recall curve) can legitimately diverge for a real reason,
  but a uniform direction across all four independent arms, on a metric Stage 9's main
  comparison already showed to be noisy at this test size (130 fraud postings — the RF
  PR-AUC reversal above), is at least as consistent with "the full model's seed-0 PR-AUC
  happened to land low" as with "every evidence category genuinely hurts ranking quality."
  **This project does not have the data to tell those two explanations apart**, and Chapter
  4/5 should say so rather than picking the more flattering reading.
- **`has_company_logo` is the one arm that improves on both metrics** (+0.032 F1, +0.028
  PR-AUC) — the largest F1 gain of any arm, in the direction the project's own pre-
  registered suspicion predicted (`sources.md` #6: this field may be unusually predictive
  within EMSCAD for reasons of dataset construction rather than a durable fraud signal).
  Methodology originally framed the bar as "performance sustained without it is a stronger
  result than performance with it" — this result clears that bar: performance measurably
  *improves* without it. This is the ablation's clearest, least noise-dependent finding,
  because it's the only arm where both metrics agree.
- **Per Decision 2:** these results do not justify dropping `has_company_logo` from the
  shipped model now — that would be a model change made because of a test-set result,
  which the "used once" guardrail forecloses for the rest of this project. It is reported
  as a finding and a recommendation for future work, not acted on here.

### Tier 2 (O5) — 2026-10-08

**Collected:** 24 fraudulent postings (BBB Scam Tracker) + 130 legitimate postings (120
Greenhouse, 10 Lever) = 154 postings, built into EMSCAD-shaped rows through the same
`record_to_request` -> `build_posting_row` pipeline Stage 8b uses
(`src/evaluation/stage9_tier2_and_leakage.py`). Full numeric output:
`reports/stage9_tier2_and_leakage_results.json`.

#### Source-probe leakage test: ROC-AUC = 1.0000, balanced accuracy = 1.0000

**This is not a fraud-detection result and is not reported as one** — the probe is a
separate `LogisticRegression` trained only to answer "is this row EMSCAD or Tier 2,"
using the same 46 structured E1-E4 features the fraud model uses. A perfect score here
means those features can tell the two *sources* apart, which is a problem for how far
T1/T2/T3 below can be trusted, not a result about fraud.

Investigated with `device_bash` rather than taken at face value (2026-10-08). Root cause
confirmed and quantified, not inferred:

| Field | EMSCAD-train missing | Tier 2 fraud missing (n=24) | Tier 2 legit missing (n=130) |
|---|---|---|---|
| has_company_logo | 0.0% (0/12,516) | 100% (0/24 present) | 100% (0/130 present) |
| has_questions | 0.0% (0/12,516) | 100% (0/24 present) | 100% (0/130 present) |
| salary_range | 85.5% | 100% | 100% |
| required_experience | 40.7% | 100% | 100% |
| required_education | 44.7% | 100% | 100% |
| industry | 26.9% | 100% | 100% |
| function | 37.2% | 100% | 100% |
| department | 66.5% | 100% | 92.3% (10/130 present) |
| employment_type | 19.1% | 100% | 92.3% (10/130 present) |

`has_company_logo` / `has_questions` alone are already a perfect, single-feature
separator: EMSCAD's source CSV never leaves them null (audited at Stage 1 —
`load_emscad.py`'s own docstring: "0% missing — real values only, never null"), while
Tier 2's raw collection — BBB Scam Tracker fraud reports *and* the Greenhouse/Lever
legitimate scrape alike — never captured either field for a single one of the 154
postings. The other seven `STRUCT_COLS` fields sit at or near 100% missing on both Tier 2
classes too, so they reinforce the same signal rather than complicating it.

**This is larger in scope than Decision 0.4 (2026-10-06, `decisions.md`) anticipated.**
That decision foresaw an asymmetry between Tier 2's fraud side (BBB, text-only) and its
legitimate side (Greenhouse/Lever, potentially more structured). What's confirmed here
instead is a near-total absence of these nine fields across **both** Tier 2 classes —
driven by how Tier 2 was collected, not by fraud status. Addendum logged in
`decisions.md`, Decision 0.4, 2026-10-08.

**Consequence for T1/T2/T3 below (flagged as a plausible reading, not a separately
measured fact):** the E3 completeness group (10 of the model's 46 features) is close to
constant across all 154 Tier 2 rows, so it cannot discriminate fraud from legit *within*
Tier 2 regardless of what it contributes on EMSCAD. More importantly, EMSCAD's own
fraud/legit split makes total E3 missingness disproportionately a fraud cue (part of why
E3 was built as an evidence category at all) — so a model trained on EMSCAD may read
*every* Tier 2 posting's near-total missingness as "looks suspicious," independent of its
real label. This is offered as a candidate explanation for part of the pattern below, not
as an independently verified result.

#### T1 — temporal transfer (3 seeds, EMSCAD-trained model, zero-shot on all 154 Tier 2 rows)

| Seed | F1 | PR-AUC |
|---|---|---|
| 0 | 0.2222 | 0.5533 |
| 1 | 0.7000 | 0.8351 |
| 2 | 0.4848 | 0.7984 |
| **mean +/- SD** | **0.4690 +/- 0.2393** | **0.7289 +/- 0.1532** |

For comparison, EMSCAD test (seed 0, from "Final test-set evaluation" above): F1=0.6449,
PR-AUC=0.6881.

**Read with the same caution as any 24-fraud-example statistic.** An SD of 0.24 on F1
across three seeds of the *same trained model* on the *same 154 rows* is less a
transfer-quality measurement than a demonstration that F1 is not a stable statistic at
this sample size — consistent with the GPU non-determinism already documented
(`decisions.md`, Stage 5 epoch-count entry: cuDNN/attention kernels aren't forced
deterministic even at a fixed seed). No single seed's number is reported as "the"
temporal-transfer result; the honest statement is the mean +/- SD, with the SD itself
being as informative as the mean.

#### T2 — signal durability (5 ablation arms, reused Part 2 checkpoints, zero-shot on Tier 2, vs. full-model seed 0 = T1 seed 0)

| Arm removed | F1 | delta F1 vs. full (seed 0) | PR-AUC | delta PR-AUC |
|---|---|---|---|---|
| E1 | 0.3750 | +0.1528 | 0.6132 | +0.0599 |
| E2 | 0.4242 | +0.2020 | 0.5507 | -0.0026 |
| E3 | 0.4000 | +0.1778 | 0.7540 | +0.2007 |
| E4 | 0.6842 | +0.4620 | 0.7786 | +0.2253 |
| has_company_logo | 0.4516 | +0.2294 | 0.7284 | +0.1751 |

**Not read as "removing any category helps on Tier 2."** Every delta is positive only
because the comparison baseline (full model, seed 0, F1=0.2222) is T1's demonstrated low
outlier on this same model — seed 1 alone scored F1=0.70. With no per-arm seed variance
(same 1-seed-per-arm budget decision used for the EMSCAD-test ablation) and T1 showing
seed-to-seed F1 swings larger than any delta in this table, these numbers cannot
distinguish "category X doesn't transfer to Tier 2" from "seed 0 was already this run's
unlucky draw before any category was removed." The one point worth naming regardless: E3's
removal shows the second-largest PR-AUC gain (+0.2007) of any arm, consistent with — not
proof of — the completeness-group finding above (E3 close to constant and possibly
actively misread as a fraud cue on Tier 2). Per Decision 2, nothing here is acted on; it is
reported and flagged for Chapter 5.

#### T3 — domain adaptation (50/50 stratified split: 77/12 fine-tune, 77/12 eval)

| | F1 | PR-AUC |
|---|---|---|
| Zero-shot | 0.2857 | 0.7161 |
| Fine-tuned (3 epochs, final-epoch number) | 0.8571 | 0.9833 |

A brief fine-tune on 77 Tier 2 rows (12 fraud) recovers to a level above the EMSCAD-test
baseline, measured on a disjoint 77-row (12-fraud) held-out half. **The same small-sample
caution as T1/T2 applies, at an even smaller N** — 12 fraud examples in each half means a
handful of predictions moving can swing F1 by a large amount; this demonstrates that brief
domain adaptation is *possible*, not a precise or generalisable recovery-rate estimate. The
epoch count (3), learning rate, and split ratio were fixed before running
(`decisions.md`, "Stage 9, Part 3 design decisions," 2026-10-08) specifically so this
number could not be tuned toward a better-looking result after the fact.

#### Summary reading for Chapter 4/5

The source-probe finding is the one number in this section backed by a fully verified,
quantified root cause rather than an inference: Tier 2's structured-field collection is
categorically different from EMSCAD's, across both classes, and this is a disclosed,
significant limitation on how much weight T1/T2/T3's absolute numbers can carry. They
measure the fused model's behaviour on data whose completeness profile looks nothing like
anything it was trained on — a *harder*, not an equivalent, test of temporal transfer than
the EMSCAD test split itself. T1/T2/T3 are reported in full rather than suppressed
(Decision 0.4's own reasoning: disclosing a confound beats dropping the experiment), but no
individual number above should be read as a stable estimate at n=154 (24 fraud).

### Demonstration (Step 4) — 2026-10-08

Source: Tier 2 (154 real postings: 24 fraud, 130 legit), not EMSCAD test. Selection was a
pre-registered, content-blind mechanical rule — not hand-picked — run before any posting
was individually inspected (decisions.md, "Stage 8b selection method"). All three examples
were run through the real, live `/score` pipeline (`src/api/pipeline.py`, the same code
`src/api/main.py` calls), not a notebook shortcut. Full output in
`reports/stage8b_demonstration.json`.

| Case | Type | Source | Score | Band | Calibrated P(fraud) | Contradictions found | Notes |
|---|---|---|---|---|---|---|---|
| 1 | Clear fraud | BBB Scam Tracker #973052 (fraud#10) | 7 | High | 0.933 | 0 fired | See note (a), (b) below |
| 2 | Clear legitimate | Stripe careers site (legit#19) | 100 | Low | 0.000 | 0 fired | Correctly confident despite several missing structured fields (no company_profile, no industry) |
| 3 | Ambiguous | BBB Scam Tracker #744199 (fraud#20) | 25 | High | 0.750 | 0 fired | See note (a), (c) below |

**(a) Cases 1 and 3's `top_reasons` are word-for-word identical.** Both source records have
every structured field (location, department, salary_range, employment_type, industry,
company_profile, etc.) set to `None` — verified directly against the raw Tier 2 JSONL, not
inferred. SHAP's scope (Stage 7, logged) is deliberately limited to the 46 structured E1-E4
features; DistilBERT's text embedding, which is what actually drives the two postings'
different scores (7 vs. 25), is held fixed and never explained by this pathway. Two
postings with identical (all-null) structured vectors therefore produce near-identical
structured-feature SHAP rankings by construction — this is the Decision 0.4 field-asymmetry
risk (Tier 2 / BBB Scam Tracker reports carry almost no structured metadata), now
concretely observed in a live demonstration rather than only anticipated. Logged in full,
with the verification steps taken, in decisions.md, 2026-10-08.

**(b) Both fraud examples show `suspicious_phrases: []`.** Checked directly: neither
description matches any pattern in any `E1_LEXICON` group (`src/features/extract_features.py`)
— zero matches, confirmed by running the actual compiled regexes against the actual text.
The lexicon targets "classic" scam-ad phrasing (guaranteed income, wire transfer, act now);
these two BBB victim reports are written in a more modern, narrative, first-person style
that the lexicon wasn't built to catch. The fused model still correctly flagged both with
high confidence (93.3%, 75.0% calibrated P(fraud)) through the DistilBERT text channel and
structural-completeness signals — evidence *for* the multi-signal design over lexicon
matching alone, but it means E1's contribution to these two specific explanations is
honestly zero, not a defect being concealed.

**(c) Case 3's calibrated P(fraud) = 0.75 is not a literal coin-flip.** By construction it
is the single Tier 2 posting (of all 154) whose calibrated P(fraud) is closest to 0.50 —
guaranteed by the selection rule, not re-verified separately — but 0.75 itself is not close
to 0.50 in absolute terms. This was not re-measured against the full 154-posting
distribution (would require the full torch-enabled scoring run); Stage 9's Tier 2 temporal-
transfer run will report that distribution directly. A plausible but **unverified**
explanation is the probability-skew/saturation behaviour already documented under
"Explanation fidelity (O4)" above — flagged here as inference, not measurement.
