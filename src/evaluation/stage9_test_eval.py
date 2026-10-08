"""
Stage 9 — Part 1: ONE-TIME test-set evaluation (O2 baselines + O3 main model)
==============================================================================
An Explainable Credibility Scoring Framework for Online Recruitment Posts
O.K. Samarasinghe — COBSCCOMP242P-069

PURPOSE
    The single, one-time evaluation of all pre-committed model configurations on the
    EMSCAD TEST split (2,682 rows, 130 fraud — Stage 3's leakage-controlled partition).
    This is the event the "test set used once" guardrail protects. See decisions.md,
    2026-10-08, "Stage 9 design decisions" (4 entries) for the reasoning behind every
    choice this script makes -- nothing here is improvised at run time.

WHAT THIS SCRIPT DOES
    1. Refits baseline seeds 1 and 2 (TRAIN ONLY -- train_baseline.py only ever saved
       seed 0 to disk) so baselines get the same 3-seed treatment as the main model
       (Decision 3). Seed 0 is loaded from the existing models/baseline_*.joblib rather
       than refit, so it is bit-identical to what Stage 5 and Stage 8 already use.
    2. Evaluates all 3 baseline seeds (LogReg, RF) ONCE on TEST.
    3. Loads the 3 existing DistilBERT+evidence checkpoints (seeds 0/1/2, already trained
       in Stage 5 -- NOT retrained here) and evaluates each ONCE on TEST.
    4. Reports mean +/- SD for every model, plus Delta F1 / Delta PR-AUC of the main model
       vs. each baseline (O3), computed from the means (same convention as Stage 5's
       validation-side table).
    5. Writes everything to reports/stage9_test_results.json. Prints a summary table.

WHAT THIS SCRIPT DELIBERATELY DOES NOT DO
    - Does not touch validation. Validation's job (model selection, epoch/seed decisions)
      is already finished; re-using it here would not be wrong, but it isn't needed, and
      touching it again invites the temptation to "double check" something before the real
      answer is in -- so this script doesn't read it.
    - Does not retrain or fine-tune the DistilBERT checkpoints. They are loaded exactly as
      Stage 5 produced them.
    - Does not run the ablation arms (separate script, stage9_ablation.py -- those require
      ~2.25 GPU-hours of fresh training and are run as a deliberately separate step).
    - Does not compute or apply a pass/fail threshold (Decision 1 -- thresholds are
      [TO SET], and that does not block computing these numbers).

USAGE
    python -m src.evaluation.stage9_test_eval

    This is real GPU work for the DistilBERT inference pass (3 forward passes over 2,682
    rows -- a few minutes on the RTX 3050, not hours) plus ~30s of CPU work for the
    baseline refits. Run it once, paste the full output back.
"""
import json
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

try:
    from src.models.train_baseline import (
        SEEDS,
        TEXT_COLS,
        TFIDF_MAX_FEATURES,
        TFIDF_NGRAM_RANGE,
        _build_text,
        _metrics,
    )
    from src.models.train_distilbert import (
        BERT_NAME,
        FusedDataset,
        FusedModel,
        build_structured_features,
    )
    from src.features.extract_features import extract_all
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from src.models.train_baseline import (  # noqa: E402
        SEEDS, TEXT_COLS, TFIDF_MAX_FEATURES, TFIDF_NGRAM_RANGE, _build_text, _metrics,
    )
    from src.models.train_distilbert import (  # noqa: E402
        BERT_NAME, FusedDataset, FusedModel, build_structured_features,
    )
    from src.features.extract_features import extract_all  # noqa: E402

from torch.utils.data import DataLoader

SPLIT_CSV = "data/interim/stage3_split.csv"
MODELS_DIR = Path("models")
REPORTS_DIR = Path("reports")
DISTILBERT_SEEDS = [0, 1, 2]
BATCH_SIZE = 16


def _mean_sd(per_seed: list) -> dict:
    keys = per_seed[0].keys()
    out = {}
    for k in keys:
        vals = np.array([m[k] for m in per_seed])
        out[k] = {"mean": float(vals.mean()), "sd": float(vals.std(ddof=1)) if len(vals) > 1 else 0.0}
    return out


