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

### Baseline results (O2) — [DATE]

| Model | Precision | Recall | F1 (fraud) | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|
| TF-IDF + LogReg | | | | | |
| TF-IDF + RF | | | | | |

### Multi-signal results (O3) — [DATE]

| Model | Precision | Recall | F1 (fraud) | PR-AUC | ROC-AUC | Δ F1 vs. baseline |
|---|---|---|---|---|---|---|
| DistilBERT + structured evidence | | | | | | |

### Calibration (O4) — [DATE]

- Calibrator selected: [ Platt / isotonic / none ] — reason: [ ]
- Brier score before / after: [ ] / [ ]
- ECE before / after: [ ] / [ ]
- Risk band thresholds: [ ]

### Explanation fidelity (O4) — [DATE]

- Comprehensiveness: [ ] · Sufficiency: [ ] · Random control: [ ]
- Rule-consistency: [ ]% of raised flags present in generated explanations

### Ablation (O5) — [DATE]

| Removed category | F1 | Δ F1 | PR-AUC | Δ PR-AUC |
|---|---|---|---|---|
| None (full model) | | — | | — |
| − E1 Text | | | | |
| − E2 Identity | | | | |
| − E3 Completeness | | | | |
| − E4 Consistency | | | | |
| − `has_company_logo` | | | | |

### Tier 2 (O5) — [DATE]

- Collected: [ ] legitimate / [ ] fraudulent, from [sources]
- Source-probe accuracy: [ ] — interpretation: [ ]
- T1 temporal transfer: [ ]
- T2 signal durability — per-category Δ comparison across eras: [ ]
- T3 domain adaptation recovery: [ ]

### Demonstration (Step 4) — [DATE]

| Case | Type | Score | Band | Contradictions found | Notes |
|---|---|---|---|---|---|
| 1 | Clear fraud | | | | |
| 2 | Clear legitimate | | | | |
| 3 | Ambiguous | | | | |
