path = "docs/project.md"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()
orig = text

old = """- **Phase:** 5-day sprint to completion, started 2026-10-06, now in Day 1 afternoon.
  **See `PROJECT_PLAN.md` §0 for the full day-by-day plan** — it is now the live operational
  document; this section stays as the narrative summary."""
new = """- **Phase:** 5-day sprint to completion, started 2026-10-06, now in Day 2
  (2026-10-08). **See `PROJECT_PLAN.md` §0 for the full day-by-day plan** — it is now the
  live operational document; this section stays as the narrative summary."""
assert old in text
text = text.replace(old, new)

old2 = """- **Not yet started:** the Stage 2 manual audit (200 postings) — **this is now the single
  biggest open Day 1–2 task, and it is mine alone to do, not something to hand off.**
  Stages 4–9 in full. Chapters 4–6 of the dissertation (Chapter 4 cannot be drafted until
  Stage 9 produces real measurements — now scheduled for Day 4–5 of the sprint). The git
  commit-attribution fix is fully closed (pushed, confirmed on GitHub) — nothing left there."""
new2 = """- **Stage 2 manual audit — complete, 2026-10-08:** all 200 postings coded by hand,
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
  on GitHub) — nothing left there."""
assert old2 in text
text = text.replace(old2, new2)

assert text != orig
with open(path, "w", encoding="utf-8") as f:
    f.write(text)
print("project.md edit OK, net change:", len(text) - len(orig))
