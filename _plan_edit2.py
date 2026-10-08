path = "docs/PROJECT_PLAN.md"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()
orig = text

old = """### Stage 2 — Evidence taxonomy + manual audit

- [x] Sample, worksheet, coding scheme built and committed
- [ ] **Manual coding of 200 postings (Day 1–2 — yours alone, not started yet)**
- [ ] Per-category observability rate computed (Day 2)
- [ ] Per-rule agreement rate computed (Day 2)
- [ ] At least one signal revised/dropped based on audit findings, logged (Day 2)
- [ ] Results written into `methodology.md` (Day 2)"""
new = """### Stage 2 — Evidence taxonomy + manual audit

- [x] Sample, worksheet, coding scheme built and committed
- [x] **Manual coding of 200 postings** — complete, `57da423`
- [x] Per-category observability rate computed
- [x] Per-rule agreement rate computed
- [x] At least one signal revised/dropped based on audit findings, logged (field-presence
  NaN-handling bug, caught twice — see `decisions.md`)
- [x] Results written into `methodology.md`"""
assert old in text
text = text.replace(old, new)

old2 = """- [x] Duplicate counts reported using the resolved grouping method (4,762 / 26.63%,
  matches the August audit exactly)
- [ ] Vectorisers/scalers/encoders fit on train only — Stage 5's task, not Stage 3's
- [ ] Results written into `methodology.md`"""
new2 = """- [x] Duplicate counts reported using the resolved grouping method (4,762 / 26.63%,
  matches the August audit exactly)
- [ ] Vectorisers/scalers/encoders fit on train only — Stage 5's task, not Stage 3's
- [x] Results written into `methodology.md`"""
assert old2 in text
text = text.replace(old2, new2)

old3 = """### Stage 4 — Multi-signal evidence extraction (Day 2)

- [ ] E1, E2, E3 features built
- [ ] E4 / C1–C6 real lexicons written, replacing every provisional pattern
- [ ] C2 real location-matching logic built (first real attempt)
- [ ] Every feature tagged with its category for clean ablation
- [ ] All C1–C6 evaluable-coverage figures re-measured against real lexicons
- [ ] Decision 0.3 applied consistently"""
new3 = """### Stage 4 — Multi-signal evidence extraction (Day 2)

- [x] E1, E2, E3 features built
- [x] E4 / C1–C6 real lexicons written, replacing every provisional pattern
- [x] C2 real location-matching logic built (first real attempt)
- [x] Every feature tagged with its category for clean ablation
- [x] All C1–C6 evaluable-coverage figures re-measured against real lexicons
- [x] Decision 0.3 applied consistently (and reconciled — see `decisions.md`, 2026-10-08)"""
assert old3 in text
text = text.replace(old3, new3)

assert text != orig
with open(path, "w", encoding="utf-8") as f:
    f.write(text)
print("part B OK, net change:", len(text) - len(orig))
