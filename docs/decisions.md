# decisions.md — Design Decisions & Rationale

_Last updated: 2026-10-08_

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

## 2026-10-08 — Stage 6 complete: isotonic selected over Platt, with an honest caveat about what its ECE=0.000 actually means

- **Results on validation (seed-0 DistilBERT+evidence model, n=2682):**

  | Calibrator | Brier | ECE |
  |---|---|---|
  | None (raw) | 0.0275 | 0.0231 |
  | Platt | 0.0212 | 0.0050 |
  | Isotonic | 0.0199 | ~0.0000 |

  No disagreement between the two metrics — isotonic wins on both, cleanly. The reliability
  curve shows the raw model is genuinely overconfident (predictions sit below the diagonal
  through the mid-range, then jump sharply only in the 0.9–1.0 bin), and both calibrators
  visibly correct it.
- **Decision:** isotonic selected, saved to `models/stage6_calibrator.joblib`.
- **The caveat, stated plainly:** isotonic's near-zero ECE is partly an artefact of fitting
  and evaluating on the SAME validation set. Isotonic regression is a flexible, non-
  parametric, many-degrees-of-freedom fit — several of its reliability bins show mean
  confidence matching the actual fraction positive to 3+ decimal places, which is exactly
  what you'd expect from a method with enough flexibility to closely trace its own
  training sample's empirical curve. Platt (a single-parameter logistic fit) has much less
  room to do this, which is part of why its ECE (0.005) is non-zero but still good. This
  does not mean isotonic was the wrong pick — it won on Brier too, a different and less
  gameable metric, so the preference is real, not just an artefact. But the exact ECE=0.000
  number should not be quoted as the model's true calibration error; it is a validation-set
  selection statistic, not the final answer.
- **Why this isn't a problem for the project's "test used once" guardrail:** this is
  precisely the situation that guardrail exists for. The calibrator was chosen here, on
  validation, exactly once. Stage 9's one-time test-set evaluation applies this same frozen
  isotonic calibrator (not re-selected, not re-fit) and reports ITS Brier/ECE — that number,
  not this one, is what Chapter 4 should present as the real calibration result.
- **Risk bands:** provisional terciles (Low 0–33, Medium 34–66, High 67–100) on the
  calibrated 0–100 score. Not validated against any external standard — logged as such
  because `PROJECT_PLAN.md` already records success thresholds as open pending supervisor
  input. Revisit if a supervisor contact window opens.
- **What I gave up:** a clean, uncomplicated "ECE went from 0.023 to 0.000" headline
  number. Reporting the honest version (real but likely overstated at exactly 0, confirm
  on test) costs a cleaner story in exchange for not overclaiming in Chapter 4.
- **Self-check:** *Why can isotonic regression report a near-perfect ECE on the same data
  it was fit on, when Platt scaling can't do the same thing nearly as easily — and what
  does that imply about which number you trust more going into Stage 9?*

---

## 2026-10-08 — Stage 5 main comparison complete: DistilBERT + structured evidence beats both baselines; ablation seed count (Decision 2, 2026-10-06) closed at 1 seed, from measured timing

### 1. Main comparison result (O3)

3 seeds (0/1/2), 5 epochs each (the measured peak — see the epoch-count entry above),
identical validation split, `pos_weight` class imbalance handling:

| Model | Precision | Recall | F1 (fraud) | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|
| TF-IDF + LogReg (baseline) | 0.464 | 0.692 | 0.556 | 0.655 | 0.931 |
| TF-IDF + RF (baseline) | 0.881 | 0.362 | 0.513 | 0.682 | 0.940 |
| DistilBERT + structured evidence | 0.634 ± 0.050 | 0.713 ± 0.004 | **0.671 ± 0.030** | 0.710 ± 0.018 | 0.934 ± 0.008 |

F1 improves over both baselines (Δ +0.115 vs. LogReg, +0.158 vs. RF), with a precision/
recall balance that sits between the two baselines rather than reproducing either one's
extreme trade-off (LogReg: high recall/low precision; RF: high precision/low recall).
ROC-AUC is roughly level with both baselines (0.934 vs. 0.931/0.940) — the gain is
concentrated in F1/PR-AUC, not ROC-AUC, worth noting honestly in Chapter 4 rather than
implying a uniform improvement across every metric.

**This was not cherry-picked:** 3 seeds were pre-committed (2026-09-20 decision) before
this run, and the full set is reported above, not a selected best-of-3.

### 2. Ablation seed count (closing the 2026-10-06 conditional decision)

- **Context:** 2026-10-06's Decision 2 left the Stage 9 ablation seed count (5 arms: E1,
  E2, E3, E4, `has_company_logo`) conditional on a real per-epoch timing, to be measured on
  "Day 3." That timing is now in hand: ~324.5s/epoch average across the two clean 5-epoch
  runs (seed 1: 325.6s avg; seed 2: 323.4s avg).
- **The arithmetic:** at 5 epochs/arm (the same count just locked in for the main
  comparison, for a fair like-for-like ablation), one full pass of all 5 ablation arms
  costs 5 arms × 5 epochs × 324.5s ≈ 135 minutes (~2.25 hours) per seed. At 3 seeds, that's
  ~6.75 hours of GPU time; at 1 seed, ~2.25 hours.
- **Decision:** 1 seed per ablation arm, not 3. Stage 9 (per `PROJECT_PLAN.md` §0.5, Day 4)
  already has to fit the full one-time test-set evaluation, the Tier 2 temporal-transfer
  test, the source-probe leakage test, Stage 7's SHAP explanations (already flagged in the
  plan as its own time risk), and Stage 8's API wiring and demo — all on one day already
  named as "the most likely day to run over." ~6.75 hours for ablation alone does not
  fit alongside that; ~2.25 hours does.
- **What I gave up:** a per-category variance estimate for the ablation — each arm's Δ
  will be a single point, not a mean ± SD like the main comparison gets. That is a real,
  disclosed reduction in rigor for the ablation specifically, not a silent one; it should
  be stated as a limitation wherever the ablation results are reported, not left implicit.
  The main 3-seed comparison above is unaffected by this — it's already complete.
- **Self-check:** *Why is it still defensible for the main comparison to report mean ± SD
  over 3 seeds while the ablation arms report only 1 seed each, when both are measuring
  model performance? What would you say if an examiner called this inconsistent?*

---

## 2026-10-08 — Stage 5 epoch count resolved: 5 epochs, from a measured peak, not a guess; checkpoint filenames fixed to not overwrite across seeds

- **Context:** the 6-epoch probe (seed 0) gave a real learning curve instead of a guess:

  | epoch | val F1 | ROC-AUC | train loss |
  |---|---|---|---|
  | 0 | 0.404 | 0.908 | 0.744 |
  | 1 | 0.580 | 0.941 | 0.381 |
  | 2 | 0.540 | 0.932 | 0.220 |
  | 3 | 0.607 | 0.945 | 0.125 |
  | **4** | **0.667** | 0.942 | 0.107 |
  | 5 | 0.620 | 0.934 | 0.058 |

- **Decision:** 5 epochs (indices 0–4) for the main 3-seed comparison. F1 peaked at epoch
  4 and fell at epoch 5 while train loss kept dropping sharply (0.107 → 0.058) — model
  still fitting the training data harder, validation getting worse. That is the standard
  signature of overfitting onset, not noise (epoch 2's smaller dip, by contrast, recovered
  the next epoch — ordinary run-to-run variance, not a trend reversal).
