import re
path = "docs/decisions.md"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()
orig = text

anchor = "## 2026-10-08 — Second incident: the field-presence fix reverted between two git commits; worksheet re-corrected, root cause of the reversion still unconfirmed"
assert text.count(anchor) == 1, "anchor not found or not unique"

new_entries = '''## 2026-10-08 — Stage 4 lexicon design: delegated decision on tuning-contamination risk and two out-of-scope patterns

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
- **What I gave up:** aC6 implementation that follows Decision 0.3's threshold-sourcing
  instruction to the letter. What's gained is a simpler, label-free, fold-independent rule
  that still satisfies the decision's actual concern (no label-conditioned statistics
  anywhere in C6).
- **Self-check:** *Why does a fixed, generous, non-label-conditioned margin satisfy Decision
  0.3's real concern even though it isn't literally "training-fold statistics," and what
  would make this reconciliation wrong?*

---

'''

text = text.replace(anchor, new_entries + anchor)
assert text != orig
with open(path, "w", encoding="utf-8") as f:
    f.write(text)
print("decisions.md edit OK, net change:", len(text) - len(orig))
