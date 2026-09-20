# methodology.md — How I'm Doing This (and the Evaluation Plan)

_Last updated: 2026-09-20_

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

**Status, 2026-08-27:** data audit complete and corrected twice; Stage 1 complete and
tested; Stage 8 skeleton (API routing/schema, no real pipeline yet) complete and tested;
Stage 2 partially complete (sampling code done, manual audit not started). Stages 3–9
otherwise not started.

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
| 2 | Evidence taxonomy definition & manual audit | O1 | 🟡 Sampling script + worksheet built and tested; manual coding of 200 postings not started; repo integration not confirmed |
| 3 | Leakage-controlled data partitioning | O2, O3, O5 | ⬜ Ready to start — Decision 0.2 resolved (MD5 + title grouping), 2026-09-20 |
| 4 | Multi-signal evidence extraction | O1, O3 | ⬜ Not started |
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
| C1 | Remote / on-site | `telecommuting` conflicts with remote/on-site language in description | **100.0%** | **10.5%** | 🟡 Provisional — placeholder pattern |
| C2 | Location mismatch | location field absent from text while a different location is named | **88.4%** | **not measured** | ❌ Deferred to Stage 4 — see note |
| C3 | Employment type | `employment_type` conflicts with working-arrangement language | **80.6%** | **12.2%** | 🟡 Provisional |
| C4 | Experience level | `required_experience` conflicts with "N+ years" extracted from text | **60.6%** | **30.2%** | 🟡 Provisional |
| C5 | Education | `required_education` conflicts with qualification statements | **54.7%** | **27.8%** | 🟡 Provisional |
| C6 | Salary | description figures fall outside parsed `salary_range` | **15.2%** | **7.6%** | 🟡 Provisional |

**Aggregate (measured, 2026-08-27):** postings evaluable by at least one rule: **10,145
(56.7%)** of 17,880. Mean rules evaluable per posting: **0.88 of 6**.

**Why C2 is deferred, not estimated:** C2's premise — a place name in free text differing
from the structured field — is an open-vocabulary problem. A quick regex proxy, unlike the
bounded vocabularies used for C1/C3 (remote/on-site language, employment-arrangement
language), would amount to a second, weaker implementation of the rule that is guaranteed to
disagree with the real Stage 4 location matcher. Field coverage (88.4%) is reported as an
explicit upper bound only.

**Why C1, C3–C6 are "provisional," not final:** all five use placeholder pattern-matching
written for audit purposes, not the final Stage 4 lexicons. **Re-measure every one of these
figures once Stage 4 lexicons are frozen** — do not carry today's numbers into the
dissertation as final results.

**What this means for E4 as a whole:** the original field-coverage estimates (used since
2026-08-07) implied E4 was observable on nearly every posting. The measured, honestly-defined
picture is that under half the corpus (56.7%) can be evaluated by even one rule, and on
average less than one rule per posting (0.88 of 6) can fire at all. This is a real and
significant finding about the practical reach of the consistency-verification contribution —
not a data-quality failure, but something the dissertation must state plainly and account
for, rather than let the original optimistic estimate stand uncorrected.

### Taxonomy validation (O1)

Manual audit of 200 stratified EMSCAD postings (100 fraudulent / 100 legitimate), fixed
seed (42), drawn from **unique normalised descriptions only** — added 2026-08-27, to avoid
near-duplicate campaigns inflating the apparent agreement rate. Records per posting: which
categories are observable; whether each automated rule agrees with manual judgement.

**Sampling script status:** built and tested (`sample_for_manual_audit.py`), reproducibility
confirmed (identical output across repeated runs and across two separate environments).
**Manual coding status:** not started. Coding scheme defined in advance in
`STAGE2_CODING_INSTRUCTIONS.md`.

**Reported:** per-category observability rate; per-rule agreement rate; catalogue of
disagreements and causes.

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
| Internal | Duplicate postings spanning train/test | Content-hash group-aware partitioning; duplicate count measured (see Results) — **near-duplicate grouping method still undecided, see Decision 0.2** |
| Internal | `has_company_logo` may encode dataset construction | Targeted ablation; results with and without |
| Internal | Tier 2 provenance labelling → model learns source not fraud | Normalisation, source-dependent feature exclusion, reported source probe |
| Internal | **E4 evaluable on only 56.7% of postings, 0.88 rules/posting on average** | State plainly in Results and Limitations; do not let the original field-coverage estimate stand uncorrected anywhere in the dissertation |
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

**Measured coverage C1–C6:** see the Consistency rule set table above (Evidence taxonomy
section) — field coverage fully verified for all six rules; evaluable coverage measured but
provisional for C1, C3–C6; deferred entirely for C2 pending Stage 4 location matching.
Aggregate: 56.7% of postings evaluable by at least one rule; mean 0.88 rules evaluable per
posting.

### Partition summary — [DATE]

- Train / validation / test sizes: [ ] / [ ] / [ ]
- Fraud ratio per partition: [ ] / [ ] / [ ]
- Duplicate groups spanning partitions: **must be 0**
- Near-duplicate grouping method used: [ ] _(Decision 0.2 must be settled first)_

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
