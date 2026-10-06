# project.md — An Explainable Credibility Scoring Framework for Online Recruitment Posts

_Last updated: 2026-10-06_

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
- **Key deadlines:** the "~1 month from 2026-08-27" deadline recorded here since August has
  elapsed without an updated submission date ever being logged. **As of 2026-10-06, the
  student states 5 days remain** (operative submission target ~2026-10-11/12). This is the
  deadline this file and `PROJECT_PLAN.md` now plan against, until the exact programme-office
  date is confirmed and logged in its place. **See `PROJECT_PLAN.md` §0 for the full
  day-by-day sprint plan** — it now carries the operational detail that used to live only
  here.

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
| O5 | Evaluation & Generalisability | Evaluate with full metric set, ablation per evidence category, and temporal generalisability on contemporary postings | Must-have (Tier 2 portion now time-boxed to a single day — see the 5-day sprint plan) |

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
  only. Hardware: gaming laptop with an RTX 3050 GPU and 16GB RAM (corrected 2026-09-20;
  previously wrongly assumed to have no GPU). DistilBERT will be fine-tuned, not frozen, as
  a result — **but the installed `torch` is still the CPU build as of 2026-10-06; fixing
  this is the first task of the 5-day sprint, with a logged fallback if it can't be fixed
  quickly.** See `decisions.md`.

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
| Tier 2 | Independently collected contemporary postings | 50–100 target | Held-out temporal validation only. **Never used for training.** Collection is now time-boxed to a single day of the 5-day sprint — see `PROJECT_PLAN.md` §0 and `decisions.md`, 2026-10-06. |

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
- **Phase:** 5-day sprint to completion, started 2026-10-06. **See `PROJECT_PLAN.md` §0 for
  the full day-by-day plan** — it is now the live operational document; this section stays
  as the narrative summary.
- **Completed:**
  - Proposal accepted; objectives finalised; research questions finalised; methodology
    finalised (9 stages + Stage 8b); dataset strategy decided and stress-tested against four
    external alternatives (2026-08-27) and reaffirmed.
  - Chapter 1 (Introduction) and Chapter 2 (Literature Review) drafted in full, with a
    six-theme empirical review and a four-gap research-gap section. Chapter 3 (Methodology)
    also drafted in full.
  - **Environment and repository:** GitHub repo set up, Python 3.13.9 venv with full
    dependency stack installed and verified. **Hardware corrected 2026-09-20:** RTX 3050 +
    16GB RAM, not "no GPU". **Still open as of 2026-10-06: the installed torch is the CPU
    build** — fixing this is the sprint's first task.
  - **Data audit:** run on the real EMSCAD CSV, then corrected twice — a missingness
    double-counting bug, a duplicate-count mislabeling bug (in both the overall and
    per-class figures), and an inconsistent "evaluable coverage" definition across the C1–C6
    rules. All measured figures verified in two independent environments.
  - **Stage 1 (ingestion):** built and tested — 9/9 tests passing against the real dataset,
    confirmed independently on two machines. Committed.
  - **Stage 8 skeleton (API):** FastAPI app, `/score` route, and the full JSON contract
    built and tested. Every pipeline stage honestly reports "not yet built" rather than
    returning fabricated data. Committed. Real wiring is Day 4 of the sprint.
  - **Stage 2 sampling — complete and confirmed committed (2026-09-20):** stratified
    200-posting sample (seed 42, drawn from unique normalised descriptions) built, tested,
    reproduced fresh on the real machine, and pushed to the repository. **The manual coding
    of the 200 postings has not started — that's Day 1–2 of the sprint, and it stays at
    200 postings; the student was explicit this is not to be cut for time.**
  - **Docs sync (2026-09-20):** `project.md`, `decisions.md`, `methodology.md`, `sources.md`
    and `PROJECT_PLAN.md` are now consistent across the Claude Project, the GitHub repo, and
    reality. `workplan.md` retired in favour of `PROJECT_PLAN.md`.
  - **Scope-cut decisions made (2026-09-20):** rules-only baseline cut; DistilBERT will be
    fine-tuned (enabled by the hardware correction); Tier 2 reduced to ~50–100 postings;
    seeds reduced to 3; explainability narrowed to SHAP only; divergent architecture review
    formally skipped, time-driven. Near-duplicate grouping (Decision 0.2) resolved: MD5
    hashing plus a secondary title-based grouping key. Full reasoning in `decisions.md`.
  - **5-day sprint compression (2026-10-06):** deadline corrected; Tier 2 further time-boxed
    to a single day; ablation seed count made conditional on a Day 3 timing measurement;
    triage order fixed in advance; manual audit explicitly protected at 200 postings. Full
    reasoning in `decisions.md`, 2026-10-06; full schedule in `PROJECT_PLAN.md` §0.
