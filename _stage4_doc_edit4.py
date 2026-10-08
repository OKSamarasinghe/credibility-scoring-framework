path = "docs/methodology.md"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()
orig = text

old = """**Measured coverage C1–C6:** see the Consistency rule set table above (Evidence taxonomy
section) — field coverage fully verified for all six rules; evaluable coverage measured but
provisional for C1, C3–C6; deferred entirely for C2 pending Stage 4 location matching.
Aggregate: 56.7% of postings evaluable by at least one rule; mean 0.88 rules evaluable per
posting."""

new = """**Measured coverage C1–C6 (final, Stage 4, 2026-10-08):** see the Consistency rule set
table above (Evidence taxonomy section) — field coverage fully verified for all six rules;
evaluable coverage now final for all six, including C2 (real location matcher, no longer
deferred). Aggregate: 42.65% of postings evaluable by at least one rule; mean 0.597 rules
evaluable per posting; see "Stage 4 multi-signal evidence extraction" below for the full
results log."""

assert old in text
text = text.replace(old, new)
assert text != orig
with open(path, "w", encoding="utf-8") as f:
    f.write(text)
print("part 4 OK, net change:", len(text) - len(orig))
