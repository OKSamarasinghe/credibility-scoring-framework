path = "docs/PROJECT_PLAN.md"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()
orig = text

old = """### Stage 5 — Model development (Day 3)

- [ ] TF-IDF + Logistic Regression baseline trained
- [ ] TF-IDF + Random Forest baseline trained
- [ ] One DistilBERT fine-tuning run timed; ablation seed count decided and logged
- [ ] Identical class weighting confirmed on both models
- [ ] Hyperparameters/threshold fitted on validation only
- [ ] 3-seed repetition completed on the main comparison, mean ± SD reported
- [ ] Test set not yet touched"""
new = """### Stage 5 — Model development (Day 3)

- [x] TF-IDF + Logistic Regression baseline trained (0.556 F1, 0.931 ROC-AUC, validation)
- [x] TF-IDF + Random Forest baseline trained (0.513 F1, 0.940 ROC-AUC, validation)
- [ ] One DistilBERT fine-tuning run timed; ablation seed count decided and logged
- [x] Identical class weighting confirmed on both baseline models (`class_weight="balanced"`)
- [ ] Hyperparameters/threshold fitted on validation only (improved model — baseline used
  default 0.5 threshold, no tuning)
- [x] 3-seed repetition completed on the baseline comparison, mean ± SD reported — improved
  model's 3-seed run still pending the seed-count decision below
- [x] Test set not yet touched"""
assert old in text
text = text.replace(old, new)
assert text != orig
with open(path, "w", encoding="utf-8") as f:
    f.write(text)
print("OK, net change:", len(text) - len(orig))