- **Not yet started:** the Stage 2 manual audit. Tier 2 collection (zero postings). Stages
  3–9 in full. Chapters 4–6 of the dissertation (Chapter 4 cannot be drafted until Stage 9
  produces real measurements — now scheduled for Day 4–5 of the sprint).

### Known state of documents

- `Research_Methodology_Final.docx` still shows the *original estimated* C1–C6 field
  coverage figures (100%/98%/81%/61%/55%/16%), not the measured ones (100%/88.4%/80.6%/
  60.6%/54.7%/15.2%), and has no evaluable-coverage column at all. Also still states "no
  dedicated GPU" as a constraint, and the Threats-to-Validity table still says "five-seed
  repetition". Needs updating — likely after the sprint, not during it, unless a spare hour
  appears.
- All numeric values in `Framework_Explanation_Walkthrough.docx` are illustrative worked
  examples, not results. Logged as `sources.md` #17. Never cite them.
- Chapters 1 and 2 cite 11 sources; several are still unread/unverified — tracked in
  `sources.md` Part C. Must be read before final submission; realistically this is a
  post-sprint task unless the 5 days leave slack.

### Next actions (in order)

See `PROJECT_PLAN.md` §0.5 for the full day-by-day breakdown. In short:

1. **Tonight:** confirm CUDA works, or start the fallback install.
2. **Day 1:** resolve Decisions 0.3 and 0.4; build Stage 3; start the manual audit; push on
   Tier 2 with an end-of-day checkpoint.
3. **Day 2:** finish the manual audit; build Stage 4 (real E1–E4, real lexicons, real C2).
4. **Day 3:** train baseline + improved models; decide the ablation seed count from a real
   timing; build Stage 6 (calibration).
5. **Day 4:** build Stage 7 (SHAP); wire Stage 8 for real; run Stage 8b and Stage 9 once.
6. **Day 5:** write Chapters 4–6, the AI-use declaration, and sync every `.md` file; the
   research paper only if time remains.

---

## Open questions

- **Tier 2 collection is time-boxed to Day 1 of the sprint** (compressed from the 1-week
  checkpoint decided 2026-09-20) — see `decisions.md`, 2026-10-06.
- **Which specific Tier 2 sources can I actually access?** Greenhouse/Lever endpoints
  verified; USAJOBS, Arbeitnow, Adzuna free tier verified (2026-09-20). Fraud-side sourcing
  is Day 1's main open question.
- **What are my success thresholds?** Still unset in `methodology.md`. Agree with
  supervisor if any contact window exists this week; otherwise state as a self-set
  limitation in Chapter 5.
- **Ethics form for Tier 2 primary data collection** — status unconfirmed. **Explicitly not
  gating collection this week** (student's direct instruction, 2026-10-06) — this must still
  be named as a disclosed limitation in Chapter 6, not silently omitted.
- **Decisions 0.3 and 0.4** — both resolve Day 1 morning of the sprint, before Stage 4 design
  and Tier 2 sourcing proceed.
- **AI-use declaration** — what wording does my programme require, and where does it go?
  Write Day 5.
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
| 2026-10-06 | Deadline corrected; 5-day sprint plan written | The ~1 month deadline had elapsed with no updated date logged. Student confirmed 5 days remain. `PROJECT_PLAN.md` rewritten with a full Day 0–5 schedule; `decisions.md` logs the compression decisions (Tier 2 time-boxed to Day 1, ablation seed count made conditional, triage order fixed in advance, manual audit explicitly protected at 200 postings). |
