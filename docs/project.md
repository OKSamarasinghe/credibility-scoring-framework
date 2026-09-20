# project.md — An Explainable Credibility Scoring Framework for Online Recruitment Posts

_Last updated: 2026-09-20_

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
- **Hard constraints:** single developer; no paid data sources; English-language postings
  only. **Corrected 2026-09-20:** "consumer-grade hardware, no dedicated GPU" was assumed
  since proposal stage and never checked — actual hardware is a gaming laptop with an
  RTX 3050 GPU and 16GB RAM. DistilBERT will be fine-tuned, not frozen, as a result. See
  `decisions.md`, 2026-09-20.

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

- **DSR step:** 3 (Design & Build) — genuinely into implementation, with real, tested,
  committed code — not just at the transition.
- **Phase:** Dissertation write-up (Chapters 1–3 drafted, in `Research_Thesis_Draft.md`) AND
  artefact build, running in parallel. **Deadline confirmed: ~1 month from 2026-08-27.**
- **Completed:**
  - Proposal accepted; objectives finalised; research questions finalised; methodology
    finalised (9 stages + Stage 8b); dataset strategy decided and stress-tested against four
    external alternatives (2026-08-27) and reaffirmed.
  - Chapter 1 (Introduction) and Chapter 2 (Literature Review) drafted in full, with a
    six-theme empirical review and a four-gap research-gap section. Chapter 3 (Methodology)
    also drafted in full.
  - **Environment and repository:** GitHub repo set up, Python 3.13.9 venv with full
    dependency stack installed and verified (including resolving a Windows long-path
    install failure for PyTorch). **Hardware corrected 2026-09-20:** RTX 3050 + 16GB RAM,
    not "no GPU" as previously assumed throughout the project files.
  - **Data audit:** run on the real EMSCAD CSV, then corrected twice — a missingness
    double-counting bug, a duplicate-count mislabeling bug (in both the overall and
    per-class figures), and an inconsistent "evaluable coverage" definition across the C1–C6
    rules. All measured figures verified in two independent environments.
  - **Stage 1 (ingestion):** built and tested — 9/9 tests passing against the real dataset,
    confirmed independently on two machines. Committed.
  - **Stage 8 skeleton (API):** FastAPI app, `/score` route, and the full JSON contract
    built and tested. Every pipeline stage honestly reports "not yet built" rather than
    returning fabricated data. Committed. Real wiring still pending Stages 4–7.
  - **Stage 2 sampling — complete and confirmed committed (2026-09-20):** stratified
    200-posting sample (seed 42, drawn from unique normalised descriptions) built, tested,
    reproduced fresh on the real machine, and pushed to the repository. The manual coding of
    the 200 postings (the actual audit) has not started — that part is human work only I
    can do.
  - **Docs sync (2026-09-20):** `project.md`, `decisions.md`, `methodology.md`, `sources.md`
    and `PROJECT_PLAN.md` are now consistent across the Claude Project, the GitHub repo, and
    reality. `workplan.md` retired in favour of `PROJECT_PLAN.md`.
  - **Scope-cut decisions made (2026-09-20):** rules-only baseline cut; DistilBERT will be
    fine-tuned (enabled by the hardware correction); Tier 2 reduced to ~50–100 postings with
    a ~1-week checkpoint; seeds reduced to 3 with the "what does N seeds mean" question
    settled (fixed split, N initialisations); explainability narrowed to SHAP only;
    divergent architecture review formally skipped, time-driven. Near-duplicate grouping
    (Decision 0.2) resolved: MD5 hashing plus a secondary title-based grouping key. Full
    reasoning for all of this in `decisions.md`, 2026-09-20.
- **Not yet started:** the Stage 2 manual audit itself. Tier 2 collection (zero postings —
  sourcing starts now, in parallel, with the checkpoint above). Stages 3–9 in full. Chapters
  4–6 of the dissertation (Chapter 4 cannot be drafted until Stage 9 produces real
  measurements).

### Known state of documents

