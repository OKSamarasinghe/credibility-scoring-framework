path = "docs/methodology.md"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()
orig = text

old = """| ID | Rule | Trigger | Field coverage (measured) | Evaluable coverage (measured) | Status |
|---|---|---|---|---|---|
| C1 | Remote / on-site | `telecommuting` conflicts with remote/on-site language in description | **100.0%** | **10.5%** | 🟡 Provisional — placeholder pattern |
| C2 | Location mismatch | location field absent from text while a different location is named | **88.4%** | **not measured** | ❌ Deferred to Stage 4 — see note |
| C3 | Employment type | `employment_type` conflicts with working-arrangement language | **80.6%** | **12.2%** | 🟡 Provisional |
| C4 | Experience level | `required_experience` conflicts with "N+ years" extracted from text | **60.6%** | **30.2%** | 🟡 Provisional |
| C5 | Education | `required_education` conflicts with qualification statements | **54.7%** | **27.8%** | 🟡 Provisional |
| C6 | Salary | description figures fall outside parsed `salary_range` | **15.2%** | **7.6%** | 🟡 Provisional |

**Aggregate (measured, 2026-08-27):** postings evaluable by at least one rule: **10,145
(56.7%)** of 17,880. Mean rules evaluable per posting: **0.88 of 6**."""

new = """| ID | Rule | Trigger | Field coverage (measured) | Evaluable coverage (measured) | Status |
|---|---|---|---|---|---|
| C1 | Remote / on-site | `telecommuting` conflicts with remote/on-site language in description | **100.0%** | **0.50%** | ✅ Final, Stage 4 — real lexicon |
| C2 | Location mismatch | location field absent from text while a different location is named | **98.1%** | **6.92%** | ✅ Final, Stage 4 — first real location matcher (cue-phrase gated) |
| C3 | Employment type | `employment_type` conflicts with working-arrangement language | **80.6%** | **15.17%** | ✅ Final, Stage 4 — real lexicon |
| C4 | Experience level | `required_experience` conflicts with "N+ years" extracted from text | **60.6%** | **20.56%** | ✅ Final, Stage 4 — real lexicon |
| C5 | Education | `required_education` conflicts with qualification statements | **54.7%** | **15.32%** | ✅ Final, Stage 4 — real lexicon |
| C6 | Salary | description figures fall outside parsed `salary_range` | **15.25%** | **1.22%** | ✅ Final, Stage 4 — real lexicon; see unit-ambiguity note below |

**Aggregate (measured, full corpus n=17,880, 2026-10-08, final Stage 4 lexicons):**
postings evaluable by at least one rule: **7,625 (42.65%)**. Mean rules evaluable per
posting: **0.597 of 6**. Contradiction rate per evaluable rule: C1 50.00%; C2 9.61%; C3
10.84%; C4 2.20%; C5 4.93%; C6 23.74%. Postings with at least one contradiction: **709
(3.97%)**. Full breakdown in `reports/stage4_coverage_report.json`.

**Why evaluable coverage dropped sharply from the provisional estimates above** (e.g. C1
10.5% → 0.50%, C3 12.2% → 15.17% is close but C4/C5 roughly halved): the provisional
patterns from the August audit counted a rule as "evaluable" far more loosely than the
real Stage 4 lexicons do. The real lexicons require an unambiguous signal, not merely a
topic mention — e.g. C1 now requires a genuine remote/on-site position claim, not any
mention of "work from home" (see the precision-bug note below). Lower evaluable coverage
with a stricter, more defensible definition of "evaluable" is the expected and intended
outcome of replacing placeholder patterns with real ones, not a regression."""

assert old in text, "C1-C6 table not found"
text = text.replace(old, new)
assert text != orig

with open(path, "w", encoding="utf-8") as f:
    f.write(text)
print("part 2 OK, net change:", len(text) - len(orig))