def run_baselines(train: pd.DataFrame, test: pd.DataFrame) -> dict:
    """Decision 3: seed 0 loaded from disk (bit-identical to Stage 5/8), seeds 1-2
    refit here on TRAIN ONLY (identical settings to train_baseline.py), all 3 evaluated
    once on TEST."""
    train_text = _build_text(train)
    test_text = _build_text(test)
    y_train = train["fraudulent"].astype(int).values
    y_test = test["fraudulent"].astype(int).values

    results = {"logreg": [], "rf": []}

    for seed in SEEDS:
        t0 = time.time()
        if seed == 0:
            print(f"  seed 0: loading existing models/baseline_*.joblib (not refitting) ...")
            vectorizer = joblib.load(MODELS_DIR / "baseline_tfidf_vectorizer.joblib")
            logreg = joblib.load(MODELS_DIR / "baseline_logreg.joblib")
            rf = joblib.load(MODELS_DIR / "baseline_rf.joblib")
        else:
            print(f"  seed {seed}: refitting on TRAIN only (train_baseline.py was never "
                  f"asked to save this seed) ...")
            vectorizer = TfidfVectorizer(
                max_features=TFIDF_MAX_FEATURES, ngram_range=TFIDF_NGRAM_RANGE, min_df=2,
            )
            X_train = vectorizer.fit_transform(train_text)
            logreg = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=seed)
            logreg.fit(X_train, y_train)
            rf = RandomForestClassifier(
                n_estimators=300, class_weight="balanced", random_state=seed, n_jobs=-1
            )
            rf.fit(X_train, y_train)

        X_test = vectorizer.transform(test_text)

        logreg_proba = logreg.predict_proba(X_test)[:, 1]
        logreg_pred = (logreg_proba >= 0.5).astype(int)
        results["logreg"].append(_metrics(y_test, logreg_pred, logreg_proba))

        rf_proba = rf.predict_proba(X_test)[:, 1]
        rf_pred = (rf_proba >= 0.5).astype(int)
        results["rf"].append(_metrics(y_test, rf_pred, rf_proba))

        print(f"    done in {time.time() - t0:.1f}s -- "
              f"logreg_f1={results['logreg'][-1]['f1']:.4f}, rf_f1={results['rf'][-1]['f1']:.4f}")

    return {
        "per_seed": results,
        "mean_sd": {"logreg": _mean_sd(results["logreg"]), "rf": _mean_sd(results["rf"])},
    }


@torch.no_grad()
def _evaluate_distilbert_seed(seed: int, test: pd.DataFrame, test_feat: pd.DataFrame, device) -> dict:
    scaler = joblib.load(MODELS_DIR / f"distilbert_structured_scaler_seed{seed}.joblib")
    meta = joblib.load(MODELS_DIR / f"distilbert_structured_feature_meta_seed{seed}.joblib")

    X_test_struct, names, _groups = build_structured_features(test_feat)
    if names != meta["feature_names"]:
        raise RuntimeError(
            f"seed {seed}: structured feature name/order mismatch between this run's "
            f"extract_all() output and the meta saved at training time -- would silently "
            f"feed the wrong column into the wrong scaler dimension. Aborting rather than "
            f"guessing."
        )
    X_test_struct = scaler.transform(X_test_struct).astype(np.float32)

    from transformers import DistilBertTokenizerFast
    tokenizer = DistilBertTokenizerFast.from_pretrained(meta["bert_model"])
    test_text = _build_text(test).tolist()
    test_enc = tokenizer(
        test_text, truncation=True, padding=True, max_length=meta["max_length"], return_tensors="pt"
    )
    y_test = test["fraudulent"].astype(int).values
    test_ds = FusedDataset(test_enc, X_test_struct, y_test)
    test_loader = DataLoader(test_ds, batch_size=BATCH_SIZE, shuffle=False)

    model = FusedModel(n_structured=meta["n_structured"]).to(device)
    state_dict = torch.load(MODELS_DIR / f"distilbert_fused_state_dict_seed{seed}.pt", map_location=device)
    model.load_state_dict(state_dict)
    model.eval()

    all_logits, all_labels = [], []
    for batch in test_loader:
        logits = model(
            batch["input_ids"].to(device),
            batch["attention_mask"].to(device),
            batch["structured"].to(device),
        )
        all_logits.append(logits.cpu().numpy())
        all_labels.append(batch["label"].numpy())
    logits = np.concatenate(all_logits)
    y_true = np.concatenate(all_labels).astype(int)
    proba = 1 / (1 + np.exp(-logits))
    pred = (proba >= 0.5).astype(int)
    return _metrics(y_true, pred, proba)


