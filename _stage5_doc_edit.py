path = "docs/methodology.md"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()
orig = text

old = """### Baseline results (O2) — [DATE]

| Model | Precision | Recall | F1 (fraud) | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|
| TF-IDF + LogReg | | | | | |
| TF-IDF + RF | | | | | |"""

new = """### Baseline results (O2) — 2026-10-08

_Measured by `src.models.train_baseline` against `data/interim/stage3_split.csv`
(Stage 3's leakage-controlled split, seed 42). Evaluated on **validation only** — test
stays untouched until Stage 9's one-time evaluation. Text input: title+description+
requirements+benefits (same scope as Stage 4's E1 lexicon). `class_weight="balanced"`
on both models, identically (Decision, 2026-08-07) — no SMOTE. 3 seeds (0/1/2), mean ± SD.
Run on the student's own pinned venv (not this project's sandbox), ~8s/seed LogReg,
~4s/seed RF. Full per-seed detail: `reports/stage5_baseline_results.json`._

| Model | Precision | Recall | F1 (fraud) | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|
| TF-IDF + LogReg | 0.464 ± ~0 | 0.692 ± ~0 | 0.556 ± 0 | 0.655 ± 0 | 0.931 ± 0 |
| TF-IDF + RF | 0.881 ± 0.009 | 0.362 ± 0 | 0.513 ± 0.002 | 0.682 ± 0.003 | 0.940 ± 0.003 |

**Reading this, not just reporting it:** LogReg and RF trade off very differently at the
default 0.5 threshold — LogReg catches more fraud (69.2% recall) at the cost of more false
positives (46.4% precision); RF is the reverse (88.1% precision, 36.2% recall). Neither
number is "the" baseline result on its own; which one a risk-band threshold should resemble
is a Stage 6 calibration question, not decided here. SD is ~0 for LogReg (the `lbfgs`
solver is close to deterministic given fixed data) and small for RF (genuine seed
sensitivity, as expected). These are the numbers the improved model (O3) must beat to
justify the added complexity of DistilBERT + structured evidence."""

assert old in text, "baseline table not found"
text = text.replace(old, new)
assert text != orig
with open(path, "w", encoding="utf-8") as f:
    f.write(text)
print("OK, net change:", len(text) - len(orig))
