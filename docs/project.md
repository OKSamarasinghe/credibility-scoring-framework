# project.md — An Explainable Credibility Scoring Framework for Online Recruitment Posts

_Last updated: 2026-10-09_

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

## Research objectives (v4 — finalised 2026-10-09, supersedes v3)

Plain-language rewording of v3 for the thesis's 1.3 section, checked sentence-by-sentence
against what was actually built and evaluated before being accepted — see `decisions.md`,
2026-10-09, "Research objectives and questions reworded to v4". No substance changed except
RQ3, which was reworded for precision (see that entry for why).

| # | Label | Statement (short form) | Type |
|---|---|---|---|
| O1 | Evidence Taxonomy | Define a structured set of credibility evidence categories for online job postings, validated by manually reviewing a sample of postings from the benchmark dataset | Must-have |
| O2 | Baseline Model | Build and test a baseline fraud-detection model using standard text-based machine learning methods, trained on a carefully split, leakage-controlled dataset, and compare its results with those reported in earlier published studies | Must-have |
| O3 | Multi-Signal Model | Build an improved model combining a more advanced text-understanding method with the defined evidence categories and consistency checks, and measure how much this changes fraud-detection performance compared with the baseline model, under matched training conditions | Must-have |
| O4 | Explainable Decision Module | Design an explainable decision module that turns the model's output into a clear credibility score with defined risk levels, supported by reasons generated automatically and checked against fixed rules | Must-have |
| O5 | Evaluation & Generalisability | Evaluate the complete framework using standard performance and calibration testing, check whether its explanations genuinely reflect the model's decisions, measure how much each evidence category contributes through ablation analysis, and test how well the framework performs on a newly collected, independent set of recent job postings | Must-have — **complete, 2026-10-08**: full metric set, calibration, explanation-faithfulness check, ablation, and Tier 2 temporal transfer all run once; see "Where I am right now" |

Full statements: see `Research_Objectives_and_Questions_Final.docx` — **needs updating to
v4 wording; still shows v3 as of 2026-10-09.**

**Rule I am holding myself to:** no objective states its own expected result. O3 quantifies
the *extent of change*, not an improvement. A negative finding still completes the objective.

## Research questions (v4 — finalised 2026-10-09, supersedes v3)

- **RQ1** — What types of information can be reliably taken from online job postings to support a credibility assessment?
- **RQ2** — How effective is a baseline text-based model at detecting fraudulent postings under leakage-controlled testing, and how do its results compare with those of earlier published studies?
- **RQ3** — To what extent does combining a more advanced text-understanding method with structured evidence features and consistency checks change fraud-detection performance, compared with the baseline model, under matched conditions?
- **RQ4** — How can model-based explanations and rule-based summaries be combined to produce a credibility score with reasons that are both faithful to the model and easy for a user to understand?
- **RQ5** — How well does the complete framework perform under standard predictive, calibration and ablation testing, and how well does it perform on a set of recent job postings?

**RQ3 note:** the v3 wording ("adding...to a transformer-based representation") was
ambiguous between two different comparisons — against the O2 baseline (already measured,
Stage 9 Part 1) or against a transformer-only/zero-evidence ablation (never run; Stage 9's
leave-one-category-out ablation removes categories one at a time, not all four at once).
v4 is worded to match only the comparison that was actually run. See `decisions.md`,
2026-10-09, for the full reasoning.

---

## The artefact

- **What it is:** a backend REST API (FastAPI) exposing a `/score` endpoint.
- **What it does:** accepts a job posting (raw text primary, plus any structured EMSCAD
  fields the caller can supply — salary_range, employment_type, etc.; URL best-effort
  secondary), runs preprocessing → multi-signal evidence extraction → prediction →
  calibration → explanation, and returns structured JSON. See decisions.md, 2026-10-08,
  for why text-only would have left E3/E4 permanently dark on every live request.
- **Response fields:** `credibility_score` (0–100), `risk_band`, `top_reasons`,
  `suspicious_phrases`, `contradictions`, `verification_checklist`.
