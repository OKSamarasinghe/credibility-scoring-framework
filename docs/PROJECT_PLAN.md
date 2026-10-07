# PROJECT_PLAN.md — Full Project Plan (Start to End)

_Compiled 2026-08-27, refreshed 2026-09-20 (scope-cut decisions, hardware correction,
checklist added), **re-compressed into a 5-day sprint on 2026-10-06**, **Tier 2 collection
checklist closed out 2026-10-07, git commit-attribution fix applied locally 2026-10-07
evening (student push still required).** The "~1 month from 2026-08-27" deadline referenced
throughout the older sections of this file and in `project.md` has elapsed. **The operative
deadline, as of 2026-10-06, is 5 days from today — submission around 2026-10-11/12, pending
confirmation with the programme office.**
Section 0 below is the live sprint plan and takes priority over every other section for
*sequencing*. Sections 1–14 remain the narrative/reference record and are still correct on
facts that haven't changed. `decisions.md`, `methodology.md`, `sources.md` remain the
detailed logs and are authoritative over this file on any specific number — if a fact here
conflicts with one of those three, THEY win._

---

## 0. FIVE-DAY SPRINT PLAN (2026-10-06 compression) — READ THIS SECTION FIRST

### 0.1 What is already done — do not redo this

- **Data audit** — run on the real EMSCAD CSV, corrected twice (missingness double-count,
  duplicate mislabel, inconsistent C1–C6 "evaluable" definition), verified in two
  independent environments. ✅ Closed.
- **Stage 1 (ingestion)** — built, 9/9 tests passing, verified on two machines, committed.
  ✅ Closed.
- **Stage 2 sampling** — stratified 200-posting worksheet + manifest built, tested,
  reproduced, committed. **The manual coding of those 200 postings is NOT done** — that's
  Day 1–2 below, and it's the only part of Stage 2 that's actually yours to do. **This is
  now the single most time-critical unstarted task on the whole plan (2026-10-07).**
- **Stage 3 (leakage-controlled partitioning)** — group-aware 70/15/15 split built, a
  genuine over-merging bug caught and fixed before committing, verified, committed
  (`b5a45aa`). ✅ Closed.
- **Stage 8 skeleton** — FastAPI app, `/score` route, full JSON contract built and tested.
  Every pipeline stage honestly returns "not yet built" (HTTP 501). Zero fabricated data.
  ✅ Closed (skeleton only — real wiring is Day 4).
- **Tier 2 collection, both sides — ✅ Closed, 2026-10-07.** Legitimate side: 130 postings
  from 26 companies via the public Greenhouse/Lever APIs. Fraud side: 24 postings from BBB
  Scam Tracker, read via Claude in Chrome once the development machine was linked, each
  with a provenance-verified unique permalink — written to
  `data/raw/tier2/tier2_fraud_raw.jsonl`. **Neither raw file is committed to git, by
  existing repo policy** — `data/raw/` is gitignored wholesale (confirmed via
  `git check-ignore`); only the derived summaries/scripts are tracked
  (`reports/tier2_sourcing_summary.json`, `src/ingestion/tier2_sourcing.py`). An earlier
  note in this file wrongly treated the fraud-side raw file as pending a commit —
  corrected 2026-10-07 evening. Both sides well inside or above the 20–30 / 30–50 target
  bands. Full detail in `decisions.md`, 2026-10-07.
- **Docs sync (2026-09-20, refreshed 2026-10-07)** — `project.md`, `decisions.md`,
  `methodology.md`, `sources.md`, `PROJECT_PLAN.md` consistent across Claude Project,
  GitHub repo, and reality, as of 2026-10-07. `workplan.md` retired.
- **Scope-cut decisions (2026-09-20)** — rules-only baseline cut; DistilBERT fine-tuned, not
  frozen; Tier 2 reduced to ~50–100 postings; 3 seeds (one fixed split, N initialisations);
  explainability narrowed to SHAP only; divergent architecture review skipped, time-driven.
  Decision 0.2 resolved (MD5 + title-based grouping for near-duplicates).
- **Dataset strategy** — four external "second dataset" suggestions checked against primary
  sources and rejected (all are EMSCAD derivatives); two-tier EMSCAD + independently-collected
  Tier 2 plan reaffirmed.

**Not done, now the live critical path:** Stage 2 manual audit (200 postings — not started
at all), Stages 4–9 in full, Chapters 4–6, AI-use declaration, research paper. The git
commit-attribution trailer on 3 commits from last night is now fixed locally (§0.3) — the
student still needs to run the force-push themselves.

