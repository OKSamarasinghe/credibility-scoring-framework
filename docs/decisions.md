# decisions.md — Design Decisions & Rationale

_Last updated: 2026-09-20_

> **What this file is.** One entry for every real design decision in my project: what I
> decided, what else I considered, why I went this way, and what it cost me. This is the
> file that answers the question every examiner asks — *"why did you do it that way?"*
>
> **How I use it.** Each entry ends with a **self-check** question. Before my viva I go
> through this file, cover the answer, and try to answer each self-check out loud in my own
> words. If I can't, I don't understand that decision well enough yet and I come back to it.
> The reasoning below is written the way I would explain it, so I have something concrete
> to test myself against.
>
> Format: newest at the top.

---

## 2026-09-20 — Correction: hardware constraint was wrong; DistilBERT will be fine-tuned, not frozen

- **Correction, not a new decision:** every project file (`project.md`, `SKILL.md`,
  `build.md`, and this file's own "Frozen vs. fine-tuned DistilBERT" pending entry) states
  "no dedicated GPU" as a hard constraint. **This was wrong.** My laptop has an RTX 3050
  (gaming laptop, 16GB RAM). This constraint was assumed at proposal stage and never
  actually checked against my own hardware.

- **Consequence — resolves the frozen-vs-fine-tuned question:** with a CUDA-capable GPU,
  fine-tuning DistilBERT (66M parameters) is feasible in hours, not days. Fine-tuning also
  reliably outperforms frozen embeddings for domain-specific text classification. **Decision:
  fine-tune, not frozen.** This also removes the earlier worry about needing an external
  environment like Colab for a seeded run — everything now runs locally, which is better for
  reproducibility, not just faster.

- **Why logged as a correction, not silently fixed:** the same principle as the "English
  Teacher Abroad" correction earlier in this file — the wrong assumption stood for weeks and
  shaped planning (e.g. it's the entire reason "frozen vs. fine-tuned" was ever a real
  question). Recording that it was wrong, and why it wasn't caught earlier, is worth more in
  a viva than quietly updating `project.md`'s hardware line with no trace.

- **Self-check:** *Why was "no GPU" assumed for months without being checked, and what
  single fact changed once it was?*

---

## 2026-09-20 — Scope-cut decisions given the confirmed ~1 month deadline

- **Context:** the actual submission deadline was confirmed for the first time on
  2026-08-27 as approximately one month away. Full rigor on all nine stages as originally
  scoped does not fit that timeline for a single developer. Five related decisions were
  made together, deliberately, in one CONVERGENT session, rather than left to erode
  piecemeal under time pressure later.

### 1. Rules-only baseline (E2+E3+E4, no text model): CUT

- **Options considered:** (A) keep it as a third model arm; (B) cut it entirely.
- **Why cut:** it was always logged as optional ("does the transformer earn its
  complexity?"). Stage 9's leave-one-category-out ablation already measures how much E4
  alone contributes, via a different but overlapping route, without a whole separate
  training arm, retraining, and extra ablation rows.
- **What I gave up:** a clean, standalone answer to "how far would rules alone get me,
  with zero text model at all." The ablation study answers a related but not identical
  question.
- **Self-check:** *What question would the rules-only baseline have answered that the
  ablation study doesn't cover, and why is losing that answer acceptable here?*

### 2. Tier 2 depth: REDUCED collection (~50–100 postings), not full, not zero

- **Options considered:** (A) full collection (300–600, as originally planned); (B) reduced
  collection (~50–100); (C) qualitative-only (the pre-planned 2026-08-07 fallback).
- **Why reduced, not the extremes:** qualitative-only (C) discards the one finding no
  reviewed paper has produced — whether an EMSCAD-trained model survives contact with 2026
  fraud — and that's too valuable to give up pre-emptively. Full collection (A) risks
  cannibalising time from Stages 3–9 if it overruns; a project with no finished pipeline is
  worse than one with a modest, honestly-scoped Tier 2. A reduced set, reported with wide
  confidence intervals and explicitly labelled as time-constrained, is a legitimate,
  disclosed limitation rather than a hidden shortcut.
- **Concrete plan:** start sourcing immediately, in parallel with the Stage 2 manual audit,
  not queued up after it. Target: at least 20–30 verified fraudulent postings and 30–50
  legitimate.
- **Checkpoint, not open-ended:** if fewer than 20 verified fraudulent postings are secured
  within roughly one week of starting, the qualitative-only fallback is invoked instead of
  letting collection drag on unbounded.
- **What I gave up:** statistical power. A 50–100 posting Tier 2 will have wide confidence
  intervals; this must be stated plainly, not minimised.
- **Self-check:** *Why is a small, honestly-reported Tier 2 more defensible than either
  collecting the full 300–600 or abandoning quantitative Tier 2 entirely?*

### 3. Reproducibility seeds: 3, not 5 — and the "what does five seeds mean" question is now settled

- **The seed-count reduction:** ablation alone multiplies retrains (~5 category removals ×
  multiple models × seeds); this compounds fast even with GPU acceleration. 3 seeds still
  supports mean ± SD reporting and is a documented, disclosed reduction, not a silent one.
- **The definition question (previously open, now resolved):** "repeated across N seeds"
  means N *model initialisations* run against **one fixed train/validation/test split** —
  not N different splits. This is the only reading compatible with the existing guardrail
  that the test set is used once; N different splits would mean N different test sets.
- **What I gave up:** some robustness in the noise estimate on the test set (~130 fraud
  postings), compared to 5 seeds.
- **Self-check:** *Why is "5 different splits" incompatible with "test set used once," and
  what does the seed count actually vary instead?*

### 4. Explainability: SHAP only, LIME dropped

- **Options considered:** (A) both SHAP and LIME, as originally planned; (B) SHAP only.
- **Why SHAP alone:** SHAP has stronger theoretical grounding (Shapley values, consistency
  guarantees) and handles both the structured evidence vector and text attribution
  reasonably well in one framework. Building and validating two separate explanation
  pipelines — each needing its own fidelity testing — isn't worth the cost under this
  timeline when SHAP alone satisfies O4's fidelity-testing requirement.
- **What I gave up:** a second, independent explanation method to cross-check SHAP's output
  against. `Research_Objectives_and_Questions_Final.docx` names both SHAP and LIME as
  examples ("e.g."), not a hard requirement of exactly two methods, so this doesn't violate
  the objective as written — but the .docx wording should be checked before submission.
- **Self-check:** *Does dropping LIME violate Objective 4 as formally written, or does its
  "e.g." wording leave room for this?*

### 5. Divergent architecture review: skipped, time-driven

- **Context:** this was logged as a pending decision since 2026-08-07 — survey alternatives
  (gradient boosting, sentence-transformer + gradient-boosted classifier, other lightweight
  transformers) before committing to TF-IDF + DistilBERT fusion.
- **Decision:** given the confirmed deadline, this survey is not done. The original design
  is committed to as-is.
- **Why this is acceptable to state plainly rather than quietly skip:** the honest position
  in a viva is "I did not conduct a full landscape review before committing to this
  architecture, because of the timeline, and I can name what that costs me" — not silence
  on the question, and not a retrofitted justification pretending the review happened.
- **What I gave up:** the ability to say with evidence that TF-IDF + DistilBERT fusion was
  chosen over specific, considered alternatives. It was chosen at proposal stage and never
  re-examined against the landscape.
- **Self-check:** *Why is honestly stating "I skipped this survey because of time" better
  than either silently skipping it or fabricating a comparison that wasn't done?*

---

## 2026-09-20 — Near-duplicate grouping method for Stage 3 (Decision 0.2, resolved)

- **Decision:** exact-normalised MD5 hashing on `description` (already built and tested in
  the audit script), with a **secondary grouping key on normalised `title`** added at low
  implementation cost.

- **Options considered:**
  - (A) Exact-normalised MD5 hashing only (already measured: 4,762 records / 26.6% in a
    duplicate group, but fragments the 715-record "English Teacher Abroad" campaign across
    15 separate groups).
  - (B) First-12-token hash proxy (already measured: merges 48.9% of the corpus — likely
    over-merging unrelated postings sharing a generic opening line).
  - (C) MD5 on description, plus a second grouping pass on normalised title text.

- **Why C:** option A under-groups (misses some real near-duplicates); option B over-groups
  badly (merges nearly half the corpus, a worse failure mode). Many campaigns reuse a
  near-identical title even when body text varies slightly — adding a title-based grouping
  key catches some of what pure description-hashing misses, at minimal new code (reuse the
  same `normalise()` + MD5 pattern already written, applied to `title` instead of
  `description`, then union the two groupings).

- **What I gave up:** a fully rigorous near-duplicate solution (e.g. MinHash/shingling)
  that would catch paraphrased campaigns with both different titles and different bodies.
  Not pursued, given the deadline — title+description exact-hash union catches the
  documented failure case (English Teacher Abroad) without new algorithmic complexity.

- **Revisit if:** time permits after Stage 3, or if Stage 3's measured duplicate-group
  statistics look implausible given what title+description hashing should catch.

- **Self-check:** *Why does adding a title-based grouping key specifically address the
  fragmentation problem measured in the "English Teacher Abroad" campaign?*

---


## 2026-08-27 — Reject four candidate "second datasets"; reaffirm independently-collected Tier 2

- **Decision:** None of four externally-suggested datasets — a 2026 Kaggle "Fake Job Posting
  Detection" competition, DIFrauD's "Job Scams" domain, the Internship-Job-Scam-Dataset, and
  ScamShield — are adopted as Tier 2. The original independently-collected, provenance-labelled
  contemporary set (decided 2026-08-07, below) stands unchanged.

- **Options considered:**
  - (A) Adopt the Kaggle 2026 competition as a "primary modern benchmark" (per an external
    report's recommendation).
  - (B) Adopt DIFrauD's Job Scams split, since it is a real, peer-reviewed benchmark
    (Boumber, Qachfar & Verma, LREC-COLING 2024).
  - (C) Adopt the Internship-Job-Scam-Dataset for its three-level risk framing.
  - (D) Check each against its primary source before adopting any of them.

- **Why I chose this:** Two unattributed PDF reports (no named authors, no institutional
  affiliation) recommended these datasets, and one was suggested by my supervisor via a
  direct DIFrauD link. Rather than accept either at face value, I checked each dataset's own
  card/page directly. All four trace back to EMSCAD:
  - The Kaggle competition (kaggle.com/competitions/fake-job-posting) is a Computational
    Intelligence module assignment at Cardiff Metropolitan University — 12,001 rows, 18
    columns, 95.1%/4.9% class split (19.4:1, matching EMSCAD almost exactly), and its own
    reference list cites Vidros et al. (2017), EMSCAD's origin paper.
  - DIFrauD's dataset card states directly: "The Employment Scam Aegean Dataset, henceforth
    referred to as the Job Scams dataset..." — it is EMSCAD, cleaned and deduplicated to
    14,295 records, with every structured field discarded (only `text` and `label` remain).
  - The Internship-Job-Scam-Dataset's own card states it was "adopted from... the Employment
    Scam Aegean Dataset (EMSCAD)." Its "suspicious" class is partly built by relabelling
    existing legitimate EMSCAD text under a new class (`rule_augmented_suspicious_variant`),
    not new data.
  - ScamShield sources its job data from EMSCAD, mixed with unrelated SMS spam data and
    ~255 LLM-generated (Gemini) synthetic examples.

  None of these provide temporally independent 2026-era postings — using any of them as
  Tier 2 would test an EMSCAD-trained model against EMSCAD again, defeating the entire
  purpose of the temporal-transfer experiment. DIFrauD and the Internship dataset also
  strip structured metadata, which would make E2, E3 and E4 — the actual research
  contribution — impossible to evaluate on them regardless of the temporal question.

- **What I gave up:** A ready-made, no-collection-required Tier 2. None exists that meets
  both requirements (genuinely independent of EMSCAD, and metadata-rich enough for E2–E4).

- **Bonus finding:** The Internship-Job-Scam-Dataset's row preview independently confirms
  the correction below — its "English Teacher Abroad" rows carry `original_fraudulent: 0`,
  corroborating via an unrelated third party that this cluster is legitimate, not a fraud
  campaign as the original 2026-08-07 entry stated.

- **Revisit if:** A genuinely independent, metadata-preserving, 2026-era recruitment fraud
  dataset is found and its primary source confirms it is not EMSCAD-derived.

- **Self-check:** *Why does a dataset being real and peer-reviewed (DIFrauD) not automatically
  make it suitable as my Tier 2 — what two separate requirements does it fail?*

---

## 2026-08-27 — Correction to the 2026-08-07 duplicate-postings decision

- **Correction, not a new decision:** The entry below (2026-08-07, "Group duplicate postings
  before splitting the data") states the "English Teacher Abroad" cluster is an example of a
  *fraudulent* campaign repeated with small changes. **This is factually wrong.** Measured
  on the real CSV: the cluster (715 records under a text-prefix match; the largest
  exact-normalised group, 417 records) is **100% legitimate, 0% fraudulent.**

- **The decision itself still stands**, on independent grounds: the fraud class is
  separately measured at 40.3% duplicated (349 of 866 records in a duplicate group of
  size > 1), which alone justifies group-aware partitioning. Only the illustrative example
  in the original entry was wrong, not the reasoning.

- **Why this is logged as a correction rather than a silent edit:** the original entry is
  left exactly as written below, because a mistake caught and corrected is worth more in a
  viva than a record that was quietly fixed. If asked, the honest answer is "I stated the
  wrong example when I wrote this in August, found it wrong during the data audit, and
  corrected it without changing the underlying decision."

- **Self-check:** *What did I originally claim about the "English Teacher Abroad" cluster,
  what did the measurement actually show, and why didn't the error change the decision?*

---

## 2026-08-27 — Uniform "evaluable coverage" definition for C1–C6; defer C2 to Stage 4

- **Decision:** All six consistency rules now use one consistent definition of "evaluable"
  (both operands present, so the rule could actually attempt a comparison — not merely that
  text exists nearby). C1 and C3 get a same-day symmetric pattern fix (bounded vocabulary,
  same category as each other). C2 is deferred entirely to Stage 4 — its field coverage
  (88.4%) is reported as an explicit upper bound, with no evaluable figure until then.

- **Options considered:**
  - (A) Apply the loose definition (field present + text non-empty) to all six rules.
  - (B) Build a quick regex proxy for every rule, including C2.
  - (C) Apply the strict definition uniformly, with category-appropriate treatment: fix
    bounded-vocabulary rules now, defer the one open-vocabulary rule.

- **Why I chose this:** The original audit script measured "evaluable" two different ways —
  strict for C4–C6, loose for C1–C3 — which understated the true gap between field coverage
  and real coverage. Applying the loose definition everywhere (A) would have overstated
  coverage across the board. Building a proxy for C2 (B) was rejected specifically: C2's
  premise is that a place name in free text disagrees with the structured `location` field —
  an open-vocabulary problem (any place name on Earth), unlike C1/C3's bounded vocabularies
  (a fixed set of remote/on-site or employment-arrangement phrases). A quick C2 proxy would
  become a second, weaker implementation of the rule, guaranteed to disagree with the real
  Stage 4 location matcher.

  Measured result: C1 field coverage 100.0%, evaluable 10.5%. C2 field coverage 88.4%,
  evaluable deferred. C3 80.6% / 12.2%. C4 60.6% / 30.2%. C5 54.7% / 27.8%. C6 15.2% / 7.6%.
  Aggregate: 56.7% of postings evaluable by at least one rule (was falsely 100% under the
  old mixed definition); mean 0.88 of 6 rules evaluable per posting (was falsely 3.35).

- **What I gave up:** A same-day number for C2, and the comfortable but false impression
  that E4 covers nearly all postings. The honest picture is that E4's practical reach is
  much thinner than the original estimate implied — a real finding, not a data-quality
  failure, and one worth stating plainly in the dissertation rather than letting the
  original estimate stand uncorrected.

- **Also fixed in the same pass:** a duplicate-count bug (the audit script printed
  `n − n_unique`, the excess count, not true group-membership — corrected in both the
  overall and per-class figures; true count is 4,762 records / 26.6% in a duplicate group,
  not 3,505) and a missingness-calculation bug (every missing value was being counted twice).

- **Revisit if:** Stage 4 builds real lexicons for C1, C3–C6 — every provisional figure above
  must be re-measured against them, not assumed to hold. Stage 4 also builds C2's first real
  evaluable-coverage measurement.

- **Self-check:** *Why is C1 fixable with a same-day regex but C2 isn't, when both looked
  like the same kind of gap at first?*

---

## 2026-08-26 — Sharpen the explainability gap from "absent" to "never tested for faithfulness"

- **Decision:** My research gap on explainability does NOT claim that explanation is absent
  from fraud detection. It claims that, where explanation is used, it is shown as a few
  examples but never tested for whether it faithfully reflects the model.

- **Options considered:**
  - (A) Keep the stronger, simpler claim: "explainability is absent from fraud detection."
  - (B) Sharpen it: explanation is rare, and where present it is never tested for faithfulness.

- **Why I chose this:** While writing Chapter 2 I read Naudé et al. (2023), a fraud-domain
  paper that actually uses LIME. That single paper disproves the "absent" claim outright. If
  I had kept option A, an examiner holding Naudé could sink the sentence in seconds. Option B
  is not a retreat — it is stronger, because it survives Naudé and because it maps exactly
  onto what I actually built: my Objective 4 tests explanation faithfulness with
  comprehensiveness and sufficiency, which is the very thing Naudé never did. The gap and my
  contribution now line up perfectly.

- **What I gave up:** A punchier one-line gap. Traded for one that cannot be knocked over.

- **Revisit if:** I find a fraud-detection paper that already runs a systematic fidelity
  evaluation of its explanations — then the gap must narrow again to whatever they did not do.

- **Self-check:** *Why can't I say explainability is absent from fraud detection, and which
  paper forces the more careful wording?*

---

## 2026-08-26 — Cut Mohiddin et al. (2025) from the reviewed literature

- **Decision:** Mohiddin et al. (2025) is not cited in my literature review and does not
  appear in my summary table.

- **Options considered:**
  - (A) Include it to raise my paper count.
  - (B) Keep it as one weighted-down sentence.
  - (C) Cut it entirely.

- **Why I chose this:** The paper has no stated dataset, no reported metrics, and no clear
  protocol, and some of its citations look unreliable. A literature review is judged partly
  on the quality of what I choose to include. Putting an evidence-free paper in the same
  summary table as Akram (IEEE Access, Q1) and Naudé (AI & Society) drags down the whole
  table's credibility. The one "future work" point it offered is made better by Akram
  anyway. Including it adds risk without adding evidence, so it goes.

- **What I gave up:** One entry on my paper count. Not worth keeping at the cost of table
  credibility.

- **Revisit if:** A later, properly reported version of the same work appears.

- **Self-check:** *On what grounds did I exclude a paper from my review, and why is excluding
  weak work a strength rather than a gap?*

---

## 2026-08-26 — Structure the research gap as four gaps derived by comparison, not lifted from papers

- **Decision:** My Chapter 2 research gap is four distinct gaps: (1) text and metadata are
  never checked for agreement — my main gap; (2) explanations are rare and never tested for
  faithfulness; (3) evaluation is not always leakage-controlled; (4) output is a binary label
  rather than a graded, calibrated score.

- **Options considered:**
  - (A) State one single gap (consistency verification) and stop.
  - (B) Derive several connected gaps that each map to one of my objectives.

- **Why I chose this:** No single paper states these gaps — they only become visible when the
  studies are compared against each other, which is exactly what a gap analysis is supposed
  to do (derive, not quote). Four gaps also give each of my objectives something in the
  literature to answer: the consistency gap → O1/O3, the faithfulness gap → O4, the leakage
  gap → O2/O5, the graded-output gap → O4. It makes the whole thesis hang together.

- **What I gave up:** A single, very sharp one-line gap. But gap (1) still carries that role;
  the other three support it rather than dilute it.

- **Revisit if:** One of the four turns out to be already solved in a paper I later read —
  then that gap is removed and the objective it fed is re-justified.

- **Self-check:** *Where did my four gaps come from, if no single paper states them — and
  which objective does each gap justify?*

---

## 2026-08-07 — Write objectives so that none of them assumes its own result

- **Decision:** My objectives say what I will *measure*, not what the measurement will
  *show*. Objective 3 now reads "quantify the extent to which it changes performance"
  instead of the earlier "achieving a measurable improvement".

- **Options considered:**
  - (A) Keep the original wording. It sounds confident and ambitious.
  - (B) Neutral wording focused on measurement.

- **Why I chose this:** I realised my original Objective 3 had written my expected result
  into the objective itself. If my multi-signal model turns out not to beat the baseline,
  then under the old wording I would have failed my own objective — even if I did
  everything else correctly. That felt wrong to me. A negative result is still a real
  result: finding that consistency features don't help would be useful knowledge and I
  could report it honestly. So I should not set myself up so that good work can look like
  failure. An objective is a promise about what I will investigate, not a prediction of
  what I will find.

- **What I gave up:** Wording that sounds more impressive to someone skimming the document.

- **Revisit if:** Never. This is a correctness issue, not a matter of taste.

- **Self-check:** *Why is "achieving an improvement" a bad way to word a research objective?*

---

## 2026-08-07 — Use four evidence categories for measurement, not five

- **Decision:** The taxonomy I actually measure has four categories — E1 text/content cues,
  E2 identity and contact cues, E3 metadata completeness, E4 text–metadata consistency. The
  external company-presence check still exists inside my API as a supporting qualitative
  feature, but it is excluded from the ablation analysis and from all quantitative results.

- **Options considered:**
  - (A) Five categories, with external presence measured like the rest.
  - (B) Five categories, but redefine external presence as an internal "employer
    plausibility" score built from `company_profile` and `industry`.
  - (C) Four measured categories, with the external check demoted to API-only.

- **Why I chose this:** Two problems killed the first two options. First, EMSCAD has no
  separate company-name field — the only employer information is free text inside
  `company_profile` — and the postings are from 2012 to 2014. If I search the web today for
  a company mentioned in a twelve-year-old posting, whatever comes back is noise, not
  evidence. I would be measuring something meaningless and reporting it as a signal.
  Second, option B looked safer but was actually worse for my ablation: it would have used
  `company_profile`, which E2 already uses. Two categories drawing on the same field means
  I cannot separate their contributions, so my ablation numbers would be contaminated. I
  would rather have four categories I can measure cleanly than five where one is fiction.
  I still keep the external check in the artefact because it is genuinely useful to a real
  job seeker looking at a real posting today — it just doesn't belong in my results.

- **What I gave up:** A fifth category that sounded impressive in my proposal, and any
  quantitative claim I could have made about external verification.

- **Revisit if:** My Tier 2 collection works well at scale. A live external check on a
  posting from 2026 *is* meaningful, so I could report it qualitatively there.

- **Self-check:** *Why can't I evaluate the external company-presence check on EMSCAD, and
  why would folding it into E2 have damaged my ablation?*

---

## 2026-08-07 — Use class weighting for both models, not SMOTE for one and class weighting for the other

- **Decision:** Both my baseline and my improved model use class weighting, with identical
  settings, to handle the 4.8% fraud class. SMOTE stays in the project only as a clearly
  labelled extra experiment on the baseline.

- **Options considered:**
  - (A) SMOTE for both models, following Akram et al. (2024).
  - (B) SMOTE for the baseline, class weighting for the improved model — this is what my
    first draft actually said.
  - (C) Class weighting for both, SMOTE as a side experiment.

- **Why I chose this:** This is probably the most important decision in my whole design,
  and I nearly got it wrong. My entire research claim is that adding multi-signal evidence
  and consistency verification improves credibility scoring. To show that, my two models
  must differ in *only* the things I am testing. Under option B they would have differed in
  three ways at once — text representation, structured features, *and* imbalance strategy.
  If the improved model then performed better, I could not say why. Someone could ask "how
  do you know it wasn't just the different balancing?" and I would have no answer. My
  central claim would be untestable, which is worse than being wrong.

  The second reason is about my output. My headline deliverable is a *calibrated* 0 to 100
  score, not a label. SMOTE creates synthetic minority examples, which shifts the predicted
  probability distribution away from the real one. Since the meaning of my score depends on
  those probabilities being trustworthy, protecting calibration matters more to me than
  squeezing out a slightly higher F1. I keep SMOTE as a separate arm so I can still compare
  against Akram et al., but it is reported separately and never mixed into the main
  comparison.

- **What I gave up:** Direct number-for-number comparability with SMOTE-based published
  results, and possibly a little raw F1.

- **Revisit if:** Calibration turns out to be robust to SMOTE in my setting, or if the
  supplementary arm shows a large and consistent advantage I can't ignore.

- **Self-check:** *Give the two separate reasons I chose class weighting — one about
  comparison validity, one about calibration.*

---

## 2026-08-07 — Group duplicate postings before splitting the data

- **Decision:** Before splitting, I normalise the description text, compute a content hash,
  and make sure every record sharing a hash goes into the same partition.

- **Options considered:**
  - (A) Plain stratified random split, which is what my proposal said.
  - (B) Delete all duplicates.
  - (C) Group-aware split — keep the duplicates but never let a group span the boundary.

- **Why I chose this:** The dataset profile shows 17,880 records but only about 15,100
  unique descriptions, so roughly 2,700 postings repeat. Some of these are the same
  fraudulent campaign posted over and over with small changes — the "English Teacher
  Abroad" cluster is a clear example. If I split randomly, near-identical fraudulent
  postings land in both my training set and my test set. My model then doesn't learn what
  fraud looks like; it memorises specific strings and recognises them again at test time. I
  would get a high F1 that means nothing. I chose option C over option B because deleting
  duplicates changes the real class balance of the dataset, whereas grouping keeps the data
  intact and only controls where records are allowed to go.

  > ⚠️ **Correction, 2026-08-27:** the "English Teacher Abroad" example above is factually
  > wrong — measured on the real CSV, that cluster is 100% legitimate, 0% fraudulent. See
  > the correction entry dated 2026-08-27 above. The decision itself still stands, justified
  > independently by the fraud class being separately measured at 40.3% duplicated.

- **What I gave up:** Comparability with published EMSCAD results that did not control for
  this. My numbers will probably look lower than theirs. I have decided to treat that as a
  finding worth reporting rather than a problem to hide — if leakage control lowers scores,
  that says something about the published figures.

- **Revisit if:** The audit shows duplication is actually negligible. I doubt it, but the
  ~2,700 figure is an estimate from a profiler and I have not measured it myself yet.

  > ⚠️ **Update, 2026-08-27:** now measured. 4,762 records (26.6%) sit in a duplicate group
  > under exact-normalised hashing; the fraud class is disproportionately duplicated (40.3%
  > vs 25.9% for legitimate). The near-duplicate grouping *method* itself is still an open
  > decision — see Decision 0.2 in `PROJECT_PLAN.md` / `workplan.md`.

- **Self-check:** *What exactly goes wrong if I use a plain random split on EMSCAD, and why
  did I group duplicates instead of deleting them?*

---

## 2026-08-07 — Use a train/validation/test split instead of 80:20

- **Decision:** Roughly 70:15:15. The validation set is used for transformer
  hyperparameters, the decision threshold, and fitting the calibrator. The test set is used
  once, at the end, for reporting.

- **Options considered:**
  - (A) 80:20 train/test, as in my proposal.
  - (B) 70:15:15 train/validation/test.
  - (C) Nested cross-validation.

- **Why I chose this:** Once I listed out everything I need to fit, the problem became
  obvious. I have to choose transformer hyperparameters, pick a decision threshold, and fit
  a probability calibrator. That is three separate things, and none of them may touch the
  test set — if they do, my final numbers are optimistic and I have no clean estimate of how
  the system performs on unseen data. With only a train/test split there is simply nowhere
  honest to fit them. Option C is more rigorous statistically, but it multiplies my compute
  and complexity, and I am one person on a laptop with a fixed deadline. A separate
  validation partition solves the actual problem at a cost I can afford.

- **What I gave up:** Some training data, and some robustness compared with nested CV.

- **Revisit if:** The fraud class in my test partition turns out too small for stable
  estimates even across five seeds.

- **Self-check:** *Name the three things I fit on the validation set, and explain why none
  of them can be fitted on the test set.*

---

## 2026-08-07 — Add an explicit probability calibration stage

- **Decision:** I fit a probability calibrator — Platt scaling or isotonic regression,
  chosen on validation performance — and map the calibrated probability to my 0 to 100
  credibility score. I report Brier score, expected calibration error, and a reliability
  curve.

- **Options considered:**
  - (A) Map the raw model probability straight to 0–100, as in my proposal.
  - (B) Fit a calibrator first, then map.

- **Why I chose this:** I noticed a gap in my own design. My training labels are binary —
  fraudulent or legitimate — but my output is a graded score, and nothing in my original
  plan connected the two. If I just rescale a raw model probability into a number between 0
  and 100, then a score of 70 doesn't actually mean anything specific; it is the model's
  uncalibrated output stretched onto a different axis. Classifiers, especially neural ones,
  are often overconfident, so those raw numbers can be badly off even when the ranking is
  good. Calibration is what makes the number defensible: after it, a score around 70 should
  correspond to roughly the right proportion of postings actually being legitimate, and I
  can test that with a reliability curve. Without this stage my main deliverable would have
  had no validation method at all.

- **What I gave up:** Pipeline simplicity — one more component that can fail or be
  misconfigured.

- **Revisit if:** Neither calibrator improves reliability over the raw probabilities. In
  that case I report that honestly and justify using the identity mapping.

- **Self-check:** *Why is a binary training label a problem for a 0–100 output, and how does
  calibration fix it?*

---

## 2026-08-07 — Test explanation quality computationally instead of asking human reviewers

- **Decision:** I evaluate my explanations using comprehensiveness and sufficiency
  (deletion and insertion tests) plus a rule-consistency check. No human participants.

- **Options considered:**
  - (A) Collect feedback from reviewers or users on whether explanations are helpful.
  - (B) Computational fidelity testing only.
  - (C) Both.

- **Why I chose this:** There was a practical reason and a better reason. The practical one
  is that involving human participants means a participant ethics application plus
  recruitment, scheduling and analysis, and I don't have room for that in my remaining
  timeline. The better reason is what each approach actually tests. Asking people whether an
  explanation *feels* helpful tells me about presentation. Fidelity testing tells me whether
  the explanation reflects what the model actually did. That second property is the one that
  matters for safety: an explanation that sounds convincing but doesn't match the model's
  real reasoning is worse than giving no explanation at all, because it makes the user
  confident for the wrong reasons. Fidelity testing is also quantitative and reproducible,
  which suits a dissertation better than a small unrepresentative user study would.

- **What I gave up:** Any evidence about whether real job seekers find my explanations
  *useful*. That is a genuine limitation and I state it as one rather than pretending
  fidelity testing covers it.

- **Revisit if:** My timeline opens up and ethics approval turns out to be quick. A small
  supervised usability round would strengthen Objective 4.

- **Self-check:** *Why is a plausible-but-unfaithful explanation worse than no explanation?*

---

## 2026-08-07 — Keep EMSCAD and add a small contemporary validation set (two-tier strategy)

- **Decision:** EMSCAD is Tier 1 and does all my training, tuning and benchmarking. A small
  independently collected set of 300 to 600 contemporary postings is Tier 2 and is used only
  as a held-out temporal validation set. The two are never merged.

- **Options considered:**
  - (A) EMSCAD only.
  - (B) Replace EMSCAD with a modern scraped dataset.
  - (C) Merge modern data into EMSCAD and train on everything.
  - (D) Two tiers, kept separate.

- **Why I chose this:** EMSCAD is from 2012 to 2014, and it is now 2026. Fraud has changed a
  lot in that time — in particular, scammers now use language models to write postings,
  which removes the bad grammar and clumsy phrasing that older detectors relied on. So
  option A would leave me with an artefact demonstrably tuned to a job market that no longer
  exists. But I couldn't take option B either, because EMSCAD is the benchmark every paper
  in my literature review uses; if I drop it, I lose the ability to compare my results with
  anyone. Option C is worse than both — mixing eras contaminates the benchmark and makes my
  numbers uninterpretable, since I could never tell which era drove a result. Option D gives
  me both things at once: full comparability with the literature on Tier 1, and a temporal
  generalisability result on Tier 2 that, as far as I can see, no paper in my review has
  produced. That turns my dataset's biggest weakness into a contribution.

  > ✅ **Reaffirmed, 2026-08-27** after checking four externally-suggested alternative
  > "second datasets" against their primary sources — all four turned out to be EMSCAD
  > derivatives. See the decision entry dated 2026-08-27 above. This decision was not
  > weakened by that check; if anything it is more clearly correct now.

- **What I gave up:** Time. Tier 2 collection is my slowest task and my main schedule risk,
  especially the fraudulent side. I also have limited statistical power on Tier 2 because
  the sample is small, so I report confidence intervals there.

- **Revisit if:** Collecting the fraudulent side proves impossible in the time I have. My
  fallback is to report Tier 2 qualitatively and state the limitation openly.

  > ⚠️ **Status, 2026-08-27:** deadline confirmed at ~1 month away. Tier 2 collection has
  > not started. This fallback clause is now live and under active consideration — see
  > `project.md` open questions.

- **Self-check:** *Why didn't I just replace EMSCAD with modern data, and why can't I merge
  the two tiers?*

---

## 2026-08-07 — Label Tier 2 by where the data came from, and test for source leakage

- **Decision:** Legitimate postings come from employers' own applicant tracking system
  endpoints and official public job feeds — legitimate by construction. Fraudulent postings
  come from documented scam repositories and advisories, and only where the original posting
  text is reproduced. I also train a classifier to predict the *source* rather than the
  label, and report what it scores.

- **Options considered:**
  - (A) Collect postings and annotate them myself.
  - (B) Label by provenance.
  - (C) Label by provenance without any leakage check.

- **Why I chose this:** Option A isn't realistic. For a genuinely ambiguous posting I have
  no way to establish ground truth on my own authority — I would just be guessing, and my
  guesses would become my labels, which is circular. Provenance labelling removes my
  judgement from the process entirely: if a posting came from a company's own Greenhouse
  board it is legitimate by definition, and if a consumer protection body has documented it
  as a scam then it is fraudulent by report.

  But provenance labelling brings a serious danger of its own, which is why I rejected
  option C. If all my legitimate postings come from one kind of source and all my fraudulent
  ones from another, my model can learn to recognise the *source formatting* rather than
  fraud, and it would score brilliantly while meaning absolutely nothing. That failure is
  invisible in normal metrics — it looks like success. The source probe is how I detect it,
  so it isn't optional. I also normalise aggressively and exclude features whose
  availability differs systematically by source.

- **What I gave up:** Coverage of borderline cases. My Tier 2 set will contain clearer
  examples than the real world does, which probably makes it an optimistic test. I say so.

- **Revisit if:** The source probe scores near-perfect even after normalisation. Then I
  restrict Tier 2 to text-only features, or report it qualitatively.

- **Self-check:** *What is source leakage, why would it be invisible in my normal metrics,
  and how does the probe catch it?*

---

## 2026-08-07 — Drop the `in_balanced_dataset` column entirely

- **Decision:** I exclude it from the feature space completely.

- **Options considered:**
  - (A) Keep it as a feature.
  - (B) Drop it.

- **Why I chose this:** This column marks whether a record was included in the dataset
  authors' own pre-built balanced subset. That is information about how the dataset was
  assembled — it says nothing whatsoever about the job posting itself. A real job seeker
  looking at a real vacancy would never have access to anything like it. Including it would
  let my model pick up on an artefact of dataset construction, which is straightforward
  leakage, and any performance it bought me would be fake.

- **What I gave up:** Nothing of value.

- **Revisit if:** Never.

- **Self-check:** *What does `in_balanced_dataset` actually describe, and why does that make
  it leakage?*

---

## 2026-08-07 — Extract contact and media tokens before stripping HTML

- **Decision:** My preprocessing order is: first count `#EMAIL_#`, `#PHONE_#` and `#URL_#`
  tokens along with image references and link counts, *then* strip the markup.

- **Options considered:**
  - (A) Strip HTML first, which is the conventional order in most tutorials.
  - (B) Extract first, then strip.

- **Why I chose this:** When EMSCAD was anonymised, contact details weren't deleted — they
  were replaced with hashed placeholder tokens that are still sitting inside the description
  text. Those tokens are the basis of my whole E2 identity and contact category: whether a
  posting pushes the applicant to email or phone directly, instead of applying through the
  platform, is a real fraud signal. If I strip markup first, those tokens go with it and I
  destroy an entire evidence category before I have even computed it — and worse, I would
  probably not notice, because the pipeline would still run and just produce zeros.

- **What I gave up:** Nothing. This is an ordering constraint, not a trade-off.

- **Revisit if:** Never.

- **Note to self:** The email *domain* cannot be recovered, because hashing destroys it.
  That means I cannot reproduce Goud and Reddy's free-webmail-domain feature on EMSCAD. I
  document this as a dataset limitation rather than quietly leaving it out.

- **Self-check:** *What breaks if I strip HTML first, and why wouldn't I notice?*

---

## 2026-08-07 — Make raw text the primary API input, with URL support best-effort only

- **Decision:** My `/score` endpoint takes raw posting text as its main input path. URL
  ingestion is secondary and only supported for sources that permit automated retrieval.

- **Options considered:**
  - (A) URL-first, as described in my proposal.
  - (B) Text-first, URL optional.

- **Why I chose this:** My proposal assumed a user would paste a LinkedIn or Indeed link and
  the system would fetch it. There are two problems with that. Automated retrieval from the
  major recruitment platforms breaches their terms of service, which I should not be
  building a university project on. And technically it is fragile — page structures change
  without warning and scrapers break constantly. If my primary input path depends on that,
  then my entire deliverable can stop working for reasons that have nothing to do with my
  research. Raw text always works, requires no permission, and keeps the artefact stable.

- **What I gave up:** Convenience for the end user, which was honestly part of the original
  appeal of the idea.

- **Revisit if:** A sanctioned API route to posting content becomes available.

- **Self-check:** *Give the two reasons — one legal, one technical — that URL input isn't my
  primary path.*

---

# Pending decisions (not yet made)

> ✅ **Resolved, 2026-09-20:** the scope-cut decision, the rules-only baseline question, the
> frozen-vs-fine-tuned DistilBERT question, the "5 seeds" definition question, and the
> near-duplicate grouping method (Decision 0.2) are all now resolved — see the entries dated
> 2026-09-20 above. Only two items remain genuinely open below.

## Success thresholds for each objective

- **The question:** What actually counts as success for each objective? These are still
  unset in `methodology.md`.
- **Constraint:** I must agree these with my supervisor **before** I see any results.
  A threshold set after seeing results is not a threshold.
- **Decide by:** Before Stage 9. **Now urgent** given the confirmed ~1 month deadline —
  schedule this conversation with my supervisor immediately, in parallel with Stage 2/3
  work, not queued up later.

## Tier 2 ethics approval status

- **The question:** Has the institutional ethics application for Tier 2 primary data
  collection actually been submitted? What is the NIBM/Coventry process and timeline?
- **Why it matters:** Tier 2 collection is starting now (see the reduced-collection
  decision, 2026-09-20, above) — this can no longer sit as a background open question.
- **Decide by:** Immediately — check status today.
