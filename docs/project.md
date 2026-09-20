# project.md — An Explainable Credibility Scoring Framework for Online Recruitment Posts

_Last updated: 2026-08-27_

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
- **Key deadlines:** ~1 month from 2026-08-27 (confirm exact date with supervisor/programme
  office — dissertation submission, artefact demo, viva all need individual dates)

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
| O5 | Evaluation & Generalisability | Evaluate with full metric set, ablation per evidence category, and temporal generalisability on contemporary postings | Must-have (Tier 2 portion at risk given the 1-month deadline — see Open questions) |

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
| Tier 1 | EMSCAD (original file, not the reduced Kaggle derivative; Vidros et al., 2017) | 17,880 (17,014 legit / 866 fraud) | All training, tuning, calibration, ablation |
| Tier 2 | Independently collected contemporary postings | 300–600 target | Held-out temporal validation only. **Never used for training.** |

> **Confirmed 2026-08-27:** four externally-suggested "second datasets" (a Kaggle 2026
> competition, DIFrauD's Job Scams split, the Internship-Job-Scam-Dataset, ScamShield) were
> checked against their primary sources and found to all be EMSCAD derivatives — none
> provide independent, contemporary, metadata-rich data. See `decisions.md`, 2026-08-27.
> Tier 2 must still be actively collected; no shortcut exists.

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

- **DSR step:** 3 (Design & Build) — genuinely into implementation now, not just at the
  transition.
- **Phase:** Dissertation write-up (Chapters 1–3 drafted, in `Research_Thesis_Draft.md`) AND
  artefact build, running in parallel. **Deadline confirmed 2026-08-27: ~1 month away.**
- **Completed:**
  - Proposal accepted; objectives finalised; research questions finalised; methodology
    finalised (9 stages + Stage 8b); dataset strategy decided and, as of 2026-08-27,
    stress-tested against four external alternatives and reaffirmed.
  - Chapter 1 (Introduction) and Chapter 2 (Literature Review) drafted in full, with a
    six-theme empirical review and a four-gap research-gap section. Chapter 3 (Methodology)
    also drafted in full.
  - **Environment and repository:** GitHub repo set up, Python 3.13.9 venv with full
    dependency stack installed and verified (including resolving a Windows long-path
    install failure for PyTorch).
  - **Data audit:** run on the real EMSCAD CSV, then corrected twice — a missingness
    double-counting bug, a duplicate-count mislabeling bug (in both the overall and
    per-class figures), and an inconsistent "evaluable coverage" definition across the C1–C6
    rules. All measured figures now verified in two independent environments.
  - **Stage 1 (ingestion):** built and tested — 9/9 tests passing against the real dataset,
    confirmed independently on two machines.
  - **Stage 8 skeleton (API):** FastAPI app, `/score` route, and the full JSON contract
    built and tested. Every pipeline stage honestly reports "not yet built" rather than
    returning fabricated data. Real wiring still pending Stages 4–7.
  - **Stage 2 (taxonomy audit) — partial:** the stratified sampling script and 200-posting
    worksheet are built and tested (seed 42, drawn from unique normalised descriptions to
    avoid duplicate-campaign inflation of agreement rates). **Not yet confirmed integrated
    into the repository — needs verification.** The manual coding of the 200 postings
    (the actual audit) has not started.
- **Not yet started:** Stages 3–9 in full. Tier 2 collection (zero postings — this is now
  the most urgent open risk given the confirmed deadline). Chapters 4–6 of the dissertation
  (Chapter 4 cannot be drafted until Stage 9 produces real measurements).

### Known state of documents

- `Research_Methodology_Final.docx` still shows the *original estimated* C1–C6 field
  coverage figures (100%/98%/81%/61%/55%/16%), not the measured ones (100%/88.4%/80.6%/
  60.6%/54.7%/15.2%), and has no evaluable-coverage column at all. Needs updating once
  Stage 4's real lexicons exist — the current measured figures are still provisional.
- All numeric values in `Framework_Explanation_Walkthrough.docx` are illustrative worked
  examples, not results. Logged as `sources.md` #17. Never cite them.
- `methodology.md`, `sources.md`, and `decisions.md` were re-synced with this project's real
  progress on 2026-08-27, after a period where the working `.md` files had drifted
  significantly behind the actual development chat.
- Chapters 1 and 2 cite 11 sources; several are still unread/unverified — tracked in
  `sources.md` Part C. Must be read before final submission.

### Next actions (in order)

1. **URGENT — decide scope cuts.** Full rigor on all nine stages as originally planned does
   not fit in the confirmed one-month deadline for a single developer. A menu of candidate
   cuts is logged in `decisions.md` under "Pending decisions." This blocks efficient
   planning of everything below and should be decided first.
2. **Confirm Stage 2 files are actually committed to the repository** — the sampling script
   and worksheet were built and tested but integration into git has not been confirmed.
3. **Complete the Stage 2 manual audit** — 200 postings, using the pre-defined coding scheme
   in `STAGE2_CODING_INSTRUCTIONS.md`. This is human work only I can do.
4. **Resolve Decision 0.2** (near-duplicate grouping method) before Stage 3 can start.
5. **Start Tier 2 sourcing** — in parallel with the above, not queued up after. Given the
   deadline, decide now whether the pre-planned fallback (report Tier 2 qualitatively) is
   being invoked.
6. **Resolve the architecture review and frozen-vs-fine-tuned DistilBERT decisions** before
   Stage 5 — both are now time-critical, not just methodologically important.
7. **Read the unverified Chapter 1–2 sources** (sources.md Part C) — especially Vidros
   (2017), Mehboob & Malik (2021), Sullivan & Weger (2025) — as time allows.

---

## Open questions

- **Scope-cut decision — see `decisions.md`, URGENT, top of Pending decisions.** This is now
  the single most important open question in the project.
- **Tier 2 collection is my slowest task and my biggest schedule risk**, and with the
  deadline confirmed at ~1 month, the pre-planned fallback clause (report Tier 2
  qualitatively, state the limitation openly) is now under live consideration rather than a
  hypothetical.
- **Which specific Tier 2 sources can I actually access?** Both documents currently
  describe sources generically. Named sources are stronger. Need to test access to
  Greenhouse/Lever endpoints, USAJOBS, Arbeitnow, Adzuna free tier.
- **What are my success thresholds?** The evaluation plan in `methodology.md` has metrics
  and baselines but thresholds are still unset. Agree these with supervisor *before*
  running the evaluation, not after seeing results.
- **Ethics form for Tier 2 primary data collection** — submitted? NIBM/Coventry process
  and timeline? This is now urgent given the confirmed deadline.
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
| 2026-08-26 | Chapter 3 drafted | Full methodology chapter written, in `Research_Thesis_Draft.md` |
| 2026-08-26/27 | Environment + repository | GitHub repo, Python 3.13.9 venv, full dependency stack; Windows long-path install failure diagnosed and fixed |
| 2026-08-27 | Data audit run and corrected | Three bugs found and fixed (missingness double-counting, duplicate-count mislabeling, inconsistent C1–C6 evaluable definition); all figures verified in two independent environments |
| 2026-08-27 | Stage 1 + API skeleton built | Ingestion loader (9/9 tests passing, verified twice); FastAPI `/score` skeleton with zero fabricated data |
| 2026-08-27 | Stage 2 sampling built | Stratified 200-posting sample + worksheet + coding instructions; reproducibility verified; repo integration not yet confirmed |
| 2026-08-27 | Dataset strategy stress-tested | Four external "second dataset" suggestions checked against primary sources and rejected; two-tier plan reaffirmed |
| 2026-08-27 | Deadline confirmed | ~1 month remaining; scope-cut decision now the most urgent open item |
| 2026-08-27 | `.md` files re-synced | `project.md`, `decisions.md`, `methodology.md`, `sources.md` updated to reflect actual progress after a period of drift |
