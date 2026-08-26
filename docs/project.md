# project.md — An Explainable Credibility Scoring Framework for Online Recruitment Posts

_Last updated: 2026-08-26_

> **How to use this file.** Paste it at the start of every AI working session, before doing
> any work. Keep it current — update "Where I am right now" at the end of each session,
> even if nothing else changed. If this file is stale, every session starts from a lie.

---

## Identity

- **Student:** O.K. Samarasinghe
- **Coventry Index:** 16116041
- **NIBM Index:** COBSCCOMP242P-069
- **Programme:** BSc (Hons) Computing — Coventry University / NIBM, Colombo 7
- **Supervisor:** Mr. Niranga Dharmaratne _[confirm spelling]_
- **Module code:** [FILL IN]
- **Key deadlines:** [FILL IN — dissertation submission, artefact demo, viva]

## Working title

An Explainable Credibility Scoring Framework for Online Recruitment Posts Using
Multi-Signal Evidence and Consistency Verification

## Research approach

Design Science Research (Hevner et al., 2004; Peffers et al., 2007). The study builds and
evaluates a purposeful artefact — an explainable credibility scoring API — rather than
producing theory alone.

---

## Problem statement (current version)

Online recruitment platforms have made job searching faster and wider in reach, but the
same convenience has made job seekers vulnerable to fraudulent and misleading job
advertisements. Job seekers currently verify vacancies manually — checking company names,
contact details and job descriptions — which is slow, inconsistent, and unreliable when
scammers imitate real employers or use professionally worded (increasingly AI-generated)
posts.

Existing machine learning and deep learning systems can detect fraudulent postings, but
four limitations remain: they provide black-box predictions without user-facing reasons;
they are heavily text-centred and underuse structured metadata; they do not verify whether
text and metadata actually agree with one another; and they output a binary fake/real label
rather than graded, actionable decision support.

## Research aim

To design, develop and evaluate an explainable credibility scoring framework for online
recruitment posts using multi-signal evidence and consistency verification.

---

## Research objectives (v3 — finalised 2026-08-07)

| # | Label | Statement (short form) | Type |
|---|---|---|---|
| O1 | Evidence Taxonomy | Define and validate a four-category credibility evidence taxonomy, validated by manual audit of a stratified EMSCAD sample | Must-have |
| O2 | Baseline Model | Develop and benchmark a TF-IDF baseline with classical classifiers on a leakage-controlled, duplicate-aware split | Must-have |
| O3 | Multi-Signal Model | Combine transformer text representation with structured evidence and consistency-contradiction flags; quantify the change under matched conditions | Must-have |
| O4 | Explainable Decision Module | Deliver a backend API converting calibrated probabilities into a 0–100 credibility score with verified explanations | Must-have |
| O5 | Evaluation & Generalisability | Evaluate with full metric set, ablation per evidence category, and temporal generalisability on contemporary postings | Must-have (Tier 2 portion at risk — see Open questions) |

Full statements: see `Research_Objectives_and_Questions_Final.docx`.

**Rule I am holding myself to:** no objective states its own expected result. O3 quantifies
the *extent of change*, not an improvement. A negative finding still completes the objective.

## Research questions

- **RQ1** — What structured evidence categories can be reliably extracted from online recruitment posts to support credibility assessment?
- **RQ2** — How effectively can a baseline text-based model identify fraudulent recruitment posts under leakage-controlled evaluation conditions, and how does this compare with published EMSCAD studies?
- **RQ3** — To what extent does adding structured evidence features and text–metadata consistency verification to a transformer-based representation affect fraud-class detection performance?
- **RQ4** — How can model-agnostic explanation methods and rule-based evidence summaries be combined to produce faithful, user-interpretable reasons for a calibrated credibility score?
- **RQ5** — How does the complete framework perform under standard predictive, calibration and ablation-based evaluation, and to what extent does that performance generalise to contemporary recruitment fraud?

---

## The artefact

- **What it is:** a backend REST API (FastAPI) exposing a `/score` endpoint.
- **What it does:** accepts a job posting (raw text primary; URL best-effort secondary),
  runs preprocessing → multi-signal evidence extraction → prediction → calibration →
  explanation, and returns structured JSON.
- **Response fields:** `credibility_score` (0–100), `risk_band`, `top_reasons`,
  `suspicious_phrases`, `contradictions`, `verification_checklist`.
- **Hard constraints:** single developer; consumer-grade hardware (DistilBERT chosen partly
  for this); no paid data sources; English-language postings only.

## Evidence taxonomy (four categories)

| ID | Category | Source |
|---|---|---|
| E1 | Text / Content Cues | title, description, requirements, benefits |
| E2 | Identity & Contact Cues | company_profile, location, anonymised contact tokens in description |
| E3 | Metadata Completeness | 9 structured fields — presence flags + composite score |
| E4 | Text–Metadata Consistency | rules C1–C6 comparing structured fields against description |

**Consistency rules (the novelty):** C1 remote/on-site, C2 location mismatch,
C3 employment type, C4 experience level, C5 education, C6 salary.

## Datasets

