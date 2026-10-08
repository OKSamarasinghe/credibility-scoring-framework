path = "docs/methodology.md"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()
orig = text

old = """**Why C2 is deferred, not estimated:** C2's premise — a place name in free text differing
from the structured field — is an open-vocabulary problem. A quick regex proxy, unlike the
bounded vocabularies used for C1/C3 (remote/on-site language, employment-arrangement
language), would amount to a second, weaker implementation of the rule that is guaranteed to
disagree with the real Stage 4 location matcher. Field coverage (88.4%) is reported as an
explicit upper bound only."""

new = """**C2, Stage 4 (2026-10-08) — no longer deferred:** the real location matcher only
counts a place name found via an explicit cue phrase ("based in X", "relocate to X",
"location: X", ...) against a modest hardcoded gazetteer (~75 major cities, ~55 ISO
country names, US states) — never a blind scan of the whole posting, which would
false-positive constantly (a company_profile naming other offices or eligibility
clauses — "Canada/US passport holders only" — is not a claim about where *this* job is).
This is a genuine but partial implementation: the gazetteer is not exhaustive, so a real
place-name mismatch written with a city or country outside the lexicon is silently
under-counted as "not evaluable" rather than wrongly flagged — the limitation is biased
toward under-claiming, not over-claiming, which is the safer direction for a coverage
figure reported as a finding."""

assert old in text, "C2 deferred paragraph not found"
text = text.replace(old, new)

old2 = """**Why C1, C3–C6 are "provisional," not final:** all five use placeholder pattern-matching
written for audit purposes, not the final Stage 4 lexicons. **Re-measure every one of these
figures once Stage 4 lexicons are frozen** — do not carry today's numbers into the
dissertation as final results.

**What this means for E4 as a whole:** the original field-coverage estimates (used since
2026-08-07) implied E4 was observable on nearly every posting. The measured, honestly-defined
picture is that under half the corpus (56.7%) can be evaluated by even one rule, and on
average less than one rule per posting (0.88 of 6) can fire at all. This is a real and
significant finding about the practical reach of the consistency-verification contribution —
not a data-quality failure, but something the dissertation must state plainly and account
for, rather than let the original optimistic estimate stand uncorrected."""

new2 = """**C1, C3–C6, Stage 4 (2026-10-08) — real lexicons, final.** The provisional
placeholder patterns from the August audit have been fully replaced; see "Stage 4 multi-signal
evidence extraction" below for the design approach, the four precision bugs found during
full-corpus validation and fixed before any figure above was reported, and the
methodological safeguard taken against tuning these lexicons to the Stage 2 audit sample.

**What this means for E4 as a whole:** the original field-coverage estimates (used since
2026-08-07) implied E4 was observable on nearly every posting. The final, measured picture
(full corpus, real lexicons) is that well under half the corpus (42.65%) can be evaluated
by even one rule, and on average under one rule per posting (0.597 of 6) can fire at all —
lower than even the provisional August estimate (56.7% / 0.88 of 6), because the real
lexicons require an unambiguous signal rather than a loose topic mention. This is a real
and significant finding about the practical reach of the consistency-verification
contribution — not a data-quality failure, but something the dissertation must state
plainly and account for, rather than let either the original optimistic estimate or the
provisional August figure stand as final."""

assert old2 in text, "provisional paragraph not found"
text = text.replace(old2, new2)
assert text != orig

with open(path, "w", encoding="utf-8") as f:
    f.write(text)
print("part 3 OK, net change:", len(text) - len(orig))