- `Research_Methodology_Final.docx` still shows the *original estimated* C1–C6 field
  coverage figures (100%/98%/81%/61%/55%/16%), not the measured ones (100%/88.4%/80.6%/
  60.6%/54.7%/15.2%), and has no evaluable-coverage column at all. Also still states "no
  dedicated GPU" as a constraint. Needs updating.
- All numeric values in `Framework_Explanation_Walkthrough.docx` are illustrative worked
  examples, not results. Logged as `sources.md` #17. Never cite them.
- Chapters 1 and 2 cite 11 sources; several are still unread/unverified — tracked in
  `sources.md` Part C. Must be read before final submission.

### Next actions (in order)

1. **Start the Stage 2 manual audit** — 200 postings, using the pre-defined coding scheme
   in `STAGE2_CODING_INSTRUCTIONS.md`. This is human work only I can do, and it's the
   longest-pole item still blocking Stage 3.
2. **Start Tier 2 sourcing in parallel, today** — target 20–30 verified fraudulent postings
   within ~1 week (checkpoint; falls back to qualitative-only if missed) and 30–50
   legitimate postings.
3. **Check Tier 2 ethics approval status** — has it actually been submitted? Do this today,
   not as a background task.
4. **Build Stage 3** (partitioning) once the Stage 2 audit and Decision 0.2's title+
   description grouping are both ready.
5. **Schedule the success-thresholds conversation with my supervisor** — must happen before
   Stage 9, and the deadline makes "before Stage 9" mean "soon."
6. **Read the unverified Chapter 1–2 sources** (sources.md Part C) — especially Vidros
   (2017), Mehboob & Malik (2021), Sullivan & Weger (2025) — as time allows.

---

## Open questions

- **Tier 2 collection has now started sourcing**, with a firm ~1-week checkpoint (see
  `decisions.md`, 2026-09-20). This is no longer an abstract risk — it's an active,
  time-boxed task.
- **Which specific Tier 2 sources can I actually access?** Need to test access to
  Greenhouse/Lever endpoints, USAJOBS, Arbeitnow, Adzuna free tier — now urgent, not
  background research.
- **What are my success thresholds?** Still unset in `methodology.md`. Agree these with
  supervisor *before* running the evaluation, not after seeing results. Urgent given the
  deadline.
- **Ethics form for Tier 2 primary data collection** — submitted? Check today.
- **AI-use declaration** — what wording does my programme require, and where does it go?
- **Chapter 1 explainability wording** — confirm Chapter 1 says explanations are "rarely
  used and never tested for faithfulness" rather than "absent", so it agrees with Chapter 2
  (which cites Naudé 2023 using LIME in the fraud domain). Sharpened gap, must be consistent
  across both chapters.
- **LIME references in `Research_Objectives_and_Questions_Final.docx` and the thesis draft**
  — since Stage 7 now uses SHAP only, check that "e.g., SHAP, LIME" wording doesn't read as
  a firm commitment to both methods anywhere it's cited.

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
| 2026-08-27 | `.md` files re-synced (first pass) | `project.md`, `decisions.md`, `methodology.md`, `sources.md` updated to reflect actual progress after a period of drift |
| 2026-09-20 | Docs sync verified and completed | Confirmed via repo inspection that the first-pass sync had only reached the Claude Project, not the GitHub repo; corrected. `PROJECT_PLAN.md` added to repo; `workplan.md` retired. Commit `272c70c`. |
| 2026-09-20 | Stage 2 sampling committed | Third attempt; verified this time — files landed with correct sizes, script re-ran and reproduced the exact sample on the real machine, then committed. Commit `498200d`. |
| 2026-09-20 | Hardware constraint corrected | "No GPU" was wrong — RTX 3050 + 16GB RAM. Resolves the frozen-vs-fine-tuned DistilBERT question. |
| 2026-09-20 | Scope-cut decisions made | Rules-only baseline cut; DistilBERT fine-tuned; Tier 2 reduced to ~50–100 postings with a 1-week checkpoint; seeds reduced to 3 with the definition settled; explainability narrowed to SHAP only; architecture review formally skipped. Decision 0.2 resolved (MD5 + title grouping). Full reasoning in `decisions.md`. |