- **Why this resolves the earlier "4 vs. probe first" decision correctly:** the probe
  (logged above, same date) was taken specifically so the epoch count wouldn't be picked
  for speed before confirming convergence — this is that confirmation. 4 epochs would have
  stopped short of the real peak; 6+ would have kept training past it for no benefit.
- **A reproducibility note, logged honestly:** the first --epochs 4 run's own epoch-3
  result (F1 0.589, same seed 0) does not exactly match the 6-epoch probe's epoch-3 result
  (F1 0.607), despite nominally identical settings. This is expected GPU non-determinism
  (cuDNN/attention kernels aren't bit-exact across runs unless deterministic mode is
  explicitly forced, which this script doesn't do) — not a bug, and not a reason to distrust
  the peak-then-decline trend, which is far larger than this run-to-run noise. Worth a
  sentence in Chapter 3 if asked why two "identical" runs differ slightly.
- **Checkpoint-filename bug caught before it caused damage:** the script originally saved
  the best checkpoint to one fixed filename regardless of `--seed`, which meant running
  seed 1 next would have silently overwritten seed 0's already-good checkpoint with no
  warning. Fixed to seed-suffixed filenames
  (`distilbert_fused_state_dict_seed{N}.pt` etc.) before any further seed was run. Seed 0's
  checkpoint, already on disk from the probe (the only run whose best epoch happens to be
  epoch 4, exactly what was decided), is reused as seed 0 of the final 3-seed comparison
  rather than retrained — the checkpoint-on-best-F1 design meant it already represents the
  trained-to-peak result, so re-running it would cost ~22 minutes to reproduce (not exactly,
  per the note above) a result already in hand.
- **What I gave up:** exactness. Seed 0's "official" checkpoint was produced inside a
  6-epoch run rather than a clean standalone 5-epoch run — methodologically equivalent
  (same code path trains epoch 4 identically either way) but not identical bytes, given the
  non-determinism noted above. Chosen over spending ~22 more minutes to replace a result
  that would differ only by run-to-run GPU noise anyway.
- **Self-check:** *Why does train loss still falling while validation F1 falls count as
  stronger evidence of overfitting than validation F1 falling alone — what would it mean if
  train loss had also started rising at epoch 5?*

---

## 2026-10-08 — Stage 5 epoch count for the main comparison: delegated decision, probe to 6 epochs before locking the 3-seed run

- **Context:** the first real (full-dataset) DistilBERT+evidence run, 4 epochs, 1 seed,
  showed validation F1 still rising each epoch (0.412 → 0.566 → 0.569 → 0.589) while train
  loss kept falling fast (0.743 → 0.125). That result already beats both baselines
  (LogReg F1 0.556, RF F1 0.513), which is encouraging, but 4 epochs was an arbitrary
  starting number, not a measured stopping point — I hadn't yet seen whether F1 keeps
  climbing, plateaus, or starts falling (overfitting) past epoch 3. I asked which way to
  resolve this and was given full authority to decide ("I give you full power to take the
  right decision").
- **Options considered:** (A) lock in 4 epochs now and spend the saved time running seeds
  1 and 2 at that count (~45 min for the full 3-seed main comparison); (B) spend one more
  run (fresh, not resumed — the script doesn't support checkpoint-resume — so a full
  6-epoch run, ~33 min) on seed 0 alone first, to see epochs 4 and 5 before deciding the
  final count for all 3 seeds.
- **Why B:** O3 ("does the fused evidence improve on text-only detection") is one of this
  project's core research questions. The baseline models (LogReg, RF) were each fit to
  their own natural stopping point by their solvers in a single call — they were not cut
  short. If DistilBERT's epoch count is picked for speed before confirming it has actually
  converged, the O3 comparison silently becomes "undertrained-DistilBERT vs. fully-fit
  baseline," a different and weaker question than the one O3 asks, and that bias would be
  invisible in the final numbers unless I can point to the epoch curve and say where it
  leveled off. The checkpoint-on-best-F1 mechanism already built into the script means
  there is no downside to running longer: if epoch 5 or 6 is worse, the saved checkpoint
  stays at whichever epoch was actually best, so the extra 33 minutes either confirms 4
  was already close to optimal, or catches a real gain I would otherwise have left on the
  table for all 3 seeds.
- **What I gave up:** about 30 extra minutes today, and the possibility that this was
  unnecessary caution if epoch 4 turns out to already be the peak. Given this decision
  feeds a core RQ and the cost is small relative to the time already available this week,
  that trade was worth taking.
- **Self-check:** *Why does training the baseline models "to convergence" (via their
  solver's own stopping rule) and training DistilBERT for a fixed, arbitrarily-chosen
  epoch count threaten the O3 comparison's fairness, and what does the checkpoint-on-
  best-F1 mechanism do to make "just run a few more epochs to check" a low-risk way to
  resolve that?*

---

## 2026-10-08 — Stage 5 improved-model fusion: E1 kept as an explicit structured feature, not left implicit in DistilBERT's text input; pos_weight used as loss-level class-imbalance control

- **Context:** writing `src/models/train_distilbert.py` (the O3 "DistilBERT + structured
  evidence" model) required deciding exactly what goes into the fused feature vector
  alongside DistilBERT's text embedding, and how to carry the "identical class weighting"
  rule (2026-08-07) across to an architecture where sklearn's `class_weight="balanced"`
  doesn't apply.

### 1. E1 (suspicious-phrase lexicon) is included as a structured feature, even though DistilBERT reads the same text directly

- **Options considered:** (A) leave E1 out of the structured vector — DistilBERT already
  sees the raw words the lexicon matches against, so including E1 too looks like feeding
  the model the same information twice; (B) include E1 as a structured feature exactly
  like E2/E3/E4.
- **Why B:** two reasons. First, decisions.md (2026-10-06, Decision 2) already names E1 as
  one of the five leave-one-category-out ablation arms (E1, E2, E3, E4, `has_company_logo`)
  — that only makes sense if E1 is a distinct, removable *input* to the fused model, not
  something sitting implicitly inside the token sequence where it can't be ablated without
  also removing the text itself. Second, a hand-coded lexicon match is a much lower-
  variance signal than whatever DistilBERT might or might not learn to extract from the
  same tokens in a short fine-tuning run — handing the model the explicit flag is a
  deliberate inductive bias, not strictly redundant information.
- **What I gave up:** a cleaner information-theoretic story ("every structured feature adds
  genuinely new information DistilBERT couldn't get from the text alone"). E1 doesn't
  satisfy that; E2/E3/E4 do (they come from metadata fields DistilBERT's text input never
  sees). This is now a stated asymmetry inside "structured evidence," not something to
  discover for the first time at the viva.
- **Self-check:** *If ablating E1 removes the lexicon flag but DistilBERT still sees the
  same words either way, what exactly does the E1 ablation arm measure — and how is that
  different from what the E2/E3/E4 ablation arms measure?*

### 2. Class imbalance in the DistilBERT arm: `pos_weight` in `BCEWithLogitsLoss`, not a literal translation of `class_weight="balanced"`

- **Options considered:** (A) try to replicate sklearn's exact "balanced" formula inside
  the PyTorch loss; (B) use `pos_weight = n_negative / n_positive` on the training fold,
  the standard PyTorch idiom for binary class imbalance, documented as equivalent in
  principle rather than identical in formula.
- **Why B:** sklearn's `class_weight="balanced"` reweights both classes by
  `n_samples / (n_classes * n_samples_class)`; `pos_weight` only reweights the positive
  term inside `BCEWithLogitsLoss`. There is no architecture-neutral way to make these
  numerically identical — they operate on different loss functions entirely. Option A would
  have produced a false sense of exactness without actually matching anything.
- **What I gave up:** the ability to claim the baseline and improved models use literally
  the same class-weighting formula. They use the same *principle* (upweight the minority
  class by its training-fold imbalance ratio), applied at the point each architecture
  allows it to be applied. The controlled-comparison claim in Chapter 3/4 should say exactly
  that, not overstate it as "identical."
- **Self-check:** *Why can't `class_weight="balanced"` and `pos_weight` be made numerically
  identical, and does that difference threaten the "both arms differ in only one thing"
  guardrail, or not?*

---

## 2026-10-08 — Stage 4 lexicon design: delegated decision on tuning-contamination risk and two out-of-scope patterns

- **Context:** building the real C1, C3–C6 lexicons raised a risk I flagged before writing
  any code: the only human-labelled signal I have about these rules is the 200-posting
  Stage 2 disagreement sample. Tuning the new lexicons row-by-row against it until they
  agreed with my own prior manual judgements would be circular — the same failure mode as
  "a threshold set after seeing results is not a threshold," just applied to rule *design*
  instead of a numeric threshold. Separately, the Stage 2 audit surfaced two inconsistency
  patterns that don't fit anywhere in C1–C6: a title-vs-body role mismatch, and a
  company_profile-vs-description employer mismatch. I asked for a decision on both and was
  given full authority to resolve them myself ("do the best and most suitable way... take
  the best decision carefully").
- **Decision (lexicon design):** every C1, C3–C6 lexicon is designed on general linguistic
  principle — what a phrase actually asserts, checked against real matched text — not by
  checking agreement with the 200-posting sample. The disagreement notes
  (`reports/stage2_disagreements_for_review.txt`) were read once for qualitative inspiration
  about *categories* of failure (e.g. "topic mention vs. genuine claim"), never re-opened as
  a row-by-row tuning target while writing or adjusting a pattern.
- **Decision (two out-of-scope patterns):** neither becomes a new rule this stage. C1–C6 is
  the taxonomy already defined and partially validated; adding a rule now, after seeing
  these two specific cases, would be a post-hoc scope change driven by what the data showed
  rather than a decision made in advance. Both are logged as a named limitation /
  future-work item instead (see `methodology.md`, Stage 4 section) — real, worth stating,
  not quietly dropped.
- **What I gave up:** a stronger-sounding claim that the real lexicons "agree with human
  judgement" on the audit sample, which would have been bought by tuning to that sample and
  would not have been a fair claim to make. Also gave up two more C-rules that might have
  caught genuine inconsistencies, in favour of not changing the taxonomy's scope reactively.
- **Self-check:** *Why would tuning a new lexicon's design against the 200-posting
  disagreement sample be the same category of error as setting a threshold after seeing
  results, even though no numeric threshold is involved?*

## 2026-10-08 — Four precision bugs found and fixed during Stage 4 full-corpus validation, before any coverage figure was reported

- **Context:** after building the real C1–C6 lexicons on principle (previous entry), I ran
  `extract_all()` against the full 17,880-row corpus and manually inspected a sample of each
  rule's actual contradiction cases against the real posting text before trusting any
  number — the same discipline already used for the C2/C4 fixes documented inline in
  `extract_features.py` from first authoring. Four more precision bugs turned up this way,
  each caught by reading real matched text, not by checking against Stage 2 labels:
  (1) C1's "work from home" matched flexible-working *perks* as often as genuine
  remote-position claims (197/223 first-pass contradictions); (2) C1 ignored negation
  ("this is **not** a remote position" still matched "remote position"); (3) C6 never
  resolved "k" (thousands) shorthand, and a salary-context proximity gate
  (`_SALARY_WORD_RE`) was written but never actually wired into the matching logic, so
  unrelated dollar figures (travel reimbursement, ad-copy product costs) were compared
  against `salary_range`; (4) C3's bare "short-term"/"fixed-term" fired on unrelated text —
  95/252 "Temporary" contradictions traced to "short-term disability," a standard US
  benefits-plan phrase with nothing to do with employment type.
- **Decision:** fix all four before reporting any Stage 4 coverage figure, documenting each
  fix inline in the module (with the before/after counts) and in `methodology.md`, rather
  than reporting the first-pass numbers with a caveat. A reported figure that is known to be
  wrong is worse than a delay to fix it.
- **What I gave up:** nothing scientifically — these are corrections, not trade-offs. The
  cost was time (four debugging cycles instead of one pass), which was worth it because the
  pre-fix C1 contradiction count (223) would have been cited in the dissertation as if it
  were a real finding about telecommuting-field inconsistency, when 88% of it was actually
  about flexible-working perks.
- **Self-check:** *For each of the four bugs, what specific real posting text exposed it,
  and why did the fix not require looking at the Stage 2 audit sample to design?*

## 2026-10-08 — Decision 0.3 reconciliation: C6's numeric-escalation path uses a fixed loose margin, not a training-fold-derived threshold

- **Context:** Decision 0.3 (2026-10-06, itself flagged as reconstructed, not recovered
  original reasoning) says C6 should be a presence/structure check wherever possible, and
  that *if* a numeric-deviation comparison turns out to be needed, its threshold should come
  from non-label-conditioned training-fold statistics, not be picked by eye. Building the
  real C6 lexicon, I kept the presence/structure check (`C6_text_salary_field_absent`,
  satisfying Decision 0.3's core concern directly) but also kept a numeric-escalation path
  for when `salary_range` **is** present and a $ figure in the text falls far outside it —
  because dropping that path entirely would have meant C6's existing, already-published O1
  coverage figure (26.5% on the Stage 2 sample, cited in `methodology.md`'s "Taxonomy
  validation" table) silently stopped meaning what it says it means.
- **Decision:** the numeric-escalation margin (a figure counts as contradicting the field
  only if it falls below 0.5× the low bound or above 3× the high bound) is a fixed,
  deliberately generous constant, not a statistic computed from the training fold. This is a
  narrower implementation than Decision 0.3's literal "training-fold statistics" language,
  made because: (a) a fold-dependent threshold would make C6's definition change depending
  on which fold a posting happens to land in, which is a worse property for a rule whose
  whole point is a stable, explainable check; (b) the margin is wide enough (3–6× the
  field's own width, roughly) to function as a sanity check for "wildly different figure,"
  not a precision discriminator — which is exactly the role a label-free default should
  play; (c) it was set once, by inspecting the shape of plausible salary figures, before
  running on the full corpus or seeing any contradiction counts, not adjusted afterward.
- **Additional empirical support found for Decision 0.3's underlying concern (not part of
  the decision itself):** 10.3% of postings with a parseable `salary_range` have a low bound
  under 1,000 — almost certainly a mix of literal dollar figures, unmarked "thousands"
  shorthand, and hourly rates, with no unit indicator in the field to tell them apart. This
  is a real data-quality limitation of `salary_range` itself (logged in `methodology.md`,
  not "fixed" by guessing units), and it independently supports why Decision 0.3 preferred
  minimizing reliance on numeric comparison in the first place.
- **What I gave up:** a C6 implementation that follows Decision 0.3's threshold-sourcing
  instruction to the letter. What's gained is a simpler, label-free, fold-independent rule
  that still satisfies the decision's actual concern (no label-conditioned statistics
  anywhere in C6).
- **Self-check:** *Why does a fixed, generous, non-label-conditioned margin satisfy Decision
  0.3's real concern even though it isn't literally "training-fold statistics," and what
  would make this reconciliation wrong?*

---

## 2026-10-08 — Second incident: the field-presence fix reverted between two git commits; worksheet re-corrected, root cause of the reversion still unconfirmed

- **What happened:** after all 200 postings were coded (commit `57da423`) and I sat down to
  compute the O1 observability/agreement rates for the methodology write-up, `C3`, `C4` and
  `C5` field coverage came back at (or near) 100% again — the exact symptom of the bug
  already found and fixed on 2026-10-07. This was surprising, because `grep` confirmed the
  fix (the `_field_str` helper in `sample_for_manual_audit.py`) was still correctly on disk.
  The bug wasn't back in the code; something had changed the **data**.
- **Investigation:** `git show`/`git diff` across the worksheet's commit history
  (`498200d` → `2ec4e00` → `bd19a7d` → `57da423`) isolated it precisely. `2ec4e00` ("Fix
  Stage 2 field-presence bug; add manual coding tool") has the correct, fixed values — the
  2026-10-07 fix genuinely worked. `bd19a7d` ("Add Stage 2 reading copies (postings +
  question explanations)") was supposed to only add two new `.txt` reading-aid files, but
  `git show --stat` shows it also touched `reports/stage2_manual_audit_worksheet.csv`
  (+101/−101 lines) — and the diff shows `field_present` for C3 (41 rows), C4 (86 rows) and
  C5 (92 rows) reverting back to the pre-fix buggy values, and S001's
  `C3/C4/C5_manual_contradiction_MANUAL` reverting from `NA,NA,NA` back to the original
  `Y,Y,Y`. The commit that was meant to add two unrelated files silently carried the
  worksheet back to an earlier, already-fixed-and-superseded state.
- **Root cause of the reversion itself: not confirmed.** My working hypothesis is a sync
  conflict — the repo sits under `Documents`, a path commonly synced by OneDrive on
  Windows, and if a cached/conflicted copy of the worksheet was restored around the time of
  that commit, it would produce exactly this effect. This is a hypothesis, not a finding: I
  have not verified whether OneDrive sync was active, whether the worksheet was open in
  Excel or another program at the time, or any other explanation. **Open question for the
  student to help resolve** — if it happens a third time without being caught, it would
  silently corrupt real judgement data, which is a materially worse outcome than this time.
- **Quantifying real impact before fixing anything:** rather than assume the worst, I first
  checked how many of the 200 real manual answers were actually affected by the reverted
  `field_present` columns (as opposed to how many rows were merely re-exposed to the
  question). Result: of the 41/86/92 structurally-reverted rows for C3/C4/C5, only **10
  postings' answers were actually wrong** — S001 (C3, C4, C5, all three), S028 (C3), S045
  (C3), S126 (C3), S134 (C3), S140 (C3), S166 (C3), S176 (C4). Every other reverted row
  already had `NA` as its manual answer, meaning **the student's own careful reading had
  already caught the tool asking an impossible question and answered `NA` anyway**,
  independently of whether the underlying `field_present` flag was correct. This is good
  evidence that the 200-row audit was conducted carefully rather than by trusting the
  tool's prompts at face value.
- **Fix:** identical non-destructive method to the first incident — recomputed
  `field_present` for C2–C6 directly from the raw CSV using the already-fixed `_field_str`
  logic; where it flipped Y→N, reset the matching `_manual_contradiction_MANUAL` cell to
  `NA` **only if** it held a real, previously-given Y/N answer (the 10 postings above);
  every other cell (all E1–E4 answers, all other C-rule answers, every `notes_MANUAL`
  entry) was left completely untouched. Saved atomically (write to `.tmp`, then
  `os.replace`).
- **Verified:** re-ran the full 200-row cross-check afterward — 0/200 mismatches remain for
  C3, C4, C5 (and C2/C6, unaffected both times, confirmed still correct). Separately
  verified completeness: 200/200 postings, every required E1–E4 and C1–C6 cell holds a
  valid value, zero blanks.
- **Why this belongs in the dissertation, same reasoning as the first incident:**
  `STAGE2_CODING_INSTRUCTIONS.md` asks the O1 write-up to name at least one thing the audit
  made me revise or drop. The field-presence bug being caught a *second* time, this time as
  a file-level reversion rather than a code-level bug, strengthens that point rather than
  repeating it: the human-in-the-loop step and the surrounding verification discipline
  caught two different failure modes of the same underlying defect, at two different
  stages of the process.
- **What I gave up:** nothing recoverable — as with the first incident, no genuine
  judgement was lost; the 10 affected cells held answers to a question that should never
  have been asked, not valid judgements being overwritten.
- **Still open:** confirm with the student whether the `credibility-scoring-framework`
  folder is OneDrive-synced, and whether the worksheet was open in Excel or VS Code around
  the time of commit `bd19a7d`. Until the actual cause is confirmed, treat any future
  session that touches `reports/stage2_manual_audit_worksheet.csv` as needing a fresh
  cross-check against the raw CSV before trusting its `field_present` columns.
- **Self-check:** *why did only 10 of the ~219 structurally-reverted rows actually have a
  wrong manual answer, and what does that gap tell you about how dependent your own
  judgement was on the tool's prompts being correct versus your own reading of each
  posting?* *Separately: why does "the worksheet file reverted between two commits" need a
  different kind of fix — a file-integrity investigation and an open root-cause question —
  rather than just reapplying the same code fix and moving on?*

---

## 2026-10-07, 23:55 — Bug found and fixed: Stage 2 worksheet pre-fill wrongly marked blank employment_type/required_experience/required_education as "present" for 41/86/92 of 200 postings

- **What happened:** while coding S001 (the first posting), I noticed the coding tool's
  `--full-text` printout showed `employment_type=(blank)`, `required_experience=(blank)`,
  `required_education=(blank)` for that posting, yet the worksheet had still asked me to
  judge C3/C4/C5 contradictions on it — which should be impossible if those fields are
  genuinely blank (per `STAGE2_CODING_INSTRUCTIONS.md`, a contradiction judgement is only
  asked when `{rule}_field_present == 'Y'`). I asked whether my answers were wrong; checking
  this directly was more useful than guessing, so the underlying pre-fill script was read
  and the raw CSV cross-checked row by row.
- **Root cause:** `src/taxonomy_audit/sample_for_manual_audit.py`'s field-presence checks for
  C3, C4 and C5 used the pattern `str(r.get("field", "") or "").strip()`. `df` is loaded with
  `dtype=str, keep_default_na=False, na_values=[""]`, which still converts a blank cell to a
  float `NaN` (the column exists, so `.get()` returns that `NaN` itself, not the `""`
  default). `NaN or ""` evaluates to `NaN` because `bool(float('nan'))` is `True` in Python,
  and `str(NaN)` is the non-empty string `"nan"` — which passes a `!= ""` presence check.
  Net effect: any row where `employment_type`, `required_experience` or `required_education`
  is genuinely blank was pre-filled as `field_present = "Y"`, wrongly soliciting a manual
  contradiction judgement on a field that doesn't exist.
- **How widespread:** cross-checked all 200 rows of `reports/stage2_manual_audit_worksheet.csv`
  against `data/raw/DataSet.csv` directly (comparing `field_present` to whether the raw field
  is actually `NaN`/blank at that row's `original_csv_index`). **C3 (employment_type) wrong
  on 41/200 rows; C4 (required_experience) wrong on 86/200; C5 (required_education) wrong on
  92/200.** C2 (location) and C6 (salary_range) use the same buggy access pattern but turned
  out unaffected in practice — C2's `has_city` check requires splitting on commas into ≥3
  parts, and C6's regex requires a `\d+-\d+` shape, so the literal string `"nan"` fails both
  checks anyway and happens to land on the correct `"N"` by coincidence, not by correct
  handling. Confirmed this with the same full-dataset cross-check: 0/200 mismatches for both.
- **Fix:** added a `_field_str(row, key)` helper to `sample_for_manual_audit.py` that checks
  `pd.isna(v)` before falling back to `""`, and routed every field-presence check (C2, C3,
  C4, C5, C6) through it instead of the `or ""` pattern — including C2 and C6, which weren't
  actually wrong, so the same latent bug can't resurface there later by accident.
- **How the live worksheet was corrected (not regenerated from scratch):** re-sampling from
  scratch was rejected — it would reshuffle which 200 postings are even in the sample (the
  `RANDOM_SEED = 42` sampling is deterministic given the same input, but rebuilding the whole
  worksheet risked clobbering every `_MANUAL` answer already entered, for the sake of fixing
  three columns). Instead, a one-off correction script recomputed only the five
  `{rule}_field_present` columns against the raw CSV using the fixed logic, row by row, in
  place. Where a `field_present` flag flipped from the old (wrong) `"Y"` to the corrected
  `"N"`, the matching `{rule}_manual_contradiction_MANUAL` cell was reset to `"NA"` (the only
  valid value once the field doesn't exist) — but only if it had actually been answered;
  rows not yet reached were left untouched. Every `E1-E4_observable_MANUAL`,
  `C1_manual_contradiction_MANUAL`, and `notes_MANUAL` entry already filled in was verified
  byte-for-byte unchanged afterward.
- **Concrete effect on real data:** only S001 had been coded at the time this was found. Its
  `C3/C4/C5_field_present` flipped `Y → N` and its `C3/C4/C5_manual_contradiction_MANUAL`
  (which I had answered `Y/Y/Y`, because the tool asked) were reset to `NA`. This is a
  mechanical correction, not a re-judgement of my answer — those three fields genuinely do
  not exist on that posting, so `NA` is the only correct value, and I was never actually
  capable of answering that question correctly as it was originally asked. My E1-E4 and C1
  answers for S001 stand exactly as I gave them.
- **Verified:** re-ran the full 200-row cross-check after the fix; 0/200 mismatches remain
  for all five rules (C2, C3, C4, C5, C6).
- **Why this belongs in the dissertation, not just this file:** `STAGE2_CODING_INSTRUCTIONS.md`
  already asks the audit write-up to name at least one thing the audit itself made me revise
  or drop — this is that thing, and it's a stronger one than a borderline judgement call: the
  manual audit caught a real, previously undetected defect in the project's own tooling,
  on the very first posting coded. That's worth stating plainly in the O1 write-up in
  `methodology.md` once the full 200 rows are done, as evidence the human-in-the-loop step is
  doing real work, not rubber-stamping.
- **What I gave up:** nothing recoverable — no manual judgement was thrown away that was ever
  valid. The only cost was the few minutes spent answering three questions that should never
  have been asked.
- **Self-check:** *why does the exact same buggy access pattern produce a wrong answer for
  C3/C4/C5 but, by coincidence, a right one for C2/C6 — and why was "fix all five anyway"
  the correct response rather than "only fix the three that were actually wrong"?*

---

## 2026-10-07, 18:10 — Git commit-attribution fix: history rewritten locally via cherry-pick, not interactive rebase; push deferred to the student

- **What decided:** three commits (`b5a45aa`, `5545d37`, `6e391b4` — Stage 3, Tier 2
  legit-side sourcing, and the overnight close-out note) carried an unwanted
  `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>` + `Claude-Session:` trailer. I
  do not want Claude attributed as a co-author in GitHub's contributor graph — my explicit
  instruction from last night. Fixed by rewriting those three commits.
- **Options considered:**
  1. **Interactive rebase (`git rebase -i`, mark as `reword`)** — the standard tool for this,
     but it opens an interactive editor per commit, which a non-interactive shell (this
     session's `device_bash`) cannot drive without extra scripting (`GIT_SEQUENCE_EDITOR` /
     `GIT_EDITOR` tricks).
  2. **`git filter-branch` / `git filter-repo`** — more powerful than needed for exactly
     three known, contiguous, top-of-branch commits; `filter-repo` wasn't confirmed
     installed, and `filter-branch` is explicitly discouraged by git itself for anything
     this small.
  3. **Branch from the shared parent + cherry-pick each commit, amending the message each
     time (`git commit -F <cleaned-message-file>`)** — chosen. Since all three commits were
     already the three most recent on `main` (no commits after them), this is equivalent to
     a reword-only rebase but fully scriptable without an interactive editor, and lets me
     verify each result before moving to the next.
- **Why this one:** option 3 does exactly what's needed with no editor dependency, and its
  intermediate state is easy to verify at each step — after each cherry-pick I diffed the
  new commit's tree against the old commit's tree (`git diff <old> <new>`) and required it
  to be empty before amending the message, so content could not silently drift. Author name,
  author email, and both author and committer dates were explicitly carried over
  (`GIT_AUTHOR_*` / `GIT_COMMITTER_*` env vars set from the original commit's own metadata)
  so the rewritten commits look, date-wise, exactly like the originals — only the message
  changed.
- **Safety steps taken before rewriting:** created `backup-pre-attribution-fix`, a branch
  pointing at the old history (tip `6e391b4`), before touching anything, so the original
  commits remain reachable and recoverable if anything goes wrong. After rewriting, scanned
  the full rewritten range (`af25cb5..a39f441`) for the strings `Co-Authored-By` and
  `Claude-Session` — zero matches.
- **What I gave up:** nothing load-bearing. The rewritten commits have different hashes from
  the ones currently on `origin/main`, which is unavoidable for any history rewrite — this
  is why the next step is a `--force-with-lease` push, not a plain push.
- **Why the push itself was not done from this session:** the task's linked development
  machine exposes a sandboxed, isolated Linux shell (`device_bash`) that is a separate VM
  from the actual Windows machine — it mounts only the connected repo folder, not the
  Windows credential manager / Git Credential Manager that normally supplies GitHub
  authentication. `git push` from that shell failed immediately with
  `fatal: could not read Username for 'https://github.com'` — there is no token or stored
  credential available to it, and entering one on its behalf isn't something I generate or
  substitute for the student. The fix must be completed by running
  `git push --force-with-lease origin main` from the student's own terminal, where GitHub
  auth already works.
- **Side-finding, logged not fixed-around:** the first `git stash` attempt during this
  work left a stray `.git/index.lock` and some `tmp_obj_*` files that blocked further git
  commands (`device_bash`'s connected folder has delete disabled by default). After delete
  permission was granted for this one folder, clearing the stale lock triggered a full
  working-tree line-ending (CRLF-vs-LF) rewrite of 9 unrelated already-committed files
  (`.gitignore`, `README.md`, two audit-history files, `data/README.md`, four `reports/*`
  files) — confirmed via `git diff -w` to be whitespace-only, zero semantic change, and
  discarded with `git checkout --` before proceeding, so none of that noise entered any
  commit.
- **Self-check:** *why is a plain `git push` not enough here, and why `--force-with-lease`
  specifically rather than plain `--force`?* — Because the commit hashes changed (the
  content is identical but the messages differ, so git treats them as different commits),
  a plain push is rejected as a non-fast-forward update; `--force` would push regardless of
  what's currently on the remote, while `--force-with-lease` refuses if someone/something
  else has pushed to `origin/main` since I last fetched it — a guard against silently
  clobbering work I don't know about.

  > ✅ **Resolved, 2026-10-07, 23:31:** pushed `git push --force-with-lease origin main`
  > from my own terminal (VS Code's integrated PowerShell, venv active). GitHub accepted it
  > cleanly: `6e391b4...09bece3 main -> main (forced update)`. `origin/main`'s tip is now
  > the trailer-free history. `backup-pre-attribution-fix` stays as a local-only branch
  > holding the old history, never pushed, costs nothing to keep.

---

## 2026-10-07, 17:30 — Tier 2 fraud-side sourcing resolved: 24 verified postings, BBB Scam Tracker, via Claude in Chrome

- **What happened:** with the development machine linked and the Claude in Chrome
  extension installed (walked through step by step this morning), BBB Scam Tracker's
  "employment" search became reachable — Claude in Chrome, driving my real signed-in
  Chrome, loads the page normally where both the sandboxed browser pane and plain WebFetch
  were stopped by a Cloudflare "Just a moment..." challenge. No bypass technique was used
  anywhere — every block was handled by waiting and retrying, or by paginating once the
  page had already loaded cleanly.
- **What was collected:** read through BBB Scam Tracker's "employment" search results,
  pages 1–8 (`from=0` through `from=70`, ~80 individual reports read in full), and kept
  every report that contains **genuinely reproduced posting-adjacent text** — a quoted
  email, SMS, or chat message from the scammer naming a role, pay rate, duties, or an
  application step — rejecting reports that are narrative-only ("they called and asked if I
  could hear them") or too corrupted to use (one report's message text was obfuscated with
  stray `?` characters past the point of being legible). **24 reports passed this filter**,
  comfortably inside the 20–30 target set in the 2026-09-20 scope-cut decision.
- **Provenance:** each BBB report has its own permanent URL
  (`https://www.bbb.org/scamtracker/lookupscam/<Scam ID>`), confirmed by inspecting the
  page's own DOM (`aria-labelledby="result-<id>-title"` on each result's link) rather than
  guessing — this resolves the provenance question left open overnight. Every one of the 24
  records in `data/raw/tier2/tier2_fraud_raw.jsonl` carries its own unique `source_job_id`
  (the BBB Scam ID) and `source_url` (the permalink), exactly mirroring how
  `tier2_legit_raw.jsonl` carries `source_job_id`/`source_url` for Greenhouse/Lever.
- **Schema decision:** the EMSCAD-shaped structured fields (`title`, `location`,
  `salary_range`, etc.) are left `null` for every fraud-side record, rather than invented
  from the narrative or populated from BBB's "Victim Location" (which is where the *victim*
  lives, not a claimed job location — not the same field semantically, so it does not belong
  in `location`). BBB-specific context (the category tag, the business name the scammer
  used, the date reported, and dollars lost) is kept in separate `bbb_*` fields instead of
  forced into EMSCAD columns. This keeps the E3/E4 asymmetry exactly as already decided and
  disclosed in Decision 0.4 (2026-10-06) — I am not quietly inventing structure on the fraud
  side to make it look more symmetric than it is.
- **Data-quality finding, worth disclosing in Chapter 6:** the same scam narrative (a
  "David Smith" / "Sheriff Gossling" personal-assistant check-fraud report) appears at least
  three times in BBB's own database under three different Scam IDs (442452, 442451, and one
  more seen in an earlier page) — byte-for-byte identical text, different report IDs. This
  report was excluded from the 24 anyway because it has no quoted posting/ad text, but the
  pattern itself matters: BBB Scam Tracker contains genuine near-duplicate injection (the
  same report filed, or re-filed, multiple times), so any later aggregate statistic drawn
  from BBB counts ("X% of scam reports are...") would need deduplication first. Noted here
  rather than silently worked around.
- **What I gave up:** nothing further was attempted after reaching 24 — pagination stopped
  once comfortably past the 20-minimum / 30-target band, rather than continuing to scrape
  every one of BBB's "employment" pages. A larger fraud-side set was available (BBB reports
  10,000+ results for this search) but collecting it all would have cost Day 1 time for a
  number the target band already calls sufficient, and Tier 2 is held-out validation only —
  more volume here doesn't buy anything a training set would need.
- **Self-check:** *Why does "Victim Location" not belong in the same `location` field
  EMSCAD uses, even though both are nominally about where a job is?*

---

## 2026-10-07, 00:40 — Tier 2 fraud-side sourcing: fetchable web tools confirmed a dead end tonight; deferred to daylight with a time-boxed browser-assisted plan

- **What was tried:** three real attempts, not a guess that it wouldn't work. (1) General
  web search for scam job postings with reproducible full text — returned only news
  coverage and BBB aggregate-study articles *describing* scam patterns, never quoting a
  real posting's actual text. (2) Direct fetch of BBB's Scam Tracker — its search is
  JavaScript-driven; a static fetch only sees the empty shell, not individual reports. (3)
  Direct fetch of Reddit r/scams — blocked outright (declined for legal reasons, same as
  any site this tool declines; not worked around with another method). (4) Direct fetch of
  two specific DOJ/FTC documents likely to quote evidence — both describe schemes in their
  own summary language ("promising job seekers... $6,000 in guaranteed monthly profit")
  rather than reproducing the actual posting text verbatim.
- **Why this matters:** unlike the legitimate side (Greenhouse/Lever expose a public,
  structured, machine-readable API because job boards want to be found), scam reporting has
  no equivalent. The primary artefact — the actual posting text — lives inside individual
  human reports (BBB Scam Tracker entries, Reddit threads, screenshots), not in any
  bulk-fetchable or API-exposed form. This is a genuine structural difference between the
  two sourcing problems, not a tooling shortfall on one side.
- **Decision:** do not invoke the pre-planned qualitative-only fallback yet — that is a real
  decision with Chapter 6 limitations consequences and deserves one focused, real attempt
  first, not a call made because fetch-only tools hit a wall at 1am. Instead: defer to
  daylight hours of Day 1, with two concrete options kept open — (a) link the development
  machine to the AI session via the desktop app, giving genuine interactive browser access
  (can search, click, scroll through BBB/Reddit), run for a hard-capped ~90 minutes; or (b)
  manual browsing and curation, done with a fresh, attentive read rather than at 1am. If
  neither reaches ~20 verified fraudulent postings by end of Day 1, the fallback decided
  2026-10-06 triggers exactly as already planned — that outcome was anticipated, not a
  surprise.
- **What I gave up:** a few hours tonight that could have gone toward fraud-side sourcing,
  in exchange for not producing low-quality, badly-documented provenance records from a
  tired, rushed attempt. Given this data becomes part of a held-out validation set whose
  entire value rests on trustworthy labels, a smaller number of carefully-verified postings
  is worth more than a larger number collected carelessly.

  > ✅ **Resolved, 2026-10-07, 17:30:** option (a) worked — see the entry above. 24 verified
  > postings collected, well inside the 20–30 target. Tier 2 fraud-side sourcing is closed.

- **Self-check:** *Why does the legitimate side of Tier 2 have a clean public API while the
  fraud side doesn't — what's structurally different about who wants a scam report to be
  easy to find by machine?*

---

## 2026-10-07, 00:40 — Tier 2 legitimate-side target exceeded (130 vs. 30–50 planned); kept in full

- **What happened:** the Greenhouse/Lever sourcing script (60 candidate company slugs,
  self-validating — tries each, keeps only what responds) returned 130 postings from 26
  real companies (24 Greenhouse, 2 Lever), capped at 5 postings/company for diversity. This
  is well above the 30–50 figure in the sprint plan and in `decisions.md`'s 2026-09-20
  Tier 2 scope-cut entry.
- **Options considered:** (A) subsample down to ~50 to match the original target exactly;
  (B) keep all 130.
- **Why B:** Tier 2 is held-out validation only — never trained on, never used to fit
  anything — so extra legitimate-side volume doesn't risk anything a training set would
  (no risk of the model fitting to Tier 2 noise, no risk to the leakage-controlled
  train/val/test boundary, which is Tier 1 only). More postings only makes the temporal-
  transfer evaluation's legitimate-side estimate more stable, and diversity across 26
  companies (vs. fewer companies at higher volume) better represents real-world variety in
  job-board formatting and writing style. There is no stated reason in any existing decision
  to prefer exactly 30–50 over "however many clean, diverse postings are available" — the
  30–50 figure was a planning estimate for what seemed achievable, not a methodological
  requirement.
- **What I gave up:** nothing substantive. The one thing to watch: this leaves Tier 2
  asymmetric in volume (130 legitimate vs. a fraud-side target of only 20–30, assuming that
  target is even met) — this asymmetry must be reported plainly in `methodology.md`
  alongside the fraud-side numbers once both are known, not presented as if the two sides
  were collected at comparable scale.

  > ✅ **Numbers now final, 2026-10-07:** 130 legitimate vs. 24 fraudulent. The asymmetry is
  > real (5.4:1) and must be stated plainly wherever Tier 2 composition is reported.

- **Self-check:** *Why is extra Tier 2 legitimate-side volume safe to keep, when extra
  Tier 1 training data in the wrong place would not be?*

---

## 2026-10-06, 23:59 — Correction: Decision 0.2's title-hash grouping over-merges; reverted to description-hash only

- **What happened:** Stage 3's partitioning code was built tonight implementing Decision
  0.2 exactly as logged — MD5-on-normalised-description UNION MD5-on-normalised-title. It
  ran, passed all 9 tests, and produced a plausible-looking top-line number (56.68% of the
  corpus in a duplicate group). Before committing, a diagnostic was run on the 15 largest
  groups rather than trusting that number — this is exactly the kind of check the project's
  own continuity protocol calls for, and it caught a real bug.
- **What the diagnostic showed:** only the known "English Teacher Abroad" group (714
  records, 7 titles, 28 descriptions) looks like a genuine repost campaign. Every other
  large group is a false merge — e.g. "Software Engineer" (572 records, **118 distinct
  titles, 501 distinct descriptions**), "Customer Service Associate" (396 records, 48
  titles, 304 descriptions). These are hundreds of genuinely unrelated postings from
  different companies, chained together because they happen to share a common, generic job
  title. Because grouping is transitive, one coincidental title or description match can
  snowball into merging hundreds of otherwise-unrelated records.
- **Why this matters:** this is a worse version of the exact failure mode Decision 0.2
  already rejected a cheaper method for in September (the 12-token-prefix proxy, rejected
  for merging 48.9% of the corpus). Tonight's title-hash union merged 56.68% — higher than
  the method already rejected for over-merging. Shipping this would have corrupted the
  train/validation/test split (forcing genuinely distinct postings into the same partition
  for no real reason) and reported a false "duplication rate" in the methodology chapter.
- **Decision:** revert to description-hash-only grouping (Decision 0.2's Option A, already
  considered and logged in September). This reproduces the already-measured, already-
  verified figures from the original August audit (4,762 records / 26.6%, largest group
  417) rather than a new, broken number. The known cost — the "English Teacher Abroad"
  campaign fragmenting across several groups under description-only hashing — is accepted
  as a disclosed limitation, exactly as Option A always represented it in the original
  Decision 0.2 analysis.
- **What I gave up:** the specific benefit Decision 0.2 was designed to provide (catching a
  campaign's stragglers that vary body text but reuse a title). Tested in practice, it
  doesn't work at corpus scale — generic titles are far more common than distinctive ones,
  and there's no cheap way tonight to tell them apart. A real fix (e.g. requiring title
  match AND some minimum description similarity, or proper near-duplicate clustering) is
  future work, same as Decision 0.2 already said about MinHash/shingling.
- **Self-check:** *Why did a method designed around one specific, validated example
  (English Teacher Abroad) fail so badly elsewhere, and what would have happened if the
  15-largest-group diagnostic hadn't been run before committing?*

---

## 2026-10-06, 23:50 — Decisions 0.3 and 0.4 resolved (delegated authority)

- **Context:** both decisions were scheduled for Day 1 morning, but Decision 0.3's original
  framing could not be recovered from the project files — only a one-line pointer existed.
  The student explicitly delegated authority to resolve both now rather than lose Day 1
  morning time rediscovering lost context. Logged honestly: 0.3 below is a reconstruction,
  not recovered original reasoning, and is flagged as such.

### Decision 0.3 — label-conditional statistics in design (C6 viability)

- **Reconstructed problem statement (not recovered from the original record):** C6 compares
  a salary figure mentioned in posting text against the structured `salary_range` field.
  Unlike C1 (a clean binary contradiction — remote vs on-site language), "mismatch" for a
  salary comparison could require a numeric deviation threshold, and setting that threshold
  by checking which deviations correlate with the fraud label would be a quiet form of
  leakage into rule *design* — not test-set leakage in the usual sense, but the same
  underlying problem as the existing guardrail "a threshold set after seeing results is not
  a threshold."
- **Decision:** C6 is defined as a presence/structure check wherever possible — e.g. "the
  text names a specific dollar figure while `salary_range` is absent entirely" — which needs
  no numeric threshold and therefore no label-conditioned statistics at all. Only if Stage 4
  finds this insufficient to produce a usable signal does a numeric-deviation version get
  considered, and if so its threshold must be set from training-fold descriptive statistics
  that do not condition on the label.
- **What I gave up:** a richer C6 that captures "salary number present but implausibly high
  or low," not just "salary number present but field missing." Given C6 already has the
  lowest evaluable coverage of all six rules (7.6% provisional), this is a small loss.
- **Self-check:** *Why would setting a numeric mismatch threshold by looking at which
  deviations correlate with the fraud label count as leakage, even though it never touches
  the test set?*

### Decision 0.4 — Tier 2 field symmetry (can E4 fire on the fraud side?)

- **Decision:** (1) during Day 1 sourcing, prefer fraud sources that document some
  structured fields over pure text dumps, reducing the asymmetry at the source rather than
  only measuring it afterward; (2) E1/E2 remain Tier 2's primary evidence, since both depend
  on posting text rather than how much structured metadata a given source happened to
  capture; (3) Tier 2's E3/E4 ablation results are reported with the asymmetry disclosed as
  a named limitation, not dropped from the experiment — E4 is the project's actual
  contribution, and discarding it from Tier 2 to dodge the confound would be a worse choice
  than measuring and disclosing it; (4) the source-probe leakage test already decided
  2026-08-07 is run specifically flagging E3/E4 feature importance, so the size of the
  confound is measured, not guessed.

  > ✅ **Outcome, 2026-10-07:** BBB Scam Tracker reports document almost no structured
  > fields (no salary_range, no employment_type, etc. — only a free-text narrative plus a
  > handful of BBB-specific metadata that isn't EMSCAD-shaped). Clause (1) above could not
  > be satisfied in practice — BBB simply doesn't offer a more structured alternative for
  > fraud reports the way Greenhouse/Lever do for legitimate postings. Clauses (2)–(4) stand
  > as planned: Tier 2's fraud side is text-heavy, EMSCAD-shaped fields are null, and this is
  > reported as a disclosed asymmetry, not hidden.

- **What I gave up:** a clean, confound-free Tier 2 E4 result. What's gained instead is an
  honest, measured one.
- **Self-check:** *Why is dropping E3/E4 from Tier 2 entirely a worse choice than measuring
  and disclosing the asymmetry, given E4 is the project's actual contribution?*

---

## 2026-10-06 — Five-day sprint compression: deadline, Tier 2 time-boxing, ablation contingency, triage order

- **Context:** the actual deadline is 5 days from today (2026-10-06), not "~1 month from
  2026-08-27" as every project file has stated — that earlier date has already passed. This
  entry supersedes the old deadline wherever it appears, until the exact programme-office
  date is confirmed and logged in its place.

### 1. Tier 2 collection is time-boxed to Day 1 only

- **Options considered:** (A) keep the 1-week checkpoint decided 2026-09-20; (B) compress
  the checkpoint to a single day with the same fallback rule; (C) drop quantitative Tier 2
  entirely, right now, with no attempt.
- **Why B:** with 5 days total and Stages 3–9 plus three dissertation chapters, a paper, and
  a declaration still ahead, a week-long checkpoint no longer exists — the whole sprint is a
  week. Option C gives up the one finding no reviewed EMSCAD paper has produced (does a model
  survive contact with contemporary fraud) before even trying. Option B keeps that chance
  alive for exactly one day and refuses to let it spend a second one if it fails.
- **Explicitly accepted risk, stated directly by me:** I am not chasing down formal
  institutional ethics sign-off for Tier 2 primary data collection before collection starts
  this week, given the timeline. This stays logged as an open item (see `project.md`) and
  must appear as a stated limitation in Chapter 6 — not something I quietly skip and never
  mention.
- **What I gave up:** the chance that fraud-side sourcing just needed 2–3 days, not 1.
- **Self-check:** *Why does compressing the checkpoint from a week to a day not change the
  fallback rule itself, only when it fires?*

### 2. Ablation seed count is conditional, decided on Day 3 from a real timing, not guessed now

- **Decision:** the main baseline-vs-improved comparison keeps 3 seeds (closed 2026-09-20,
  unchanged). The leave-one-category-out ablation arms (E1, E2, E3, E4, `has_company_logo` —
  5 arms) may drop to 1 seed each if 3×5 does not fit the compute budget measured by timing
  one real DistilBERT fine-tuning run on Day 3.
- **Why conditional rather than decided now:** I don't yet have a real per-run time to reason
  from — guessing now risks either wasting Day 3 on an avoidable cut or discovering too late
  that it was necessary. One timed run on Day 3 settles it with evidence instead of a guess.
- **What I gave up:** certainty about the shape of Day 3's schedule, in exchange for not
  pre-committing to a cut I might not need.
- **Self-check:** *Why is it defensible for the main comparison and the ablation arms to end
  up using a different seed count, when both measure performance?*

### 3. Triage order, fixed in advance

- **Decision, in order:** (1) the research paper is cut first — it may finish after the
  5-day window if there's slack, named now as the most likely casualty, not discovered on
  the last day; (2) ablation seed count reduces per Decision 2 above; (3) Tier 2 depth
  reduces further or falls back to qualitative-only (already time-boxed per Decision 1);
  (4) never cut: leakage-controlled partitioning, calibration, the test-set-used-once rule,
  the 200-posting manual audit, and the honest stub-vs-real distinction in the API.
- **Why fix this now:** deciding what to cut while exhausted on Day 4 night produces worse
  decisions than deciding it now, calmly, with the whole week still ahead. I was explicit
  that I do not want the manual audit or the core pipeline's correctness touched for any
  reason — this order protects exactly that.
- **What I gave up:** flexibility to reorder this under pressure. That's deliberate.
- **Self-check:** *Why is the manual audit protected ahead of the research paper, when the
  paper is also a formal deliverable?*

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

  > ✅ **Resolved, 2026-10-06, 22:56:** the CPU-only `torch` build was replaced with the
  > CUDA 12.4 build (`torch==2.6.0+cu124`) on the first try — a matching wheel existed for
  > Python 3.13 on Windows, so the Python-3.13-wheel-lag risk flagged earlier did not
  > materialise. `torch.cuda.is_available()` confirmed `True` against the RTX 3050. No
  > fallback (separate venv, frozen embeddings) was needed. `requirements.txt` needs
  > regenerating to reflect this.

- **Self-check:** *Why was "no GPU" assumed for months without being checked, and what
  single fact changed once it was?*

---

## 2026-09-20 — Scope-cut decisions given the confirmed ~1 month deadline

- **Context:** the actual submission deadline was confirmed for the first time on
  2026-08-27 as approximately one month away. Full rigor on all nine stages as originally
  scoped does not fit that timeline for a single developer. Five related decisions were
  made together, deliberately, in one CONVERGENT session, rather than left to erode
  piecemeal under time pressure later.

  > ⚠️ **Superseded, 2026-10-06:** the "~1 month" deadline this section refers to has
  > elapsed. The decisions below (rules-only cut, fine-tuned DistilBERT, reduced Tier 2,
  > 3 seeds, SHAP-only, architecture review skipped) all still stand — they were not
  > reopened — but the deadline context is the 5-day sprint recorded above, not this entry.

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
- **What I gave up:** statistical power. A 50–100 posting Tier 2 will have wide confidence
  intervals; this must be stated plainly, not minimised.

  > ⚠️ **Update, 2026-10-06:** the 1-week checkpoint below is now a 1-day checkpoint — see
  > the 2026-10-06 entry above. The reduced target (20–30 fraud / 30–50 legit) is unchanged.

  > ✅ **Final numbers, 2026-10-07:** 130 legitimate (kept in full, see entry above) / 24
  > fraudulent (see entry above). Both targets met or exceeded within the Day 1 time-box.

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

  > ⚠️ **Update, 2026-10-06:** whether the ablation arms specifically keep 3 seeds or drop
  > to 1 is now conditional on a Day 3 timing measurement — see the 2026-10-06 entry above.
  > The main comparison's 3 seeds are unaffected.

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
  > decision — see Decision 0.2, resolved 2026-09-20.

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
  estimates even across three seeds.

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

  > ⚠️ **Status, 2026-10-06:** the fallback clause is now time-boxed to a single day — see
  > the 2026-10-06 entry at the top of this file.

  > ✅ **Status, 2026-10-07:** fallback not needed — both tiers of Tier 2 met their targets
  > within Day 1. See the 2026-10-07 entries above.

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

  > ✅ **Applied, 2026-10-07:** the fraud-side BBB-sourced records are labelled
  > "fraudulent by report," not independently fact-checked for whether the underlying
  > narrative is literally true — consistent with this decision. The quoted scammer
  > message/email itself is what I train/evaluate on, not the surrounding narrative, which
  > keeps the labelling principle intact (the text is reproduced, not paraphrased by the
  > reporter or by me).

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

> ✅ **Resolved:** the 2026-09-20 scope-cut round, Decision 0.2, the 2026-10-06 sprint
> compression (deadline, Tier 2 time-boxing, ablation contingency, triage order), Decisions
> 0.3 and 0.4 (resolved 2026-10-06, 23:50), and Tier 2 fraud-side sourcing (resolved
> 2026-10-07, 17:30) are all closed. Two items remain genuinely open:

## Success thresholds for each objective

- **The question:** What actually counts as success for each objective? Still unset in
  `methodology.md`.
- **Constraint:** Agree with supervisor before results are seen, if any contact window
  exists this week. If not, state in Chapter 5 that thresholds were self-set under time
  pressure.

## Tier 2 ethics approval status

- **The question:** Has the institutional ethics application for Tier 2 primary data
  collection actually been submitted?
- **Status, 2026-10-06:** explicitly not gating collection this week (see the 2026-10-06
  entry above). This remains open and must be named as a limitation in Chapter 6.