| Tier | Dataset | Size | Role |
|---|---|---|---|
| Tier 1 | EMSCAD (Kaggle mirror; Vidros et al., 2017) | 17,880 (17,014 legit / 866 fraud) | All training, tuning, calibration, ablation |
| Tier 2 | Independently collected contemporary postings | 300–600 target | Held-out temporal validation only. **Never used for training.** |

## Scope

**In scope**
- English-language job postings
- Text, structured metadata, and text–metadata consistency signals
- Explainable AI (SHAP/LIME) plus deterministic rule-based evidence summaries
- Backend API as decision-support tool

**Out of scope**
- Image-based fraud detection; deepfake video interview detection
- Large-scale social network analysis
- Legal verification of employers — the system indicates risk, it does not adjudicate
- Multilingual postings
- Frontend UI (backend API only)
- External company-presence check as a *measured* signal — implemented in the API as a
  qualitative supporting feature only, excluded from ablation and quantitative evaluation

---

## Where I am right now

- **DSR step:** 3 (Design & Build) — at the transition from design into implementation.
- **Phase:** Dissertation write-up AND artefact build, running in parallel.
- **Completed:** proposal accepted; objectives finalised; research questions finalised;
  methodology finalised (9 stages + Stage 8b); dataset strategy decided; Stage 8b and the
  FEDS citation added to `Research_Methodology_Final.docx`; **Chapter 1 (Introduction)
  drafted; Chapter 2 (Literature Review) drafted** with a six-theme empirical review and a
  four-gap research-gap section.
- **Not yet started:** any code. No data has been loaded or measured. Chapters 3–5 not
  drafted. About to begin Chapter 3 (Methodology) write-up and the software build.

### Known state of documents

- `Research_Methodology_Final.docx` now contains Stage 8b (Demonstration) and the FEDS
  citation, matching `methodology.md` and Figure 3. (Previously flagged mismatch is fixed.)
- All numeric values in `Framework_Explanation_Walkthrough.docx` are illustrative worked
  examples, not results. Logged as `sources.md` #17. Never cite them.
- Chapters 1 and 2 cite 11 sources; several are still unread/unverified — tracked in
  `sources.md` Part C. Must be read before final submission.

### Next actions (in order)

1. **Run the data audit** on the real EMSCAD CSV — measure duplicates, confirm `t`/`f`
   encoding, confirm class counts, and measure true per-rule coverage for C1–C6.
   _This replaces estimated figures currently sitting in the methodology document, and
   closes sources.md #3, #4, #5, #7, #9._
2. **Run a divergent-gear review of the model architecture** before building. I committed
   to TF-IDF + DistilBERT at proposal stage without seeing the design landscape.
3. **Decide on adding a rules-only baseline** (see Open questions).
4. **Read the unverified Chapter 1–2 sources** (sources.md Part C) — especially Vidros
   (2017), Mehboob & Malik (2021), Sullivan & Weger (2025).
5. **Begin Chapter 3 (Methodology) write-up** — most content already exists across the
   .docx and .md files.
6. **Begin Stage 1 implementation** (ingestion & preprocessing).

---

## Open questions

- **Should I add a rules-only baseline?** Consistency + completeness features with no text
  model at all. Would answer "does the transformer earn its complexity?" — a stronger
  dissertation result either way. Cost: one extra training arm and extra ablation rows.
  **Decide before Stage 5.**
- **Tier 2 collection is my slowest task and my biggest schedule risk.** The fraudulent
  side requires manual curation. If it slips, O5's generalisability clause is at risk.
  Do I start collection now in parallel with Stage 1?
- **Which specific Tier 2 sources can I actually access?** Both documents currently
  describe sources generically. Named sources are stronger. Need to test access to
  Greenhouse/Lever endpoints, USAJOBS, Arbeitnow, Adzuna free tier.
- **What are my success thresholds?** The evaluation plan in `methodology.md` has metrics
  and baselines but thresholds are still unset. Agree these with supervisor *before*
  running the evaluation, not after seeing results.
- **Ethics form for Tier 2 primary data collection** — submitted? NIBM/Coventry process
  and timeline?
- **AI-use declaration** — what wording does my programme require, and where does it go?
- **Chapter 1 explainability wording** — confirm Chapter 1 says explanations are "rarely
  used and never tested for faithfulness" rather than "absent", so it agrees with Chapter 2
  (which cites Naudé 2023 using LIME in the fraud domain). Sharpened gap, must be consistent
  across both chapters.

---

## Session log

| Date | Focus | Outcome |
|---|---|---|
| 2026-08-07 | Set up project files | Four `.md` files created; project state captured |
| 2026-08-07 | Diagrams + walkthrough | Architecture, workflow and worked-example figures produced; explanation document written |
| 2026-08-07 | SKILL.md + project instructions | Behavioural coach file written; project instructions finalised |
| 2026-08-07 | Data audit script | `emscad_audit.py` written and tested; not yet run on real CSV |
| 2026-08-26 | Chapter 1 drafted | All 8 sections written and reworded; 8 sources cited |
| 2026-08-26 | Chapter 2 drafted | Six-theme empirical review + four-gap section; 11 sources total; Mohiddin dropped; explainability gap sharpened |
| | | |
