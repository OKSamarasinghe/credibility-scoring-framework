"""
Stage 5 — Baseline models (O2): TF-IDF + Logistic Regression, TF-IDF + Random Forest
======================================================================================
An Explainable Credibility Scoring Framework for Online Recruitment Posts
O.K. Samarasinghe — COBSCCOMP242P-069

PURPOSE
    The O2 baseline: text-only models (TF-IDF features, no structured E2/E3/E4 evidence),
    against which Stage 5's improved model (DistilBERT + fused structured evidence) is
    compared for O3 ("does multi-signal evidence help?"). Per Decision (2026-08-07, "Use
    class weighting for both models"), this is the FIRST of the two arms that must differ
    in only one thing from the improved model: the presence of structured evidence. Both
    arms use identical class weighting and the identical leakage-controlled split.

WHAT THIS DOES NOT DO
    - Does not touch the test split. Per the project's guardrail ("test set used once") and
      the Day 3/Stage 5 checklist, validation is used for all metrics reported here; the
      test split is reserved for Stage 9's one-time final evaluation (baseline + improved +
      ablation, together).
    - Does not use SMOTE. Class weighting only, per the 2026-08-07 decision — SMOTE is a
      separate, clearly labelled supplementary arm (not built here).
    - Does not invent a train/val/test split. It reads the `split` column already produced
      by Stage 3 (`src/partitioning/split_data.py`, commit 9a5379b), group-aware and
      leakage-controlled, fixed seed 42.

INPUT
    data/interim/stage3_split.csv — Stage 3's full-corpus output: every Stage 1 column plus
    `group_id` and `split` (train/val/test). Re-run `python -m src.partitioning.split_data
    data/raw/DataSet.csv` first if this file doesn't exist yet (it's gitignored, since it's
    a ~60MB derived file, not source data).

TEXT INPUT TO TF-IDF
    title + description + requirements + benefits, concatenated and HTML-stripped — the
    same text scope Stage 4's E1 lexicon uses (`extract_features._norm_text`'s four
    source columns), so the baseline and the later DistilBERT arm see a consistent
    definition of "the posting's text," not two different ad-hoc choices.

CLASS IMBALANCE
    `class_weight="balanced"` for both LogisticRegression and RandomForestClassifier —
    sklearn computes this automatically from the training fold's actual class frequencies,
    so "identical settings" holds by construction across both models (and, later, across
    the DistilBERT arm, which must apply the equivalent weighting at the loss level).

SEEDS
    Per decisions.md (2026-09-20, "3 seeds means 3 model initialisations against one fixed
    train/validation/test split"): loops over SEEDS below, reports mean +/- SD. For
    LogisticRegression (lbfgs solver) this is close to deterministic given fixed data: the
    seed loop is kept anyway for consistency with the convention used everywhere else in
    this project, and because RandomForestClassifier is genuinely seed-sensitive.

OUTPUT
    - reports/stage5_baseline_results.json — per-seed and mean+/-SD metrics for both models.
    - models/baseline_tfidf_vectorizer.joblib, models/baseline_logreg.joblib,
      models/baseline_rf.joblib — the seed-0 fit, saved for Stage 8's API wiring and
      Stage 9's one-time test-set evaluation. (Seed 0 chosen arbitrarily as "the" saved
      model; all three seeds' validation metrics are reported, not just seed 0's.)
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

SEEDS = [0, 1, 2]
SPLIT_CSV = "data/interim/stage3_split.csv"
TEXT_COLS = ["title", "description", "requirements", "benefits"]
TFIDF_MAX_FEATURES = 20000  # documented choice, not tuned against validation performance
TFIDF_NGRAM_RANGE = (1, 2)
MODELS_DIR = Path("models")
REPORTS_DIR = Path("reports")


def _build_text(df: pd.DataFrame) -> pd.Series:
    return df[TEXT_COLS].fillna("").agg(" ".join, axis=1)


def _metrics(y_true, y_pred, y_proba) -> dict:
    return {
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "pr_auc": average_precision_score(y_true, y_proba),
        "roc_auc": roc_auc_score(y_true, y_proba),
    }


def _mean_sd(per_seed: list) -> dict:
    keys = per_seed[0].keys()
    out = {}
    for k in keys:
        vals = np.array([m[k] for m in per_seed])
        out[k] = {"mean": float(vals.mean()), "sd": float(vals.std(ddof=1)) if len(vals) > 1 else 0.0}
    return out


def run(split_csv: str = SPLIT_CSV):
    if not Path(split_csv).exists():
        print(
            f"ERROR: {split_csv} not found. Run Stage 3 first:\n"
            f"  python -m src.partitioning.split_data data/raw/DataSet.csv",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Loading {split_csv} ...")
    df = pd.read_csv(split_csv)
    for col in TEXT_COLS + ["fraudulent", "split"]:
        if col not in df.columns:
            raise KeyError(f"expected column '{col}' not found in {split_csv}")

    train = df[df["split"] == "train"].reset_index(drop=True)
    val = df[df["split"] == "val"].reset_index(drop=True)
    print(f"train: {len(train)} rows ({train['fraudulent'].sum()} fraud)")
    print(f"val:   {len(val)} rows ({val['fraudulent'].sum()} fraud)")

    train_text = _build_text(train)
    val_text = _build_text(val)
    y_train = train["fraudulent"].astype(int).values
    y_val = val["fraudulent"].astype(int).values

    results = {"logreg": [], "rf": []}
    saved_models = {}

    for seed in SEEDS:
        print(f"\n--- seed {seed} ---")
        t0 = time.time()

        # TF-IDF fit on train only, per seed (deterministic given fixed text and params,
        # but refit inside the loop so each seed's model is trained against an identically
        # produced vectorizer, not a shared mutable one).
        vectorizer = TfidfVectorizer(
            max_features=TFIDF_MAX_FEATURES,
            ngram_range=TFIDF_NGRAM_RANGE,
            min_df=2,
        )
        X_train = vectorizer.fit_transform(train_text)
        X_val = vectorizer.transform(val_text)

        logreg = LogisticRegression(
            class_weight="balanced", max_iter=1000, random_state=seed
        )
        logreg.fit(X_train, y_train)
        logreg_proba = logreg.predict_proba(X_val)[:, 1]
        logreg_pred = (logreg_proba >= 0.5).astype(int)
        results["logreg"].append(_metrics(y_val, logreg_pred, logreg_proba))
        print(f"  LogReg done in {time.time() - t0:.1f}s")

        t1 = time.time()
        rf = RandomForestClassifier(
            n_estimators=300, class_weight="balanced", random_state=seed, n_jobs=-1
        )
        rf.fit(X_train, y_train)
        rf_proba = rf.predict_proba(X_val)[:, 1]
        rf_pred = (rf_proba >= 0.5).astype(int)
        results["rf"].append(_metrics(y_val, rf_pred, rf_proba))
        print(f"  RF done in {time.time() - t1:.1f}s")

        if seed == SEEDS[0]:
            saved_models["vectorizer"] = vectorizer
            saved_models["logreg"] = logreg
            saved_models["rf"] = rf

    summary = {
        "seeds": SEEDS,
        "n_train": len(train),
        "n_val": len(val),
        "text_columns": TEXT_COLS,
        "tfidf": {"max_features": TFIDF_MAX_FEATURES, "ngram_range": list(TFIDF_NGRAM_RANGE)},
        "class_weight": "balanced",
        "per_seed": results,
        "mean_sd": {
            "logreg": _mean_sd(results["logreg"]),
            "rf": _mean_sd(results["rf"]),
        },
    }

    REPORTS_DIR.mkdir(exist_ok=True)
    out_path = REPORTS_DIR / "stage5_baseline_results.json"
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nWritten: {out_path}")
    print(json.dumps(summary["mean_sd"], indent=2))

    try:
        import joblib

        MODELS_DIR.mkdir(exist_ok=True)
        joblib.dump(saved_models["vectorizer"], MODELS_DIR / "baseline_tfidf_vectorizer.joblib")
        joblib.dump(saved_models["logreg"], MODELS_DIR / "baseline_logreg.joblib")
        joblib.dump(saved_models["rf"], MODELS_DIR / "baseline_rf.joblib")
        print(f"Saved seed-{SEEDS[0]} vectorizer + models to {MODELS_DIR}/")
    except ImportError:
        print("joblib not installed -- models not saved to disk (metrics still written).")


if __name__ == "__main__":
    csv_path = sys.argv[1] if len(sys.argv) > 1 else SPLIT_CSV
    run(csv_path)