### 0.2 What changed today (2026-10-06) — log these in `decisions.md` (done below; see the
new entry dated 2026-10-06)

1. **Deadline corrected.** 5 days remaining, not "~1 month from 2026-08-27." That older date
   has already passed. If the actual programme-office date differs from "2026-10-11/12",
   this entire schedule shifts — confirm it the moment you can, but don't let confirming it
   block starting tonight.
2. **Tier 2 is time-boxed to Day 1 only**, compressed from the 1-week checkpoint decided on
   2026-09-20. Same fallback rule, just a much shorter fuse: if fewer than ~20 verified
   fraudulent postings are secured by the end of Day 1, the qualitative-only fallback is
   invoked and Tier 2 does not get a second day.

   > ✅ **Outcome, 2026-10-07:** not needed — 24 verified fraudulent postings secured well
   > within Day 1. See `decisions.md`.

3. **Ablation seed count is now conditional**, decided empirically on Day 3 by timing one
   real DistilBERT fine-tuning run, not guessed in advance.
4. **A triage order is fixed now, in advance** — see §0.4 — so that if the week slips, you
   are not making those calls live, under pressure, on Day 4 night.
5. **The 200-posting manual audit stays at 200.** You were explicit that quality here is not
   negotiable, and this file holds that line.
6. **Explicitly accepted, disclosed risk:** chasing down formal institutional ethics sign-off
   for Tier 2 primary data collection is not a gating step before collection starts, given the
   timeline. This is not being hidden — it stays logged as an open item in `project.md` and
   belongs in the dissertation's limitations section, stated plainly, not silently dropped.

### 0.3 Hard risk items — resolve these FIRST, before the day-by-day plan matters at all

- **CUDA — ✅ RESOLVED, 2026-10-06, 22:56.** `torch` reinstalled as `2.6.0+cu124`;
  `torch.cuda.is_available()` confirmed `True` against the RTX 3050 on the first attempt
  (`cu124` wheel). The Python-3.13-wheel-lag risk flagged here did not materialise — no
  fallback needed. `requirements.txt` still needs regenerating (`pip freeze > requirements.txt`,
  commit) to reflect the new pin before Day 3.

- **Tier 2 fraud-side sourcing — ✅ RESOLVED, 2026-10-07.** 24 postings collected from BBB
  Scam Tracker via Claude in Chrome. See `decisions.md`.

