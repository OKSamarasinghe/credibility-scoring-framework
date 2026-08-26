# methodology.md — How I'm Doing This (and the Evaluation Plan)

_Last updated: 2026-08-07_

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

**Status: not yet started. No code written, no data loaded.**

### Step 4 — Demonstration

_[ADDED 2026-08-07 — this step was missing from the formal methodology document and must be
added there.]_

Before formal evaluation, the API will be demonstrated end-to-end on a small set of real
postings to establish proof of life. The demonstration set will deliberately include:

- at least one clearly fraudulent posting,
- at least one clearly legitimate posting,
- **at least one genuinely ambiguous posting** — no cherry-picking the easy cases.

For each, the full JSON response is captured (`credibility_score`, `risk_band`,
`top_reasons`, `suspicious_phrases`, `contradictions`, `verification_checklist`) along with
the input.

**Demonstration proves the artefact works at all. It proves nothing about how well.**
That is Step 5's job, and the two are reported separately.

### Step 5 — Evaluation

Full plan below. Designed to be hard to pass, not easy.

### Step 6 — Communication

Dissertation plus research paper. Drafted from `decisions.md` and this file rather than
from scratch. AI-use declaration to be included — see `project.md` open questions.

---

## Implementation stages

| Stage | Activity | Objective | Status |
|---|---|---|---|
| 1 | Data ingestion & preprocessing | Foundation | Not started |
| 2 | Evidence taxonomy definition & manual audit | O1 | Not started |
| 3 | Leakage-controlled data partitioning | O2, O3, O5 | Not started |
| 4 | Multi-signal evidence extraction | O1, O3 | Not started |
| 5 | Model development (baseline & improved) | O2, O3 | Not started |
| 6 | Probability calibration & score mapping | O4 | Not started |
| 7 | Explainability layer & fidelity evaluation | O4 | Not started |
| 8 | API development | O4 | Not started |
| **8b** | **Demonstration** _(to add to formal doc)_ | O4 | Not started |
| 9 | Evaluation, ablation & generalisability | O5 | Not started |

### Stage 1 critical ordering constraints

