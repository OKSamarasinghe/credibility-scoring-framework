# project.md — An Explainable Credibility Scoring Framework for Online Recruitment Posts

_Last updated: 2026-10-07, 18:10_

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
| O5 | Evaluation & Generalisability | Evaluate with full metric set, ablation per evidence category, and temporal generalisability on contemporary postings | Must-have (Tier 2 collection now closed for both sides — see "Where I am right now") |

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
- **Stage 4 (multi-signal evidence extraction) — complete, 2026-10-08:** E1–E4 built
  (`src/features/extract_features.py`), run on the full corpus (n=17,880), 33/33 new tests
  passing (51/51 across the whole suite). Four precision bugs found during full-corpus
  validation and fixed before any figure was reported (C1 "work from home" perk-vs-position
  conflation, C1 negation ignored, C6 "k"-suffix unresolved plus a dead salary-context gate,
  C3 "short-term disability"/"seasonal" polysemy). C2 has its first real location matcher,
  no longer deferred. All C1–C6 coverage figures re-measured and final — see
  `methodology.md`, `decisions.md`, `sources.md` #3. **Not yet committed — pending the
  student's own commit**, per standing project policy that commits are never run by AI.
- **Not yet started:** Stages 5–9 in full. Stage 5 (model development/DistilBERT
  fine-tuning) needs the student's real Windows/CUDA venv — it cannot run from this
  session's sandboxed `device_bash` shell, which is Python 3.10.12/pandas 2.3.3 (useful for
  deterministic cross-checks, not for GPU training). Chapters 4–6 of the dissertation
  (Chapter 4 cannot be drafted until Stage 9 produces real measurements — now scheduled for
  Day 4–5 of the sprint). The git commit-attribution fix is fully closed (pushed, confirmed
  on GitHub) — nothing left there.

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

1. **Done overnight 2026-10-06/07:** CUDA fixed; Decisions 0.3/0.4 resolved; Stage 3 built,
   bug found and fixed, verified, committed; Tier 2 legitimate-side sourced (130 postings)
   and committed.
2. **Done Day 1 daytime (2026-10-07):** Tier 2 fraud-side sourced (24 postings,
   provenance-verified) — Tier 2 collection is now fully closed, both sides.
3. **Day 1, remaining — the critical path now:** start (and push hard on) the 200-posting
   manual audit — it has not started at all yet and nothing in Stage 4 can be finalised
   without it. Everything else on Day 1 is closed: the git commit-attribution fix is pushed
   and confirmed on GitHub; today's doc sync is committed (`data/raw/` stays gitignored by
   existing policy, nothing pending there).
4. **Day 2:** finish the manual audit; build Stage 4 (real E1–E4, real lexicons, real C2).
5. **Day 3:** train baseline + improved models; decide the ablation seed count from a real
   timing; build Stage 6 (calibration).
6. **Day 4:** build Stage 7 (SHAP); wire Stage 8 for real; run Stage 8b and Stage 9 once.
7. **Day 5:** write Chapters 4–6, the AI-use declaration, and sync every `.md` file; the
   research paper only if time remains.

---

## Open questions

- **Tier 2 collection — ✅ CLOSED, 2026-10-07.** Both sides met or exceeded target within
  the Day 1 time-box: 130 legitimate (Greenhouse/Lever), 24 fraudulent (BBB Scam Tracker,
  via Claude in Chrome once the development machine was linked). See `decisions.md`,
  2026-10-07.
- **What are my success thresholds?** Still unset in `methodology.md`. Agree with
  supervisor if any contact window exists this week; otherwise state as a self-set
  limitation in Chapter 5.
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
