path = "docs/PROJECT_PLAN.md"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()
orig = text

# Day 1 table row — Stage 2 audit status was stale (now complete)
old = "| All day, parallel | **Start the Stage 2 manual audit** — 200 postings | You, alone | ⬜ **Not started — now the critical path** |"
new = "| All day, parallel | **Start the Stage 2 manual audit** — 200 postings | You, alone | ✅ Done — 200/200 coded by hand, `57da423` (finished 2026-10-08, carried into Day 2) |"
assert old in text
text = text.replace(old, new)

# Day 2 checklist bullets
old2 = """- [ ] **Finish the Stage 2 manual audit** if any of the 200 postings remain — this cannot run
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
- [ ] Commit. Tick §7.5 boxes."""
new2 = """- [x] **Finish the Stage 2 manual audit** — all 200 postings coded.
- [x] Build Stage 4: E1 (text/content cues), E2 (identity & contact cues — reuse the token
  logic from Stage 1), E3 (completeness flags + composite), and the real E4 lexicons for
  C1, C3–C6 (replacing every provisional regex from the August audit), plus the **first real
  attempt** at C2 location-matching (not a backfilled proxy). Four precision bugs found
  during full-corpus validation and fixed before any figure was reported — see
  `decisions.md`, 2026-10-08.
- [x] Every feature tagged with its evidence category, for clean leave-one-category-out
  ablation later (E1_/E2_/E3_/C1_.../C6_ prefixes).
- [x] Re-measured C1–C6 evaluable coverage against the real lexicons and updated
  `sources.md` #3 — figures are now final, including C2 (no longer deferred).
- [x] Applied the Decision 0.3 resolution; reconciled the numeric-escalation margin against
  it, logged as its own decision (`decisions.md`, 2026-10-08).
- [x] Stage 2 audit finding applied: the field-presence NaN-handling bug (logged in
  `methodology.md`/`decisions.md`) directly motivated designing Stage 4's rules on
  linguistic principle rather than loose presence checks.
- [ ] Commit. Tick §7.5 boxes. _(commit is the student's own step — not done by AI per the
  project's standing instruction; boxes below ticked now that the work is verified done)_"""
assert old2 in text
text = text.replace(old2, new2)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)
print("part A OK, net change:", len(text) - len(orig))