- **Hard constraints:** single developer; no paid data sources; English-language postings
  only. Hardware: gaming laptop with an RTX 3050 GPU and 16GB RAM (corrected 2026-09-20;
  previously wrongly assumed to have no GPU). DistilBERT will be fine-tuned, not frozen, as
  a result. CUDA build confirmed working 2026-10-06. See `decisions.md`.

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
| Tier 2 | Independently collected contemporary postings | **130 legitimate (Greenhouse/Lever) + 24 fraudulent (BBB Scam Tracker) = 154 total, both sides collected 2026-10-07** | Held-out temporal validation only. **Never used for training.** Collection is now closed — see `decisions.md`, 2026-10-07. |

> **Confirmed 2026-08-27:** four externally-suggested "second datasets" (a Kaggle 2026
> competition, DIFrauD's Job Scams split, the Internship-Job-Scam-Dataset, ScamShield) were
> checked against their primary sources and found to all be EMSCAD derivatives — none
> provide independent, contemporary, metadata-rich data. See `decisions.md`, 2026-08-27.

> **Tier 2 asymmetry, stated plainly:** 130 legitimate vs. 24 fraudulent (5.4:1) is a
> different ratio from EMSCAD's own 19.6:1 legitimate:fraud split, and the two sides were
> collected from structurally different sources (a public API vs. a consumer-complaint
> database), so Tier 2's structured-field richness is asymmetric by source, not by fraud
> status — see Decision 0.4 in `decisions.md`. This must be stated plainly wherever Tier 2
> results are reported, not smoothed over.

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
- **Phase:** 5-day sprint to completion, started 2026-10-06, now in Day 2
  (2026-10-08). **See `PROJECT_PLAN.md` §0 for the full day-by-day plan** — it is now the
  live operational document; this section stays as the narrative summary.
- **Completed:**
  - Proposal accepted; objectives finalised; research questions finalised; methodology
    finalised (9 stages + Stage 8b); dataset strategy decided and stress-tested against four
    external alternatives (2026-08-27) and reaffirmed.
  - Chapter 1 (Introduction) and Chapter 2 (Literature Review) drafted in full, with a
    six-theme empirical review and a four-gap research-gap section. Chapter 3 (Methodology)
    also drafted in full.
  - **Environment and repository:** GitHub repo set up, Python 3.13.9 venv with full
    dependency stack installed and verified. **Hardware corrected 2026-09-20:** RTX 3050 +
    16GB RAM, not "no GPU". **Resolved 2026-10-06, 22:56:** `torch` reinstalled as the CUDA
    build (`2.6.0+cu124`); `torch.cuda.is_available()` confirmed `True` against the RTX
    3050 on the first attempt — no fallback needed.
  - **Decisions 0.3 and 0.4 resolved (2026-10-06, 23:50):** C6 defined as a presence/
    structure check requiring no label-conditioned threshold; Tier 2 field-symmetry handled
    by sourcing preference + disclosed-limitation reporting + the existing source-probe
    leakage test. Full reasoning in `decisions.md`.
  - **Stage 3 (leakage-controlled partitioning) — built, bug found and fixed, verified,
    committed (2026-10-06/07):** group-aware stratified 70/15/15 split. Implementing
    Decision 0.2 exactly as logged (description-hash UNION title-hash) produced a badly
    over-merged result (56.68% of the corpus in a duplicate group, caught by a 15-largest-
    group diagnostic before committing); reverted to description-hash-only grouping the same
    night, which exactly reproduces the already-verified August audit figures (4,762
    duplicate records / 26.63%, zero train/val/test group overlap, fraud rate preserved
    across all three splits). Logged as a correction in `decisions.md`, not a silent fix.
    9/9 tests passing. Committed (`b5a45aa`).
  - **Tier 2 legitimate-side sourcing — built, run, verified, committed (2026-10-07):**
    self-validating script against the public Greenhouse/Lever APIs collected 130 postings
    from 26 real companies (24 Greenhouse, 2 Lever), well above the 30–50 target. Kept in
    full — see `decisions.md`. Committed (`5545d37`).
  - **Tier 2 fraud-side sourcing — collected and provenance-verified, 2026-10-07:** 24
    postings from BBB Scam Tracker's "employment" search, read via Claude in Chrome after
    the development machine was linked and the extension installed. Each record carries a
    verified unique permalink (BBB's own `aria-labelledby` DOM attribute confirms the
    report-ID-to-URL mapping, not an assumption). Written to
    `data/raw/tier2/tier2_fraud_raw.jsonl` — EMSCAD-shaped structured fields left `null`
    (per Decision 0.4's outcome: BBB documents almost no structured fields), BBB-specific
    provenance kept in separate `bbb_*` fields. A source-side near-duplicate pattern (one
    report filed under 3+ distinct Scam IDs) was found and logged as a limitation. Full
    detail in `decisions.md` and `sources.md` item #20. **Tier 2 collection is now fully
    closed — both sides met or exceeded target within the Day 1 time-box.** **Correction,
    2026-10-07 evening:** this file is NOT pending a commit — `data/raw/` is gitignored
    wholesale (confirmed via `git check-ignore`), and the legitimate-side file
    (`tier2_legit_raw.jsonl`) was never committed either, for the same reason. Raw postings
    stay local-only by existing repo policy; only the derived summaries/scripts
    (`reports/tier2_sourcing_summary.json`, `src/ingestion/tier2_sourcing.py`) are tracked.
    An earlier session log wrongly treated this as an open commit item — corrected here,
    not silently.
  - **Git commit-attribution fix — ✅ RESOLVED, 2026-10-07 evening:** the three commits
    (`b5a45aa`, `5545d37`, `6e391b4`) were rewritten on a new branch (`attribution-fix`)
    built from their shared parent — cherry-picked in order, each amended to strip the
    `Co-Authored-By: Claude` / `Claude-Session:` trailer lines while keeping the original
    author, email, and commit/author dates unchanged. Verified: `git diff` between each old
    and new commit's tree is empty (identical content, message only changed), and a trailer
    scan across the rewritten range (`af25cb5..a39f441`) returns nothing. A safety branch
    (`backup-pre-attribution-fix`) was created pointing at the old history before rewriting,
    in case of need to revert. **Pushed and confirmed, 2026-10-07 23:31** — the linked
    machine's isolated Linux shell (`device_bash`) has no stored GitHub credentials (it's a
    separate sandboxed VM from the Windows host's own credential manager), so the student
    ran `git push --force-with-lease origin main` from their own terminal; GitHub accepted
    it: `6e391b4...09bece3 main -> main (forced update)`. The remote `main` tip is now the
    clean, trailer-free history. Full write-up in `decisions.md`.
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
    of the 200 postings has not started — this is now the single most time-critical
    unstarted task (see "Next actions").**
  - **Docs sync (2026-10-07):** `project.md`, `decisions.md`, `sources.md` updated to
    reflect today's Tier 2 fraud-side close-out; synced to both the Claude Project and the
    GitHub repo `docs/` folder in the same pass (no stale duplicate left in either place).
  - **Scope-cut decisions made (2026-09-20):** rules-only baseline cut; DistilBERT will be
    fine-tuned (enabled by the hardware correction); Tier 2 reduced to ~50–100 postings;
    seeds reduced to 3; explainability narrowed to SHAP only; divergent architecture review
    formally skipped, time-driven. Near-duplicate grouping (Decision 0.2) resolved: MD5
    hashing plus a secondary title-based grouping key. Full reasoning in `decisions.md`.
  - **5-day sprint compression (2026-10-06):** deadline corrected; Tier 2 further time-boxed
    to a single day; ablation seed count made conditional on a Day 3 timing measurement;
    triage order fixed in advance; manual audit explicitly protected at 200 postings. Full
    reasoning in `decisions.md`, 2026-10-06; full schedule in `PROJECT_PLAN.md` §0.
- **Stage 2 manual audit — complete, 2026-10-08:** all 200 postings coded by hand,
  committed `57da423`. Per-category observability and per-rule agreement rates measured;
  one signal revised (the field-presence NaN-handling bug, caught twice). Full detail in
  `methodology.md`'s "Taxonomy validation (O1)".
- **Stages 4 through 9 — all complete, built, run, and committed, 2026-10-08.** The whole
  5-day sprint's technical core finished in a single day, well ahead of the Day 3/4 pacing
  `PROJECT_PLAN.md` originally planned — not something to read back into the plan as if it
  were expected; it is logged here as what actually happened.
  - **Stage 4 (multi-signal evidence extraction):** E1-E4 built, run on the full corpus
    (n=17,880), four precision bugs found and fixed before any coverage figure was reported.
    Committed `ff6872f`.
  - **Stage 5 (baseline + multi-signal models):** TF-IDF+LogReg/RF baselines and the
    DistilBERT+structured-evidence fusion model trained, 3 seeds each. DistilBERT+evidence
    beats both baselines on validation (F1 0.671±0.030). Epoch count resolved from a real
    6-epoch probe (peaked at epoch 4), not guessed. Ablation seed count closed at 1/arm from
    measured per-epoch timing. Committed `04eaeb0`, `628857d`.
  - **Stage 6 (calibration):** isotonic selected over Platt (Brier 0.0199 vs. 0.0212 on
    validation), with an explicit caveat that isotonic's near-zero ECE is partly a
    same-set-fit artefact, not re-litigated once Stage 9 reports test-set calibration.
    Committed `e28520e`.
  - **Stage 7 (explainability):** SHAP (KernelExplainer, scoped to the 46 structured
    E1-E4 features), run in logit space after the first probability-space run was found to
    be saturation-compressed. SHAP beats a random-ranking control at every k tested; rule-
    consistency 100% (14/14, Wilson 95% CI [0.785, 1.000]), reported with the sparse-feature
    SHAP-inflation caveat attached, not as an unqualified result. Committed `d940ea3`.
  - **Stage 8 / 8b (API wiring + demonstration):** `src/api/pipeline.py` wires the real
    Stage 1/4/5/6/7 code behind `/score`. Two real bugs caught by the first smoke test and
    fixed: a missing structured-field input contract, and a direction-inverted
    `credibility_score` (was reporting P(fraud), not P(credible)). Stage 8b ran 3 real Tier 2
    postings through the live pipeline via a pre-registered, content-blind selection rule;
    two of the three explanations came back near-identical, investigated and confirmed as the
    already-logged Decision 0.4 field-asymmetry risk actually showing up, not a bug.
    Committed `ada4c94`.
  - **Stage 9 (evaluation), Parts 1-3 — the project's one-time, now-closed test-set
    touch:** Part 1 — baselines (3 seeds, refit for parity) + main model (3 seeds)
    evaluated once on the EMSCAD test split; multi-signal model beats both baselines on F1,
    beats LogReg but not RF on PR-AUC (a genuine validation-to-test reversal, reported
    honestly). Part 2 — leave-one-category-out ablation (5 arms, 1 seed/arm per the Day-3
    budget decision); all four evidence categories lower F1 when removed, `has_company_logo`
    improves both F1 and PR-AUC on removal (supports the pre-registered suspicion it's a
    dataset-construction artefact, not shipped-on now per the "test used once" guardrail).
    Part 3 — Tier 2 temporal transfer (T1/T2/T3) and the source-probe leakage test, all run
    on the real 154-posting Tier 2 set. **The source-probe came back at a perfect
    ROC-AUC=1.0000** — investigated with `device_bash` rather than accepted at face value,
    and confirmed as a Tier-2-collection-wide structured-field missingness artefact
    (EMSCAD's `has_company_logo`/`has_questions` are 0% missing; all 154 Tier 2 postings,
    fraud AND legit alike, are 100% missing on both) — bigger in scope than Decision 0.4
    anticipated. Full numbers in `methodology.md`'s "Tier 2 (O5)"; addendum in
    `decisions.md`, Decision 0.4. T1/T2/T3's individual numbers are reported with an
    explicit small-sample-instability caveat (n=154, 24 fraud) rather than read at face
    value. Committed `e81fab5`, `3cc02b3`.
  - Per the Stage 9 design decision logged before any test number was seen: **no further
    model, feature, seed, or architecture change is permitted for the rest of this
    project** — Stage 9's numbers are final.
- **Live end-to-end API test — complete, 2026-10-08.** Ran a real `uvicorn` server and
  sent the same 3 Stage 8b postings (clear fraud, clear legit, ambiguous) over actual HTTP,
  via `src/api/live_api_check.py`. All 3 live responses matched Stage 8b's already-verified
  `credibility_score`/`risk_band` exactly — confirms the request parsing, routing, and
  response serialization are wired correctly, not just the pipeline logic in isolation
  (Stage 8b only ever called it in-process). Results: `reports/stage_live_api_check_results.json`.
  **Full automated test suite also re-run and confirmed, 2026-10-08: 51/51 tests passing**
  (`test_extract_features.py`, `test_load_emscad.py`, `test_split_data.py`) — every stage's
  unit tests pass together, not just individually as each was built.
- **The artefact itself (the backend credibility-scoring API) is now fully built, trained,
  evaluated, and verified end-to-end.** Nothing technical remains outstanding.
- **Frontend UI added, iterated, tested, and committed -- 2026-10-09.** Reopens the
  "backend API only" line in Scope on purpose, logged as a decision (see `decisions.md`,
  2026-10-09, plus two addenda) rather than by drift. `frontend/index.html` -- a
  self-contained static page, no build step, no new Python dependency -- served via one
  new additive route (`GET /` in `src/api/main.py`). Three passes: (1) a minimal
  manual-entry form, zero auto-parsing, confirmed working end-to-end by the student
  (real pasted posting scored correctly); (2) a visual redesign for polish and mobile
  responsiveness; (3) a naming/copy/attribution pass -- named **JobCred**, footer credits
  "Developed by Oshadha Samarasinghe, Coventry University - 16116041, NIBM -
  COBSCCOMP242P-069". Every pass verified structurally (no duplicate element ids, balanced
  tags, every id the JS reads present in the markup) and confirmed the `<script>` block
  (field collection, omit-if-empty payload logic, the `/score` call) byte-identical across
  all three versions before deploying. `/score`, `/health`, `pipeline.py`, and every
  trained-model code path are untouched. Student confirmed it working, committed, and
  pushed.
- **URL and screenshot/OCR input built, 2026-10-09 (same day, after being deferred
  earlier that day):** two new, purely additive FastAPI routes, `POST /extract-url` and
  `POST /extract-image`, plus two new schemas (`UrlExtractRequest`, `ExtractResponse`).
  Both only ever return extracted text (and title, for URL) for the frontend to drop into
  the existing `text`/`title` fields for review -- nothing is auto-submitted, and neither
  route touches `/score`, `ScoreRequest.url`'s still-unimplemented 501 stub, `pipeline.py`,
  or any trained-model code. This does NOT reopen the 2026-08-07 "raw text is the primary
  input" decision -- `/score` still only accepts text; these are pre-fill conveniences in
  front of that same box, not a second path into the model. URL fetching
  (`trafilatura`) checks each site's own `robots.txt` at request time, plus two hardcoded
  exclusions (LinkedIn -- client-side-rendered pages, and ToS; topjobs.lk -- added after
  real testing showed the robots.txt check alone didn't reliably catch it, see below), plus
  a content-quality guard that rejects extracted text that's too short or matches known
  "enable JavaScript" placeholder phrases (added after real testing caught xpress.jobs
  returning exactly that string as if it were a valid posting). OCR (`pytesseract` + the
  system Tesseract binary) was chosen over `easyocr` after testing directly against all 8
  of the student's real example job-ad images with clean, legible results; on the real
  Windows machine, `pytesseract` needed a fallback to the installer's default path because
  the UB-Mannheim Tesseract installer doesn't add itself to PATH (now handled in code, no
  manual PATH edit needed). All of the above logged in full in `decisions.md`,
  2026-10-09, "URL and screenshot input added as pre-fill conveniences" and its four
  addenda (the dependency-conflict fix, the Tesseract-PATH fix, and two real-world test
  rounds). **Real-world URL testing is now done, by the student, with real internet access
  -- something Claude could never do itself** (every fetch tool available to Claude is
  blocked from reaching external sites by its own outbound proxy). Across **13 real job
  sites**: **8 extracted cleanly** (ikman.lk, finders.lk, rooster.jobs, jobpal.lk,
  jobeka.lk, itpro.lk, dreamjobs.lk, plus skyjobs.lk via the screenshot/OCR fallback when
  URL extraction alone wasn't enough -- a genuine demonstration of why both features exist,
  not just one); **4 correctly declined** (LinkedIn, topjobs.lk, xpress.jobs, and
  unjobs.org -- the last caught by the general robots.txt mechanism on its own, with no
  special-casing, which is good evidence that mechanism does generally work); **1 failed
  gracefully** (Indeed -- clear "could not reach / site blocked" message, not a crash).
  **The honest claim for the write-up:** broad coverage across real local job boards,
  clean/non-crashing behaviour on the rest -- not "works on every site," which was never
  the goal (per the student's own framing: "Dont need to work for all websites"). Frontend
  UI added (a URL box + Fetch button, a file input + Extract button), verified
  structurally (no duplicate ids, balanced tags, the existing submit handler/
  `buildPayload`/`renderResults` confirmed byte-identical before and after).
  `requirements.txt` updated
  (`trafilatura==2.3.1`, `pytesseract==0.3.13`, `python-multipart==0.0.32`, plus
  `trafilatura`'s own transitive dependencies, and three existing pins bumped to satisfy
  it -- see `decisions.md` addendum) --
  **student still needs to `pip install -r requirements.txt` and install the Tesseract
  OCR binary on Windows before either feature works on their machine; see "Next
  actions."**
- **Not yet started (writing, not development):** Chapters 4-6 of the dissertation (Chapter
  4 can now be drafted — Stage 9's real measurements exist); the AI-use declaration; the
  research paper (stretch goal, named first to go if time runs out).

### Next actions (in order)

1. ~~Install dependencies + Tesseract OCR binary~~ — ✅ done, 2026-10-09 (one real
   dependency conflict and one PATH issue hit and fixed along the way; see `decisions.md`).
2. ~~Live URL/OCR testing with real internet access~~ — ✅ done, 2026-10-09, well beyond
   the original 6 URLs (13 real sites tested; 8 clean, 4 correctly declined, 1 graceful
   failure). Two real bugs this testing caught were fixed same-day (topjobs.lk slipping
   through, xpress.jobs returning a JS-placeholder as if it were real text). Full results
   in `decisions.md`.
3. **Delete two harmless leftover debug files** in the project root
   (`req_utf8_debug.txt`, `req_final_check_debug.txt` — Claude couldn't delete them
   itself, permission-gated) before committing; don't stage them.
4. **Commit and push** (student commits, not Claude). **Development is now fully
   complete, including both extra input features, live-tested with real data.**
5. **Chapter 4 (Results)** — can be drafted now; every number it needs exists in
   `methodology.md`. Write from the measured tables only, not from memory of what was
   expected.
6. **Chapter 5 (Discussion)** — interpret Stage 9's honestly-reported findings (the RF
   PR-AUC reversal, the ablation's noise-indistinguishable PR-AUC pattern, the Tier 2
   source-probe artefact and what it does and doesn't undermine, the `has_company_logo`
   finding). State the self-set-thresholds limitation here if no supervisor contact window
   opens this week — **open question, needs an answer before this chapter is written.**
7. **Chapter 6 (Conclusion)** — contributions, and limitations named plainly: the Tier 2
   source-asymmetry/missingness artefact, the Tier 2 ethics-approval status (still open),
   the E2 contact-token inertness on live text, the 70/15/15-split-not-nested-CV trade-off,
   the un-reviewed architecture choice. The URL/OCR pre-fill features can be described
   honestly now with real numbers (8/13 sites), not as a caveat about unverified behaviour.
8. **AI-use declaration** — programme-required; write once the wording/placement
   requirement is confirmed. Must now also cover this session's URL/OCR feature work
   (including the bugs Claude introduced and fixed, and the ones the student's own testing
   caught that Claude had missed).
9. **Research paper** — stretch goal only, per the triage order fixed 2026-10-06.

---

## Open questions

- **Tier 2 collection and evaluation — ✅ CLOSED, 2026-10-08.** Both sides collected within
  the Day 1 time-box (130 legitimate / 24 fraudulent); Stage 9 Part 3 ran the full
  154-posting temporal-transfer and source-probe evaluation on 2026-10-08. See
  `decisions.md`, 2026-10-07 and 2026-10-08.
- **Tier 2 source-probe: structured-field collection artefact, confirmed — stated here as
  a real limitation, not a pending question.** The source-probe scored a perfect
  ROC-AUC=1.0000 distinguishing EMSCAD from Tier 2 on structured features alone, root-caused
  to Tier 2's raw collection never capturing 9 of EMSCAD's structured fields, across both
  fraud and legit postings alike (bigger in scope than Decision 0.4 anticipated — see its
  2026-10-08 addendum). This must appear as a named limitation in Chapter 6, and T1/T2/T3's
  absolute numbers in Chapter 4/5 must carry this caveat rather than be read at face value.
- **What are my success thresholds? Still genuinely open — needs an answer before Chapter 5
  is drafted.** Has any supervisor contact happened since 2026-10-06? If yes, log the
  agreed thresholds here and in `methodology.md`. If no, Chapter 5 states plainly that
  thresholds were self-set under time pressure, per the fallback already agreed
  (`decisions.md`, Stage 9 design decisions, 2026-10-08).
- **Ethics form for Tier 2 primary data collection** — status unconfirmed. **Explicitly not
  gating collection this week** (student's direct instruction, 2026-10-06) — this must still
  be named as a disclosed limitation in Chapter 6, not silently omitted.
- **Git commit attribution — ✅ CLOSED, 2026-10-07 23:31.** The three commits (`b5a45aa`,
  `5545d37`, `6e391b4`) were replayed with the `Co-Authored-By: Claude` / `Claude-Session:`
  trailers stripped (author, email, and dates preserved; tree contents verified identical
  to the originals). Student ran `git push --force-with-lease origin main` from their own
  terminal; GitHub confirmed `6e391b4...09bece3 main -> main (forced update)` — the remote
  `main` tip is now the clean history. A safety branch `backup-pre-attribution-fix`
  (pointing at the old, trailer-carrying history, local-only, never pushed) remains in the
  repo in case of need to compare or revert later; it costs nothing to leave in place.
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
| 2026-10-06/07 (overnight) | CUDA fixed; Decisions 0.3/0.4 resolved; Stage 3 built and fixed; Tier 2 legit-side sourced | `torch` reinstalled as CUDA build, confirmed working. Decisions 0.3 (C6 presence-only, no label-conditioned threshold) and 0.4 (Tier 2 field symmetry) resolved. Stage 3 partitioning built, found to over-merge under Decision 0.2's exact logged method, caught by diagnostic before committing, reverted to description-hash-only, reproduced the original August audit exactly, committed (`b5a45aa`). Tier 2 legitimate-side sourced via self-validating Greenhouse/Lever script — 130 postings from 26 companies, well above target, committed (`5545d37`). Tier 2 **fraud-side** sourcing attempted via web search/fetch, confirmed a structural dead end (no bulk-fetchable source exists), deferred to daylight with a time-boxed, browser-assisted plan. Stopped for the night with fraud-side sourcing and the manual audit as the next judgment-heavy tasks, deliberately left for fresh attention. |
| 2026-10-07 (Day 1 daytime) | Tier 2 fraud-side sourcing closed out | Linked the development machine; installed and used Claude in Chrome, which successfully loaded BBB Scam Tracker where the sandboxed browser pane and WebFetch had both been stopped by a Cloudflare challenge (handled by waiting, never bypassing). Read 8 pages of BBB's "employment" search results (~80 reports), filtered to 24 containing genuinely reproduced posting-adjacent text, resolved the provenance question (each report has a unique permalink, confirmed via the page's own DOM), and wrote the result to `data/raw/tier2/tier2_fraud_raw.jsonl` with BBB-specific provenance fields kept separate from the (mostly null) EMSCAD-shaped fields. Found and logged a source-side near-duplicate pattern (one report filed under 3+ Scam IDs) as a disclosed limitation. Tier 2 collection is now fully closed. `decisions.md` and `sources.md` updated and synced; git commit for commit-attribution fix still pending (remote shell was still provisioning). |
| 2026-10-07 (Day 1 evening) | Git commit-attribution fix resolved; docs re-synced | Remote shell came online. Backed up old history (`backup-pre-attribution-fix`), replayed `b5a45aa`/`5545d37`/`6e391b4` on a fresh branch with `Co-Authored-By`/`Claude-Session` trailers stripped (author/dates preserved, tree contents verified byte-identical to originals), reset `main` to the rewritten tip. Also corrected a standing error: the Tier 2 fraud-side JSONL was never "pending a commit" — `data/raw/` is gitignored wholesale, same as the pre-existing legit-side file; nothing was missing. Committed today's four-file docs sync (`decisions.md`, `sources.md`, `project.md`, `PROJECT_PLAN.md`) with a clean message, no AI trailer, under the student's own already-used git identity. Local `main` is now 4 commits ahead / 3 behind `origin/main`, clean of any AI trailer across the whole new range (verified by scanning every commit message) — pushing it (`git push --force-with-lease origin main`) is the one remaining student action; this session's sandboxed remote shell has no GitHub credentials to do it directly. |
| 2026-10-08 | Stages 4-9 built, run, and committed in one day — the sprint's technical core is done | Multi-signal evidence extraction (Stage 4), baseline + DistilBERT-fusion models (Stage 5), calibration (Stage 6), SHAP explainability (Stage 7), real API wiring + Stage 8b demonstration, and Stage 9's full evaluation (one-time test-set comparison, ablation, Tier 2 temporal transfer, source-probe) all completed same-day, well ahead of the original Day 3-4 pacing. Two real bugs caught and fixed before being reported (Stage 8's inverted credibility-score direction; Stage 7's probability-space SHAP saturation). The Tier 2 source-probe's perfect ROC-AUC=1.0000 was investigated empirically (`device_bash`, direct missingness counts against the raw EMSCAD/Tier 2 files) rather than accepted at face value, and confirmed as a Tier-2-collection-wide structured-field artefact — bigger in scope than Decision 0.4 anticipated. All results written into `methodology.md`; decisions and the investigation logged in `decisions.md`; `PROJECT_PLAN.md` and this file's "Where I am right now" brought current. Per the Stage 9 design decision, no further model/feature/seed change is permitted now that test has been seen. Next: live API test, then Chapters 4-6. |
| 2026-10-09 | Live API + full test suite confirmed; manual-entry frontend added, redesigned twice, named, and committed | Live HTTP test (`live_api_check.py`) and the full pytest suite (51/51) confirmed the artefact end-to-end -- development formally complete. A manual-entry frontend was then added as a deliberate, logged reopening of the "backend API only" scope line: built, visually redesigned twice (polish, then naming/attribution), verified structurally and against the untouched `<script>` block at every pass, named JobCred, confirmed working by the student, committed and pushed. Discussed and deferred two further input options (URL link, screenshot/OCR) at the student's request -- not decided, to revisit later. Student is now moving to thesis writing.
