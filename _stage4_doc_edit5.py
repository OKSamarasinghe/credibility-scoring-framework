path = "docs/methodology.md"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()
orig = text

anchor = "### Baseline results (O2) — [DATE]"
assert text.count(anchor) == 1
insert = '''### Stage 4 multi-signal evidence extraction (O1, O3) — 2026-10-08

_Measured by running `src.features.extract_features.extract_all()` against the full
EMSCAD corpus (`data/raw/DataSet.csv`, n=17,880) via its own `__main__` driver, which
writes `reports/stage4_coverage_report.json` (committed alongside the module and tests —
pending the student's commit). 33/33 new tests in `tests/test_extract_features.py`
passing; 51/51 across the whole suite (no regression in Stages 1 or 3)._

**What was built:** E1 (a 6-group suspicious-phrase lexicon: advance-fee, unrealistic
earnings, off-platform contact, urgency/pressure, personal-info requests, vague
employer), E2 (company_profile presence/length, location specificity, the Stage 1
contact-token counts carried through, tagged E2_), E3 (9-field presence + equal-weighted
completeness score), and E4 — real C1–C6 lexicons replacing every provisional pattern
from the August audit, including the first real C2 location matcher.

**Methodological safeguard taken (delegated decision, student's instruction "do the best
and most suitable way... take the best decision carefully"):** the 200-posting Stage 2
disagreement notes (`reports/stage2_disagreements_for_review.txt`) are the only
human-labelled signal this project has about these rules. Tuning the new lexicons
row-by-row against that sample until they agreed with it would have been circular — the
same failure mode the project's own guardrail names directly ("a threshold set after
seeing results is not a threshold"). Each rule was instead designed on general linguistic
principle, using the disagreement notes only as qualitative inspiration for *categories*
of failure (e.g. "topic mention vs. genuine claim"), never as a row-by-row tuning target.
No lexicon decision in this module was made by checking its effect on the 200-posting
sample.

**Four precision bugs found and fixed during full-corpus validation, before any figure
above was reported** (same discipline as the C2/C4 fixes already in the module's inline
notes from first authoring) — in each case the fix is a general linguistic distinction
checked against the actual matched text, not a fit to the Stage 2 audit sample:

1. **C1 — "work from home" perk vs. position claim.** The bare phrase fired on
   flexible-working *perks* ("ability to occasionally work from home", "work from home
   Wednesdays") as often as on genuine remote-position claims. 197 of 223 first-pass C1
   "contradictions" (88%) traced to this one phrase. Fixed by requiring a position-
   asserting cue near the phrase and excluding a nearby perk/conditional cue.
2. **C1 — negation ignored.** "This is **not** a remote position" still matched the
   literal phrase "remote position" and was flagged as contradicting the field even
   though the text and field actually agreed. Fixed with a general negation check applied
   to every C1 phrase match, not patched per-phrase.
3. **C6 — "k" (thousands) unresolved, and a dead salary-context gate.** "$95k – $105k"
   parsed as the literal numbers 95 and 105, so a figure that exactly matched the field
   range was reported as "far outside" it. Separately, `_SALARY_WORD_RE` (meant to
   require a $ figure to sit near explicit salary/pay language) was defined but never
   actually wired into the matching logic, so unrelated dollar figures in the same
   posting (a travel/interview reimbursement, a product cost mentioned in ad copy) were
   compared against `salary_range` and flagged as contradictions. Both fixed; the
   context gate is now load-bearing rather than dead code.
4. **C3 — "short-term"/"fixed-term" too polysemous.** 95 of 252 "Temporary"-signal
   contradictions traced to "short-term disability" / "long-term disability" — standard
   US benefits-plan boilerplate with nothing to do with the advertised role's employment
   type. A related shape: bare "seasonal" matched even when describing *other* staff
   mentioned in the posting ("...80 full-time staff and 200 seasonal workers...") rather
   than the advertised role. Fixed by dropping the polysemous bare phrases and requiring
   "seasonal" to be followed by a role-noun.

C1's evaluable/contradiction counts fell from 362/223 (pre-fix) to 90/45 (final) as a
direct result of fix 1–2; C6 from 242/142 to 219/52 as a result of fix 3; C3 from
17.49%-of-evaluable contradictions to 10.84% as a result of fix 4. The final figures in
the Consistency rule set table above are post-fix.

**Data-quality finding, not a code bug — `salary_range` unit ambiguity.** Of 2,725
postings with a parseable `salary_range`, 280 (10.3%) have a low bound under 1,000 (174
under 50) — almost certainly a mix of literal annual-dollar figures, unmarked
"thousands"-shorthand (a field literally reading "135-165" meaning $135k–$165k), and
genuine hourly rates, with no unit indicator in the field itself to tell them apart.
Guessing the unit would itself be an invented assumption, so this was left undecided
rather than "fixed" with a heuristic. This is additional empirical support for Decision
0.3's existing preference for a presence/structure check over numeric comparison in C6 —
the numeric-escalation path is inherently noisier than the rest of C6 for a reason
outside this module's control.

**Two inconsistency patterns found outside C1–C6, logged as future work only (delegated
decision):** the Stage 2 audit surfaced (a) a title-vs-body role mismatch (the advertised
job title doesn't match the role described in the body text) and (b) a
company_profile-vs-description employer mismatch (the company described in the profile
differs from the employer implied in the description). Both are real patterns worth
naming in the dissertation's limitations/future-work section, but neither became a new
rule this stage: C1–C6 is the taxonomy already defined and partially validated against
the 200-posting sample, and extending it now — after seeing these two cases — would be
exactly the kind of post-hoc, result-driven scope change the project's guardrails warn
against ("no objective or research question may presuppose its own result" is the
nearest-in-spirit guardrail, applied here to scope rather than a threshold). See
`decisions.md` for the full decision record.

**C2 gazetteer limitation (restated from the table note above):** ~75 major cities, ~55
ISO country names, and US states — not exhaustive. A genuine location mismatch written
with a place outside this list is under-counted as "not evaluable," not wrongly flagged —
the safer direction for a reported coverage figure.

'''
text = text.replace(anchor, insert + anchor)
assert text != orig
with open(path, "w", encoding="utf-8") as f:
    f.write(text)
print("part 5 OK, net change:", len(text) - len(orig))
