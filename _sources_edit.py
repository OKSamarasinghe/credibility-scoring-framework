path = "docs/sources.md"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()
orig = text

old = """## 3. 🟡 Consistency rule coverage C1–C6 — MEASURED 2026-08-27, but PARTIALLY and PROVISIONALLY

- **Claim:** Per-rule field coverage AND evaluable coverage for C1–C6, for
  `Research_Methodology_Final.docx` §3.1.
- **Original claim (now superseded):** field coverage C1 100%, C2 98%, C3 81%, C4 61%,
  C5 55%, C6 16% — AI model, 2026-08-07, derived by inference, not measured. **This
  estimate is now replaced by the measured figures below.**
- **Measured field coverage (2026-08-27, real CSV, n = 17,880):**

  | Rule | Field coverage (measured) | Was estimated |
  |---|---|---|
  | C1 Remote/on-site | 100.0% | 100% |
  | C2 Location mismatch | 88.4% | 98% |
  | C3 Employment type | 80.6% | 81% |
  | C4 Experience level | 60.6% | 61% |
  | C5 Education | 54.7% | 55% |
  | C6 Salary | 15.2% | 16% |

  **Field coverage is VERIFIED** — directly measured on the real CSV, reproduced
  identically across two independent environments.

- **Measured evaluable coverage (2026-08-27) — the honest number for the methodology
  table, but NOT yet fully verified:**

  | Rule | Evaluable coverage | Status |
  |---|---|---|
  | C1 | 10.5% | 🟡 PROVISIONAL — placeholder pattern (see note below) |
  | C2 | **not measured** | ❌ DEFERRED to Stage 4 — see note below |
  | C3 | 12.2% | 🟡 PROVISIONAL |
  | C4 | 30.2% | 🟡 PROVISIONAL |
  | C5 | 27.8% | 🟡 PROVISIONAL |
  | C6 | 7.6% | 🟡 PROVISIONAL |

  Aggregate: **postings evaluable by at least one rule: 10,145 (56.7%)**; mean rules
  evaluable per posting: **0.88 of 6**. An earlier draft of this audit used an inconsistent
  definition of "evaluable" (loose for C1–C3, strict for C4–C6) and reported false figures
  of 100% and 3.35 — corrected 2026-08-27, see `decisions.md` (Decision 0.1).

- **Why "provisional" (C1, C3–C6):** these five figures use the *audit script's own*
  placeholder pattern-matching (regexes for remote/on-site language, employment-arrangement
  language, "N years," education words, money words) — not the final Stage 4 lexicons.
  They must be **re-measured once Stage 4 lexicons are frozen**, and may change.

- **Why C2 has no evaluable figure at all:** C2's premise is that a place name in the free
  text differs from the structured `location` field — genuine location extraction, an
  open-vocabulary problem that cannot be honestly approximated with a quick regex (unlike
  C1/C3, whose vocabularies are small and enumerable). Building a placeholder regex for it
  now would create a second, weaker implementation of the rule that would disagree with the
  real Stage 4 matcher. Field coverage (88.4%) is reported as an explicit **upper bound**
  only. Decision logged in `decisions.md`, 2026-08-27.
- **Verified:** Field coverage — YES. Evaluable coverage — PARTIAL (C1, C3–C6 provisional;
  C2 not measured). **Do not mark this item fully verified.**
- **Action:** Re-measure C1, C3–C6 evaluable coverage against final Stage 4 lexicons before
  they enter the dissertation as final figures. Build C2's real location-matching logic in
  Stage 4, then measure it for the first time — do not backfill a proxy."""

new = """## 3. ✅ Consistency rule coverage C1–C6 — MEASURED, FINAL (2026-10-08, real Stage 4 lexicons)

- **Claim:** Per-rule field coverage AND evaluable coverage for C1–C6, for
  `Research_Methodology_Final.docx` §3.1.
- **Superseded history:** an AI-inferred estimate (2026-08-07) was replaced by a measured
  but provisional figure (2026-08-27, placeholder audit-script patterns) which is now itself
  replaced by the figures below — the real Stage 4 lexicons (`src/features/extract_features.py`),
  run against the full corpus (n = 17,880), after four precision bugs found during full-corpus
  validation were fixed (see `decisions.md`, 2026-10-08, and `methodology.md`'s Stage 4
  section for the bug list).
- **Measured field coverage (2026-10-08, real CSV, n = 17,880):**

  | Rule | Field coverage (measured) |
  |---|---|
  | C1 Remote/on-site | 100.0% |
  | C2 Location mismatch | 98.1% |
  | C3 Employment type | 80.6% |
  | C4 Experience level | 60.6% |
  | C5 Education | 54.7% |
  | C6 Salary | 15.25% |

- **Measured evaluable coverage (2026-10-08, final, real lexicons) — all six rules, C2
  included:**

  | Rule | Evaluable coverage | Contradiction rate (of evaluable) |
  |---|---|---|
  | C1 | 0.50% | 50.00% |
  | C2 | 6.92% | 9.61% |
  | C3 | 15.17% | 10.84% |
  | C4 | 20.56% | 2.20% |
  | C5 | 15.32% | 4.93% |
  | C6 | 1.22% | 23.74% |

  Aggregate: **postings evaluable by at least one rule: 7,625 (42.65%)**; mean rules
  evaluable per posting: **0.597 of 6**; postings with at least one contradiction: **709
  (3.97%)**. Full breakdown: `reports/stage4_coverage_report.json`.
- **Why evaluable coverage is lower than the provisional 2026-08-27 figures:** the real
  lexicons require an unambiguous signal (e.g. a genuine remote-position claim), not a loose
  topic mention (e.g. any "work from home" phrase, including flexible-working perks) — see
  `methodology.md` for the full explanation. Lower coverage under a stricter, correct
  definition is expected, not a regression.
- **C2, now measured for the first time:** a real location matcher (cue-phrase gated against
  a ~75-city/~55-country gazetteer) replaces the deferred placeholder. The gazetteer is not
  exhaustive, so a genuine mismatch naming a place outside it is under-counted as "not
  evaluable," not wrongly flagged — a documented, safely-directed limitation.
- **Verified:** Field coverage — YES. Evaluable coverage — YES, all six rules, final. **This
  item may now be marked fully verified and cited as a final result.**
- **Residual limitation (not a verification gap):** `salary_range`'s own units are
  ambiguous for ~10.3% of present values (a mix of literal dollars, unmarked "thousands"
  shorthand, and hourly rates) — a property of the EMSCAD field itself, not of this
  measurement. Logged in `methodology.md`; do not attempt to resolve by guessing units."""

assert old in text, "sources.md #3 entry not found"
text = text.replace(old, new)
assert text != orig
with open(path, "w", encoding="utf-8") as f:
    f.write(text)
print("sources.md #3 OK, net change:", len(text) - len(orig))