1. Map `t`/`f` string literals to integers **on load**; assert fraud count = 866 before
   proceeding. _(Encoding claim unverified — see `sources.md` #4.)_
2. Drop `in_balanced_dataset`.
3. **Extract `#EMAIL_#` / `#PHONE_#` / `#URL_#` tokens, image refs and link counts BEFORE
   stripping HTML.** Reversing this destroys the whole E2 feature group.
4. Treat `salary_range` value `"0-0"` as missing.
5. Flag missingness per field; never impute.

---

## Evidence taxonomy (O1)

| ID | Category | Signals |
|---|---|---|
| E1 | Text / Content Cues | TF-IDF weights (baseline); contextual embeddings (improved); suspicious-phrase lexicon matches |
| E2 | Identity & Contact Cues | company_profile presence/length; location specificity; contact/email/URL token counts |
| E3 | Metadata Completeness | presence flags across 9 structured fields + composite score |
| E4 | Text–Metadata Consistency | rules C1–C6 + aggregate contradiction count |

### Consistency rule set (C1–C6) — the novelty

| ID | Rule | Trigger | Field coverage | Measured coverage |
|---|---|---|---|---|
| C1 | Remote / on-site | `telecommuting` false but description matches remote-work lexicon | 100% ⚠️ est. | [TO MEASURE] |
| C2 | Location mismatch | location country/city absent from description while a different location is named | 98% ⚠️ est. | [TO MEASURE] |
| C3 | Employment type | `employment_type` conflicts with working-arrangement language | 81% ⚠️ est. | [TO MEASURE] |
| C4 | Experience level | `required_experience` conflicts with "N+ years" extracted from text | 61% ⚠️ est. | [TO MEASURE] |
| C5 | Education | `required_education` conflicts with qualification statements | 55% ⚠️ est. | [TO MEASURE] |
| C6 | Salary | description figures fall outside parsed `salary_range` beyond tolerance | 16% ⚠️ est. | [TO MEASURE] |

> ⚠️ **The "field coverage" column is UNVERIFIED and is an upper bound, not rule coverage.**
> These are field-availability rates inferred from a dataset profile, not measured on the
> CSV. True triggerable coverage will be **lower** — C2 needs both a parseable location
> *and* a location mention in the text. Replace with measured values from the data audit
> before these figures enter the dissertation. See `sources.md` #3.

### Taxonomy validation (O1)

Manual audit of 200 stratified EMSCAD postings (100 fraudulent / 100 legitimate), fixed
seed. Records per posting: which categories are observable; whether each automated rule
agrees with manual judgement.

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
> after seeing results is not a threshold.

### Strategy (FEDS positioning)

- **Ex post** — the built artefact is evaluated, not the design in advance.
- **Artificial** — primary evaluation on a benchmark dataset under controlled conditions.
- **Naturalistic component** — Tier 2 assessment on independently collected contemporary
  postings.

### Baselines

1. **TF-IDF + Logistic Regression / Random Forest** — the O2 baseline.
2. **Published EMSCAD results** — external comparison, with the leakage-control caveat.
3. **Rules-only model** — *pending decision, see `decisions.md`*.
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

| ID | Experiment | What it tests |
|---|---|---|
| E1 | Temporal transfer — EMSCAD-trained model evaluated on Tier 2 | Does an EMSCAD-trained framework still work in 2026? |
| E2 | Signal durability — ablation repeated on Tier 2, profiles compared across eras | **Central hypothesis:** do consistency signals transfer better than lexical cues? |
| E3 | Domain adaptation — fine-tune on a Tier 2 portion, evaluate on remainder | Is the framework maintainable? |

Plus the **source-probe leakage test** (classifier predicts collection source, not label).
Near-perfect probe accuracy indicates residual leakage requiring further normalisation.
Result reported regardless of outcome.

### Reproducibility

- All seeds fixed and recorded; every experiment repeated across **five seeds**, reported
  as mean ± SD.
- Environment specs, library versions, model configs version-controlled with the code.
- Tier 2 results reported with confidence intervals given the small sample.

---

## Known threats to validity

| Category | Threat | Mitigation |
|---|---|---|
| Internal | Duplicate postings spanning train/test | Content-hash group-aware partitioning; duplicate count reported |
| Internal | `has_company_logo` may encode dataset construction | Targeted ablation; results with and without |
| Internal | Tier 2 provenance labelling → model learns source not fraud | Normalisation, source-dependent feature exclusion, reported source probe |
| External | EMSCAD is 2012–2014, predates AI-assisted fraud | Tier 2 temporal assessment, reported as a primary result |
| External | English-language only | Stated scope boundary; multilingual as future work |
| External | Anonymisation destroys email domain | Token counts used instead; unavailable feature documented |
| Construct | Binary labels vs. graded score output | Calibration + Brier, ECE, reliability curve |
| Construct | Explanations may be plausible but unfaithful | Comprehensiveness/sufficiency + rule-consistency check |
| Conclusion | Single-split noise (~130 fraud posts in test) | Five-seed repetition, mean ± SD |
| Conclusion | Single-coder taxonomy audit | Pre-defined coding scheme; limitation acknowledged |

---

## Results (fill in as they come)

### Data audit — [DATE]

- Total records: [ ]
- Fraudulent / legitimate: [ ] / [ ]
- Boolean encoding confirmed as `t`/`f`: [ yes / no ]
- Unique normalised descriptions: [ ]  → duplicates removed/grouped: [ ]
- Unique titles: [ ]
- `in_balanced_dataset` present and dropped: [ yes / no ]
- `salary_range` `"0-0"` count: [ ]
- Contact token counts — `#EMAIL_#`: [ ] · `#PHONE_#`: [ ] · `#URL_#`: [ ]
- **Measured coverage C1–C6:** [ ]

### Partition summary — [DATE]

- Train / validation / test sizes: [ ] / [ ] / [ ]
- Fraud ratio per partition: [ ] / [ ] / [ ]
- Duplicate groups spanning partitions: **must be 0**

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
- E1 temporal transfer: [ ]
- E2 signal durability — per-category Δ comparison across eras: [ ]
- E3 domain adaptation recovery: [ ]

### Demonstration (Step 4) — [DATE]

| Case | Type | Score | Band | Contradictions found | Notes |
|---|---|---|---|---|---|
| 1 | Clear fraud | | | | |
| 2 | Clear legitimate | | | | |
| 3 | Ambiguous | | | | |