- **Git commit attribution — 🟡 FIXED LOCALLY, 2026-10-07 evening; student push still
  needed.** Three commits (`b5a45aa`, `5545d37`, `6e391b4`) carried a
  `Co-Authored-By: Claude` / `Claude-Session:` trailer the student did not want showing up
  in GitHub's contributor graph. Fix applied: backed up the old history as
  `backup-pre-attribution-fix`, cherry-picked all three onto a fresh branch from their
  shared parent, amended each message to drop the trailer lines only (author, email,
  commit/author dates all preserved), verified each new commit's tree is byte-identical to
  the old one (`git diff <old> <new>` empty) and that no trailer remains anywhere in the
  rewritten range. `main` reset to the rewritten tip locally. **Could not push from this
  session** — the linked machine's isolated remote shell has no stored GitHub credentials
  (separate sandbox from the Windows host's own credential manager). The student must run,
  from their own terminal: `git push --force-with-lease origin main`. Do **not** `git pull`
  first (that would re-merge the old trailer-carrying commits back in).

### 0.4 Triage order if the week slips — decided now, not live under pressure

1. **First cut: the research paper.** It slips past Day 5, finished in whatever slack exists
   right after, if any. The dissertation and the working artefact come first.
2. **Second cut: ablation seed count.** Reduce the leave-one-category-out ablation arms
   (E1, E2, E3, E4, `has_company_logo`) from 3 seeds to 1 each. The main baseline-vs-improved
   comparison keeps 3 seeds regardless — that comparison is the headline result.
3. **Third cut: Tier 2 depth.** Already resolved (§0.1) — both sides closed within Day 1.
4. **Never cut:** leakage-controlled partitioning, calibration, the test-set-used-once rule,
   the 200-posting manual audit, and the honest stub-vs-real distinction in the API. If the
   week runs out before these are solid, the paper and Tier 2 are what's missing from the
   final submission — not these.

### 0.5 Day-by-day schedule

**Tonight — 2026-10-06 (before you sleep, ~1 hour)**
- [x] Run the CUDA check in §0.3.
- [ ] Read `STAGE2_CODING_INSTRUCTIONS.md` once tonight so Day 1 morning starts coding
  immediately instead of re-reading the scheme cold.
- [x] Sleep.

**Day 1 — 2026-10-07**
*Goal: Decisions 0.3/0.4 resolved; Stage 3 built and tested; manual audit started; Tier 2
push happens and is checkpointed by end of day.*

| When | Task | Who | Status |
|---|---|---|---|
| Morning | Resolve Decision 0.3 (C6 viability) | You + me | ✅ Done, 23:50 last night |
| Morning | Resolve Decision 0.4 (Tier 2 field symmetry) | You + me | ✅ Done, 23:50 last night |
| Morning–afternoon | Build Stage 3 | Me (code), you run/verify | ✅ Done, committed `b5a45aa` |
| All day, parallel | **Start the Stage 2 manual audit** — 200 postings | You, alone | ⬜ **Not started — now the critical path** |
| All day, parallel | **Tier 2 push** — legitimate + fraud sourcing with provenance | You + me | ✅ Both sides done: 130 legit, 24 fraud |
| End of day | **Tier 2 checkpoint** — count verified fraudulent postings | You | ✅ 24, well above the 20 minimum |
| End of day | Commit Stage 3 + Tier 2 data; log decisions; fix git attribution | You | ✅ Stage 3 committed; Tier 2 raw files correctly gitignored (nothing to commit there); attribution fix rewritten locally — 🟡 force-push still needed from your own terminal; docs synced and committed |

**Day 2 — 2026-10-08**
*Goal: Stage 4 built — the actual research contribution (E4). Manual audit finished.*

- [ ] **Finish the Stage 2 manual audit** if any of the 200 postings remain — this cannot run
  later than today, Stage 4's lexicon work needs its findings.
- [ ] Build Stage 4: E1 (text/content cues), E2 (identity & contact cues — reuse the token
  logic from Stage 1), E3 (completeness flags + composite), and the real E4 lexicons for
  C1, C3–C6 (replacing every provisional regex from the August audit), plus the **first real
  attempt** at C2 location-matching (not a backfilled proxy).
- [ ] Every feature tagged with its evidence category, for clean leave-one-category-out
  ablation later.
- [ ] Re-measure C1,C3–C6 evaluable coverage against the real lexicons and update
  `sources.md` #3 — these figures are currently provisional; today they become real.
- [ ] Apply whatever the Decision 0.3 resolution requires, consistently.
- [ ] Apply whatever at least one Stage 2 audit finding revises or drops — this is Stage 2's
  actual payoff, not a formality. Log it.
- [ ] Commit. Tick §7.5 boxes.

**Day 3 — 2026-10-09**
*Goal: baseline + improved models trained and calibrated. The ablation-seed decision gets
made today, with real numbers, not a guess.*

- [ ] Confirm the CUDA fallback from Day 0 actually works before touching the real training
  run.
- [ ] Train the baseline: TF-IDF + Logistic Regression, TF-IDF + Random Forest. Quick, CPU
  is fine for this.
- [ ] Run **one** DistilBERT fine-tuning pass (1 seed) fused with the E2/E3/E4 vector, and
  time it. Use that real number to decide, right then, whether 3 seeds × 5 ablation arms fits
  what's left of the week. If not, apply the Day-0-agreed cut: ablation arms go to 1 seed,
  main comparison stays at 3. **Log whichever way it goes, same day, in `decisions.md`.**
- [ ] Confirm identical class weighting across baseline and improved models.
- [ ] Fit hyperparameters, decision threshold and calibrator on validation only — never on
  test.
- [ ] Build Stage 6: Platt vs. isotonic, chosen on validation; Brier, ECE, reliability curve.
- [ ] Commit. Tick §7.5 boxes.

**Day 4 — 2026-10-10**
*Goal: the heaviest day. Explainability, real API wiring, demonstration, and the one-time
test-set evaluation with ablation. Flagged now: this is the most likely day to run over —
if it does, it spills into Day 5 morning, and that's Day 5's writing time it eats, not an
excuse to touch the test set twice.*

- [ ] Build Stage 7: SHAP over the fused feature set (consider sub-sampling the test set for
  the fidelity tests specifically, if SHAP's compute cost threatens the day — log this as a
  decision if you do it, don't let it happen silently), rule-message summaries from the
  C1–C6 flags, comprehensiveness/sufficiency (deletion/insertion) and rule-consistency
  checks, compared against a random-attribution control.
- [ ] Wire Stage 8: replace the four stub functions in `src/api/main.py`
  (`preprocess`, `extract_features`, `predict`, `explain`) with the real Stage 1/4/5-6/7
  code, one function at a time, without touching the route handler. Run one real end-to-end
  request with no stubs left.
- [ ] Run Stage 8b: 3 real postings through the live API — clear fraud, clear legit, one
  genuinely ambiguous. No cherry-picking. Write results straight into `methodology.md`, kept
  separate from Stage 9.
- [ ] Run Stage 9: full metric set on the test set, **used exactly once**; leave-one-category-
  out ablation at whatever seed count Day 3 settled on; Tier 2 temporal transfer (T1/T2/T3)
  — Tier 2 is ready on both sides, so this runs for real, not as the qualitative fallback;
  source-probe leakage test, reported regardless of outcome.
- [ ] Commit. Tick §7.5 boxes. Write the raw numbers into `methodology.md` immediately —
  don't let them live only in a notebook.

**Day 5 — 2026-10-11**
*Goal: Chapter 4 through 6, AI-use declaration, final sync. The paper is a stretch goal, not
a commitment — see §0.4.*

- [ ] Write **Chapter 4 (Results)** directly from the Day 3/4 measured numbers. This is the
  first day it's even possible to write this chapter — do not draft it from anything but
  real measurements, and mark any figure you're unsure of before it goes further.
- [ ] Write **Chapter 5 (Discussion)** — what the numbers mean against each RQ, including
  any that don't confirm what was hoped. A null or negative result on O3 is a complete
  answer, not a failure to hide.
- [ ] Write **Chapter 6 (Conclusion)** — contributions, limitations (name the Tier 2
  asymmetry — 130 legit vs. 24 fraud, different source types — and the skipped ethics
  sign-off here, plainly), future work.
- [ ] Write the **AI-use declaration** — required by the programme; state what AI assisted
  with (planning, code scaffolding, docs structuring) versus what's yours (the contribution,
  the words, the judgement calls).
- [ ] Final sync: update "Where I am right now" in `project.md`; finalise `decisions.md` and
  `sources.md`; tick every remaining §7.5 box that's true; copy all five `.md` files into
  the repo `docs/` folder and the Claude Project, replacing the old copies in both places so
  only one copy exists anywhere.
- [ ] **If, and only if, everything above is done with time left:** condense the dissertation
  into the research paper. If there's no time left, this is the one deliverable that moves
  past the 5-day window — named now, not discovered as a surprise on the last day.

---

## 1. What this is

**"An Explainable Credibility Scoring Framework for Online Recruitment Posts Using
Multi-Signal Evidence and Consistency Verification."**

BSc (Hons) Computing final-year individual project — Coventry University / NIBM, Colombo 7.
O.K. Samarasinghe — Coventry 16116041, NIBM COBSCCOMP242P-069.

Design Science Research. The deliverable is a **built and evaluated artefact** — a backend
credibility-scoring API — plus a dissertation and a research paper. Positioned in FEDS terms
as **ex post** (the built system is evaluated, not the design in advance) and predominantly
**artificial** (benchmark dataset, controlled conditions), with a **naturalistic** component
in the Tier 2 assessment.

**Deadline: 5 days from 2026-10-06 (see Section 0).**

---

## 2. The problem and the gap

Four gaps identified from a ten-study literature review (2017–2026): limited user-facing
explainability; underuse of structured multi-signal evidence; **absence of explicit
text–metadata consistency verification** (the empty column — no reviewed system checks
whether a posting's structured fields contradict its own free text); and binary
fake/real output that gives weak practical decision support.

**The research contribution is consistency verification (E4).** Everything else in the
taxonomy exists to support and contextualise that contribution, not to compete with it.

---

## 3. Objectives and research questions

| ID | Objective | Maps to |
|---|---|---|
| O1 | Define and validate a four-category evidence taxonomy, validated by manual audit | RQ1 |
| O2 | Develop and benchmark a TF-IDF baseline under leakage-controlled evaluation | RQ2 |
| O3 | Combine transformer text representation with structured evidence + consistency flags; quantify the change under matched conditions | RQ3 |
| O4 | Deliver a backend API converting calibrated probabilities into a 0–100 score with verified explanations | RQ4 |
| O5 | Evaluate with full metric set, per-category ablation, and temporal generalisability on contemporary postings | RQ5 |

**Rule held throughout:** no objective or RQ states its own expected result. O3 quantifies
a change; it does not presuppose the change is positive.

---

## 4. The artefact — what gets built

A backend REST API (**FastAPI**) exposing a **`/score`** endpoint.

- **Input:** raw job-posting text (primary, supported path) or a posting URL (secondary,
  best-effort, only where terms allow automated retrieval).
- **Pipeline, executed end-to-end per request:** preprocessing → feature extraction →
  prediction → explainability.
- **Output — single JSON object:**

```json
{
  "credibility_score": 0-100,
  "risk_band": "High | Medium | Low",
  "top_reasons": ["...", "..."],
  "suspicious_phrases": ["..."],
  "contradictions": [{"rule": "C1", "field": "telecommuting", "detail": "on-site vs remote"}],
  "verification_checklist": ["..."]
}
```

The score is a **calibrated probability mapped to 0–100** — never a raw model output.

**Current build status (2026-10-07):** the FastAPI app, `/score` route, and the exact
request/response schema above are built and tested (`src/api/main.py`, `src/api/schemas.py`).
Every pipeline stage is an honest stub — raises a clear "not yet built" error rather than
inventing a result. Zero fabricated data anywhere in the running system. Real wiring is
Day 4 of the sprint.

---

## 5. Evidence taxonomy — the four measured categories

| ID | Category | What it reads |
|---|---|---|
| E1 | Text / Content Cues | wording, phrasing, suspicious phrases (title, description, requirements, benefits) |
| E2 | Identity & Contact Cues | employer identity, off-platform contact pressure (company_profile, location, token counts) |
| E3 | Metadata Completeness | presence flags across 9 structured fields + composite score |
| E4 | Text–Metadata Consistency **(the novelty)** | C1–C6 comparing fields against text |

The external company-presence check is **API-only, qualitative, and explicitly not a fifth
measured category** — excluded from ablation and all quantitative evaluation.

### Consistency rules C1–C6, measured status as of 2026-08-27 (provisional; Day 2 re-measures)

| Rule | Compares | Field cov. (verified) | Evaluable cov. | Status |
|---|---|---|---|---|
| C1 | telecommuting vs description | 100.0% | 10.5% | 🟡 Provisional pattern — Day 2 re-measures |
| C2 | location vs description | 88.4% | not measured | ❌ Deferred — Day 2 builds the real matcher |
| C3 | employment_type vs description | 80.6% | 12.2% | 🟡 Provisional pattern — Day 2 re-measures |
| C4 | required_experience vs description | 60.6% | 30.2% | 🟡 Provisional pattern — Day 2 re-measures |
| C5 | required_education vs description | 54.7% | 27.8% | 🟡 Provisional pattern — Day 2 re-measures |
| C6 | salary_range vs description | 15.2% | 7.6% | 🟡 Provisional pattern — Day 2 re-measures |

**Aggregate:** 56.7% of postings evaluable by at least one rule; mean 0.88 of 6 rules
evaluable per posting. Full detail: `sources.md` #3.

---

## 6. Datasets — two tiers, never merged

| Tier | Dataset | Size | Role | Status |
|---|---|---|---|---|
| 1 | EMSCAD (Vidros et al., 2017) | 17,880 (866 fraud / 4.84%) | ALL training, tuning, calibration, ablation | ✅ Audited, ingestion built and tested |
| 2 | Independently collected contemporary postings | **130 legitimate (Greenhouse/Lever) + 24 fraudulent (BBB Scam Tracker) = 154 total** | Held-out temporal validation ONLY | ✅ **Closed, 2026-10-07** — both sides sourced, provenance-recorded, exceeding their respective 30–50 / 20–30 targets |

Tier 2 is never used for training; the tiers are never merged. **Decision 0.4 (Tier 2 field
symmetry)** — resolved: BBB fraud reports document almost no structured fields, so the
asymmetry could not be reduced at the source as originally hoped; it is disclosed instead
(130:24 volume ratio, and E3/E4 feature availability differs systematically by source, not
by fraud status). The source-probe leakage test (2026-08-07 decision) is run on Tier 2 as
planned, during Stage 9.

---

## 7. Full methodology — all nine stages plus 8b, with sprint-day targets

| Stage | Activity | Objective | Status (2026-10-07) | Sprint day |
|---|---|---|---|---|
| — | Data audit | grounds Stage 1 | ✅ Done | — |
| 1 | Ingestion & preprocessing | Foundation | ✅ Done, 9/9 tests | — |
| 2 | Evidence taxonomy + manual audit (200 postings) | O1 | 🟡 Sampling done; manual coding not started — **critical path** | **Day 1–2** |
| 3 | Leakage-controlled partitioning (70/15/15) | O2,O3,O5 | ✅ Done, verified 2026-10-06/07 | **Day 1** |
| 4 | Multi-signal evidence extraction (E1–E4) | O1,O3 | ⬜ Not started | **Day 2** |
| 5 | Model development (baseline + improved) | O2,O3 | ⬜ Not started | **Day 3** |
| 6 | Probability calibration + score mapping | O4 | ⬜ Not started | **Day 3** |
| 7 | Explainability layer + fidelity testing | O4 | ⬜ Not started | **Day 4** |
| 8 | API build (FastAPI `/score`) | O4 | 🟡 Skeleton built; real wiring pending | **Day 4** |
| 8b | Demonstration (3 postings, one ambiguous) | O4 | ⬜ Not started | **Day 4** |
| 9 | Evaluation, ablation, temporal transfer | O5 | ⬜ Not started | **Day 4** |
| — | Chapters 4–6, AI declaration | — | ⬜ Not started | **Day 5** |
| — | Research paper | — | ⬜ Not started | **Stretch — may slip past Day 5, see §0.4** |

For the detailed "definition of done" per stage, see Section 0.5's day-by-day task lists —
they now carry the operational detail that used to live here. The twelve guardrails in
Section 8 below still apply unchanged to every stage.

---

## 7.5 — LIVE CHECKLIST (tick the moment you finish something, not at the next review)

### Pre-work

- [x] Repository, environment, `.gitignore` set up and verified
- [x] Data audit run and corrected
- [x] Dataset strategy stress-tested against 4 external alternatives — rejected, reaffirmed
- [x] Hardware capability corrected (RTX 3050 + 16GB RAM)
- [x] Scope-cut decisions made (2026-09-20 round)
- [x] Decision 0.2 resolved (MD5 + title grouping)
- [x] Tier 2 legitimate-source APIs verified
- [x] CUDA-enabled torch confirmed working (`2.6.0+cu124`, 2026-10-06 22:56)
- [x] Decision 0.3 resolved (2026-10-06, 23:50 — see `decisions.md`)
- [x] Decision 0.4 resolved (2026-10-06, 23:50 — see `decisions.md`)
- [x] Tier 2 fraud-source access verified (2026-10-07 — Claude in Chrome against BBB Scam Tracker)

### Stage 1 — Ingestion & preprocessing

- [x] All items complete, tested, committed.

### Stage 2 — Evidence taxonomy + manual audit

- [x] Sample, worksheet, coding scheme built and committed
- [ ] **Manual coding of 200 postings (Day 1–2 — yours alone, not started yet)**
- [ ] Per-category observability rate computed (Day 2)
- [ ] Per-rule agreement rate computed (Day 2)
- [ ] At least one signal revised/dropped based on audit findings, logged (Day 2)
- [ ] Results written into `methodology.md` (Day 2)

### Stage 3 — Leakage-controlled partitioning (Day 1)

- [x] Group-aware stratified 70/15/15 split implemented (description-hash grouping;
  title-hash union tried, found to over-merge, reverted same night — see `decisions.md`)
- [x] Zero group overlap proven across train/validation/test
- [x] Duplicate counts reported using the resolved grouping method (4,762 / 26.63%,
  matches the August audit exactly)
- [ ] Vectorisers/scalers/encoders fit on train only — Stage 5's task, not Stage 3's
- [ ] Results written into `methodology.md`

### Stage 4 — Multi-signal evidence extraction (Day 2)

- [ ] E1, E2, E3 features built
- [ ] E4 / C1–C6 real lexicons written, replacing every provisional pattern
- [ ] C2 real location-matching logic built (first real attempt)
- [ ] Every feature tagged with its category for clean ablation
- [ ] All C1–C6 evaluable-coverage figures re-measured against real lexicons
- [ ] Decision 0.3 applied consistently

### Stage 5 — Model development (Day 3)

- [ ] TF-IDF + Logistic Regression baseline trained
- [ ] TF-IDF + Random Forest baseline trained
- [ ] One DistilBERT fine-tuning run timed; ablation seed count decided and logged
- [ ] Identical class weighting confirmed on both models
- [ ] Hyperparameters/threshold fitted on validation only
- [ ] 3-seed repetition completed on the main comparison, mean ± SD reported
- [ ] Test set not yet touched

### Stage 6 — Calibration (Day 3)

- [ ] Platt and isotonic both tried, selected on validation
- [ ] Brier score, ECE, reliability curve reported
- [ ] Risk-band thresholds set

### Stage 7 — Explainability (Day 4)

- [ ] SHAP integrated over the fused feature set
- [ ] Rule-message summaries generated from C1–C6 flags
- [ ] Comprehensiveness, sufficiency, rule-consistency measured
- [ ] Random-attribution control compared against

### Stage 8 — API, real pipeline wiring (Day 4)

- [x] Skeleton built and tested
- [ ] All four stub functions wired to real code
- [ ] End-to-end real request tested, no stubs remaining

### Stage 8b — Demonstration (Day 4)

- [ ] Fraud, legitimate, and ambiguous examples run and captured
- [ ] Results written into `methodology.md`, kept separate from Stage 9

### Stage 9 — Evaluation (Day 4)

- [ ] Full metric set computed on test set, used once
- [ ] Ablation run at whatever seed count Day 3 settled on
- [ ] Tier 2 transfer run (ready on both sides — not the qualitative fallback)
- [ ] Source-probe leakage test run and reported regardless of outcome
- [ ] Results written into `methodology.md`

### Tier 2 collection (Day 1 only) — ✅ ALL CLOSED, 2026-10-07

- [x] Company slug list built
- [x] Legitimate postings collected (target 30–50) — 130 collected, kept in full
- [x] Fraud-source access verified
- [x] Fraudulent postings collected (target 20–30) — 24 collected
- [x] Provenance recorded for every collected posting (unique source URL + source job ID
  for every one of the 130 + 24 records)

### Write-up (Day 5)

- [x] Chapters 1–3 drafted
- [ ] Chapter 4 (Results)
- [ ] Chapter 5 (Discussion)
- [ ] Chapter 6 (Conclusion)
- [ ] AI-use declaration written
- [ ] Research paper drafted (stretch — may slip past the sprint)

---

## 8. The twelve guardrails (build.md §5) — hold these as hard constraints throughout

1. Controlled comparison — baseline/improved differ only in text + structured features.
2. Class weighting is primary; SMOTE is a supplementary baseline-only arm, fitted inside
   training folds only.
3. Leakage control — duplicates never span train/test; vectorisers fit on train only.
4. 70/15/15 split; hyperparameters/threshold/calibrator on validation only; test used once.
5. Calibration mandatory — Brier, ECE, reliability curve.
6. Drop `in_balanced_dataset`.
7. Extract contact/media tokens **before** stripping HTML.
8. Never impute missing structured fields — missingness is the E3 signal.
9. Feature-level ablation, category-tagged, overlaps reported.
10. Thresholds set before seeing test results.
11. Demonstration ≠ evaluation.
12. Explanation faithfulness tested, not assumed — computational only.

---

## 9. Environment

Python 3.13.9, FastAPI, pandas 3.0.5, scikit-learn, PyTorch 2.6.0+cu124 (**CUDA build
confirmed working 2026-10-06**), Hugging Face Transformers, SHAP,
imbalanced-learn. Full pinned list in `requirements.txt`. No paid data sources, single
developer. Hardware: RTX 3050 GPU + 16GB RAM (gaming laptop). Git repository:
`credibility-scoring-framework` (private).

---

## 10. Decision log — status as of 2026-10-07

| Decision | Status | Notes |
|---|---|---|
| Class weighting over SMOTE | ✅ Closed | `decisions.md`, 2026-08-07 |
| Two-tier dataset strategy | ✅ Closed, reaffirmed | 2026-08-07; stress-tested 2026-08-27 |
| Drop `in_balanced_dataset` | ✅ Closed | 2026-08-07 |
| **0.1** — C1–C6 evaluable-coverage definition | ✅ Closed | 2026-08-27 |
| **0.2** — near-duplicate grouping method | ✅ Closed, then CORRECTED | 2026-09-20 decision, reverted to description-only 2026-10-06 23:59 after the title-hash union was found to over-merge in practice (56.68% vs the 48.9% it was meant to improve on) — see `decisions.md` |
| Hardware constraint correction | ✅ Applied | 2026-09-20 |
| Rules-only baseline | ✅ Closed — CUT | 2026-09-20 |
| Frozen vs. fine-tuned DistilBERT | ✅ Closed — fine-tuned | 2026-09-20, CUDA confirmed working 2026-10-06, no fallback needed |
| Divergent architecture review | ✅ Closed — skipped | 2026-09-20 |
| "5 seeds" definition + count | ✅ Closed — 3 seeds, fixed split | 2026-09-20 |
| Explainability method scope | ✅ Closed — SHAP only | 2026-09-20 |
| Tier 2 legitimate-source API access | ✅ Verified | 2026-09-20 |
| **0.3** — label-conditional statistics in design | ✅ Closed | 2026-10-06, 23:50 — see `decisions.md` |
| **0.4** — Tier 2 field symmetry | ✅ Closed | 2026-10-06, 23:50; outcome confirmed 2026-10-07 — see `decisions.md` |
| **Deadline correction** | ✅ Applied | 2026-10-06 — 5 days remaining, not ~1 month |
| **Tier 2 time-boxing to Day 1** | ✅ Closed, not needed | 2026-10-06 — both sides closed within Day 1, see `decisions.md` |
| **Tier 2 fraud-side sourcing** | ✅ Closed | 2026-10-07 — 24 postings via BBB Scam Tracker / Claude in Chrome, see `decisions.md` |
| **Ablation seed count** | 🟡 Conditional | 2026-10-06 — decided empirically Day 3 |
| **Sprint triage order** | ✅ Closed | 2026-10-06 — fixed in advance, §0.4 |
| Success thresholds per objective | ⬜ Open | Agree with supervisor if any contact window exists this week; otherwise state as a limitation |
| Tier 2 ethics approval status | ⬜ Open, explicitly accepted risk | Not gating collection this week — see §0.2.6 |
| Git commit attribution (3 commits) | 🟡 Fixed locally 2026-10-07 evening | Rewritten on `attribution-fix`, trees verified identical, trailers gone, `main` reset locally; student runs `git push --force-with-lease origin main` — see §0.3 |

---

## 11. Dependency graph — 5-day compression

```
Tonight: CUDA check + fallback plan
    │
Day 1: Decision 0.3, 0.4 ──► Stage 3 (build) ║ Manual audit starts ║ Tier 2 push → checkpoint
    │
Day 2: Manual audit finishes ──► Stage 4 (E1-E4, real lexicons, re-measured coverage)
    │
Day 3: Stage 5 (baseline + 1 timed DistilBERT run → seed decision) ──► Stage 6 (calibration)
    │
Day 4: Stage 7 (SHAP) ──► Stage 8 (real wiring) ──► Stage 8b (demo) ──► Stage 9 (evaluation, once)
    │
Day 5: Chapter 4 ──► Chapter 5 ──► Chapter 6 ──► AI declaration ──► final sync
    │
(stretch, may slip): research paper
```

---

## 12. Evaluation plan (Stage 9 detail)

| Objective | Metric(s) | Threshold |
|---|---|---|
| O1 | Per-category observability; per-rule agreement | **[TO SET]** — provisional ≥80%/rule |
| O2 | Precision, Recall, F1, PR-AUC, ROC-AUC | **[TO SET]** |
| O3 | Δ F1, Δ PR-AUC vs. baseline | No directional threshold — objective is to quantify |
| O4 | Comprehensiveness, sufficiency, rule-consistency, Brier, ECE | **[TO SET]** |
| O5 | Full metric set + per-category Δ; Tier 2 transfer | **[TO SET]** |

Thresholds should still be agreed with the supervisor if any contact window exists this
week; if not, Chapter 5 must state plainly that thresholds were self-set under time
pressure, which is a limitation to disclose, not a result to present as rigorous.

---

## 13. Write-up — Day 5

Chapters 1–3 already drafted. **Chapter 4 (Results) cannot be drafted until Stage 9 produces
real measurements on Day 4** — do not start it earlier from assumed or illustrative numbers.
Chapter 5 (Discussion) and Chapter 6 (Conclusion) follow the same day. AI-use declaration
required by the programme — write it Day 5, not at the very last minute. The research paper
is explicitly a stretch goal (§0.4) — condensed from the finished dissertation, only once
Chapters 4–6 and the declaration are done.

---

## 14. What "done" looks like, end of Day 5

- Stages 1–9 and 8b each meeting its own stated definition of done, at whatever seed depth
  Day 3's conditional decision landed on.
- Decisions 0.3 and 0.4 closed and logged.
- Tier 2 collected on both sides and transfer-tested on Day 4 — Decision 0.4's field-
  symmetry question already answered (asymmetric, disclosed) rather than still open.
- `/score` runs the full real pipeline on a real request — no stubs remaining in
  `src/api/main.py`.
- Every RQ has a measured answer in Chapter 4, including any that don't confirm what was
  hoped.
- Dissertation and AI-use declaration finished. Research paper finished if time allowed,
  named honestly as outstanding if not.