def run_main_model(test: pd.DataFrame) -> dict:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"  device: {device}")
    print("  computing E1-E4 structured features for test split (extract_all) ...")
    test_feat = extract_all(test)

    results = []
    for seed in DISTILBERT_SEEDS:
        t0 = time.time()
        m = _evaluate_distilbert_seed(seed, test, test_feat, device)
        results.append(m)
        print(f"  seed {seed}: {time.time() - t0:.1f}s -- f1={m['f1']:.4f}, pr_auc={m['pr_auc']:.4f}")

    return {"per_seed": results, "mean_sd": _mean_sd(results)}


def main():
    if not Path(SPLIT_CSV).exists():
        print(f"ERROR: {SPLIT_CSV} not found.", file=sys.stderr)
        sys.exit(1)

    print(f"Loading {SPLIT_CSV} ...")
    df = pd.read_csv(SPLIT_CSV)
    train = df[df["split"] == "train"].reset_index(drop=True)
    test = df[df["split"] == "test"].reset_index(drop=True)
    print(f"train: {len(train)} rows ({train['fraudulent'].sum()} fraud)")
    print(f"test:  {len(test)} rows ({test['fraudulent'].sum()} fraud)  <-- TOUCHED FOR THE FIRST TIME NOW")

    print("\n=== Baselines (3 seeds each, seed 0 loaded from disk, seeds 1-2 refit on train) ===")
    baseline_results = run_baselines(train, test)

    print("\n=== Main model: DistilBERT + structured evidence (3 existing checkpoints, inference only) ===")
    main_results = run_main_model(test)

    def delta(main_mean, base_mean):
        return {"f1": main_mean["f1"]["mean"] - base_mean["f1"]["mean"],
                "pr_auc": main_mean["pr_auc"]["mean"] - base_mean["pr_auc"]["mean"]}

    summary = {
        "split": "test",
        "n_test": len(test),
        "n_fraud_test": int(test["fraudulent"].sum()),
        "note": (
            "ONE-TIME evaluation -- see decisions.md, 2026-10-08, 'Stage 9 design "
            "decisions' for what 'used once' means here and why baselines were refit "
            "for seeds 1-2."
        ),
        "baselines": baseline_results,
        "main_model": main_results,
        "delta_vs_baseline": {
            "logreg": delta(main_results["mean_sd"], baseline_results["mean_sd"]["logreg"]),
            "rf": delta(main_results["mean_sd"], baseline_results["mean_sd"]["rf"]),
        },
    }

    REPORTS_DIR.mkdir(exist_ok=True)
    out_path = REPORTS_DIR / "stage9_test_results.json"
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 70)
    print("STAGE 9 TEST RESULTS (one-time, final)")
    print("=" * 70)
    for name, key in [("TF-IDF + LogReg", "logreg"), ("TF-IDF + RF", "rf")]:
        ms = baseline_results["mean_sd"][key]
        print(f"{name:30s} F1={ms['f1']['mean']:.3f}+/-{ms['f1']['sd']:.3f}  "
              f"PR-AUC={ms['pr_auc']['mean']:.3f}+/-{ms['pr_auc']['sd']:.3f}  "
              f"ROC-AUC={ms['roc_auc']['mean']:.3f}+/-{ms['roc_auc']['sd']:.3f}  "
              f"P={ms['precision']['mean']:.3f} R={ms['recall']['mean']:.3f}")
    ms = main_results["mean_sd"]
    print(f"{'DistilBERT + structured':30s} F1={ms['f1']['mean']:.3f}+/-{ms['f1']['sd']:.3f}  "
          f"PR-AUC={ms['pr_auc']['mean']:.3f}+/-{ms['pr_auc']['sd']:.3f}  "
          f"ROC-AUC={ms['roc_auc']['mean']:.3f}+/-{ms['roc_auc']['sd']:.3f}  "
          f"P={ms['precision']['mean']:.3f} R={ms['recall']['mean']:.3f}")
    print(f"\nDelta F1 vs LogReg: {summary['delta_vs_baseline']['logreg']['f1']:+.3f}  "
          f"Delta PR-AUC vs LogReg: {summary['delta_vs_baseline']['logreg']['pr_auc']:+.3f}")
    print(f"Delta F1 vs RF:     {summary['delta_vs_baseline']['rf']['f1']:+.3f}  "
          f"Delta PR-AUC vs RF:     {summary['delta_vs_baseline']['rf']['pr_auc']:+.3f}")
    print(f"\nWritten: {out_path}")


if __name__ == "__main__":
    main()
