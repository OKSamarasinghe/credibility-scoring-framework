"""
Stage 9 — Part 2: Leave-one-category-out ablation (O5)
=========================================================
An Explainable Credibility Scoring Framework for Online Recruitment Posts
O.K. Samarasinghe — COBSCCOMP242P-069

PURPOSE
    5 arms (E1, E2, E3, E4, has_company_logo), 1 seed each (seed 0), 5 epochs each --
    the seed/epoch budget closed 2026-10-06 and 2026-10-08 from a measured ~324.5s/epoch
    timing (~2.25 GPU-hours total). Each arm trains a FRESH FusedModel from scratch with
    that category's structured features removed, checkpointed on best VALIDATION F1 (same
    convention as Stage 5 -- does not touch test), then evaluated ONCE on TEST. See
    decisions.md, 2026-10-08, "Stage 9 design decisions" (4 entries) for why ablation is
    allowed to touch test at all (Decision 2) and what it's compared against (Decision 4).

COMPARISON BASIS (Decision 4)
    Each arm's test result is compared to the FULL model's SEED-0 test result (read from
    reports/stage9_test_results.json, produced by stage9_test_eval.py -- NOT the 3-seed
    mean), because the ablation is itself only 1 seed. Comparing 1 seed to 1 seed keeps
    both sides of the delta on the same noise footing.

THE has_company_logo ARM
    Not a STRUCTURED_FEATURE_GROUPS group on its own -- it's one field inside E3. This
    script removes just the single `E3_has_company_logo_present` column after building the
    full E1-E4 vector, rather than the whole E3 group.

RESUMABILITY
    Each arm's result is written to reports/stage9_ablation_results.json as soon as that
    arm finishes (not only at the very end) -- a ~2.25-hour run is long enough that a crash
    or a closed laptop lid shouldn't cost finished arms. Re-running this script skips any
    arm already present in that file.

SANITY CHECK BEFORE THE REAL RUN
    This script's training loop is new code (train_distilbert.py's run() was not reused
    directly, since it isn't parameterised by excluded group) -- exactly the kind of code
    this project has found real bugs in before. Run the subsample sanity check FIRST:
        python -m src.evaluation.stage9_ablation --subsample 300 --epochs 1
    This does NOT save checkpoints or write to the results JSON (matching
    train_distilbert.py's convention) -- it only proves every arm's feature-exclusion path
    runs end-to-end without a shape/column error, in under a minute, before any real GPU
    time is spent.

    Then the real run:
        python -m src.evaluation.stage9_ablation

OUTPUT
    - reports/stage9_ablation_results.json
    - models/stage9_ablation_{arm}_seed0.pt / _scaler_seed0.joblib /
      _feature_meta_seed0.joblib -- one checkpoint per arm, for reproducibility.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader

try:
    from src.models.train_baseline import TEXT_COLS, _build_text
    from src.models.train_distilbert import (
        BERT_NAME, FusedDataset, FusedModel, build_structured_features, _evaluate,
    )
    from src.features.extract_features import extract_all
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from src.models.train_baseline import TEXT_COLS, _build_text  # noqa: E402
    from src.models.train_distilbert import (  # noqa: E402
        BERT_NAME, FusedDataset, FusedModel, build_structured_features, _evaluate,
    )
    from src.features.extract_features import extract_all  # noqa: E402

SPLIT_CSV = "data/interim/stage3_split.csv"
MODELS_DIR = Path("models")
REPORTS_DIR = Path("reports")
RESULTS_PATH = REPORTS_DIR / "stage9_ablation_results.json"
FULL_MODEL_RESULTS_PATH = REPORTS_DIR / "stage9_test_results.json"

ARMS = ["E1", "E2", "E3", "E4", "has_company_logo"]
SEED = 0
EPOCHS = 5
BATCH_SIZE = 16
MAX_LENGTH = 256
LR = 2e-5


def build_ablation_features(features_df: pd.DataFrame, arm: str):
    """Same contract as build_structured_features: returns (X, names, groups).
    `has_company_logo` is a single column inside E3, not a whole group -- removed
    post-hoc rather than via exclude_groups."""
    if arm == "has_company_logo":
        X, names, groups = build_structured_features(features_df)
        col = "E3_has_company_logo_present"
        if col not in names:
            raise KeyError(f"expected column '{col}' not found -- cannot build the "
                            f"has_company_logo ablation arm")
        drop_idx = names.index(col)
        keep = [i for i in range(len(names)) if i != drop_idx]
        return X[:, keep], [names[i] for i in keep], [groups[i] for i in keep]
    return build_structured_features(features_df, exclude_groups=[arm])


def train_one_arm(arm: str, train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame,
                   device, epochs: int, subsample: bool) -> dict:
    print(f"  computing E1-E4 structured features (extract_all) for arm '{arm}' ...")
    train_feat = extract_all(train)
    val_feat = extract_all(val)
    test_feat = extract_all(test)

    X_train, names, groups = build_ablation_features(train_feat, arm)
    X_val, val_names, _ = build_ablation_features(val_feat, arm)
    X_test, test_names, _ = build_ablation_features(test_feat, arm)
    if val_names != names or test_names != names:
        raise RuntimeError(f"arm '{arm}': feature name/order mismatch across "
                            f"train/val/test -- aborting rather than misaligning columns")
    print(f"  structured vector: {len(names)} features (full model has 46), "
          f"groups present: {sorted(set(groups))}")

    scaler = StandardScaler().fit(X_train)
    X_train = scaler.transform(X_train).astype(np.float32)
    X_val = scaler.transform(X_val).astype(np.float32)
    X_test = scaler.transform(X_test).astype(np.float32)

    y_train = train["fraudulent"].astype(int).values
    y_val = val["fraudulent"].astype(int).values
    y_test = test["fraudulent"].astype(int).values

    from transformers import DistilBertTokenizerFast
    tokenizer = DistilBertTokenizerFast.from_pretrained(BERT_NAME)
    train_text = _build_text(train).tolist()
    val_text = _build_text(val).tolist()
    test_text = _build_text(test).tolist()
    train_enc = tokenizer(train_text, truncation=True, padding=True, max_length=MAX_LENGTH, return_tensors="pt")
    val_enc = tokenizer(val_text, truncation=True, padding=True, max_length=MAX_LENGTH, return_tensors="pt")
    test_enc = tokenizer(test_text, truncation=True, padding=True, max_length=MAX_LENGTH, return_tensors="pt")

    train_ds = FusedDataset(train_enc, X_train, y_train)
    val_ds = FusedDataset(val_enc, X_val, y_val)
    test_ds = FusedDataset(test_enc, X_test, y_test)
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False)
    test_loader = DataLoader(test_ds, batch_size=BATCH_SIZE, shuffle=False)

    torch.manual_seed(SEED)
    np.random.seed(SEED)
    model = FusedModel(n_structured=X_train.shape[1]).to(device)

    n_pos = int(y_train.sum())
    n_neg = int(len(y_train) - n_pos)
    pos_weight = torch.tensor([n_neg / max(n_pos, 1)], dtype=torch.float32, device=device)
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR)

    best_val_f1 = -1.0
    best_epoch = None
    best_state = None
    epoch_log = []
    for epoch in range(epochs):
        model.train()
        t0 = time.time()
        running_loss = 0.0
        for batch in train_loader:
            optimizer.zero_grad()
            logits = model(
                batch["input_ids"].to(device),
                batch["attention_mask"].to(device),
                batch["structured"].to(device),
            )
            loss = criterion(logits, batch["label"].to(device))
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * len(batch["label"])
        epoch_time = time.time() - t0
        val_metrics = _evaluate(model, val_loader, device)
        print(f"    [{arm}] epoch {epoch}: {epoch_time:.1f}s "
              f"train_loss={running_loss / len(train_ds):.4f} val_f1={val_metrics['f1']:.4f}")
        epoch_log.append({"epoch": epoch, "seconds": epoch_time,
                           "train_loss": running_loss / len(train_ds), "val_metrics": val_metrics})
        if val_metrics["f1"] > best_val_f1:
            best_val_f1 = val_metrics["f1"]
            best_epoch = epoch
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}

    if subsample:
        print(f"  [{arm}] --subsample set: sanity check only, not saving checkpoint or "
              f"evaluating on test.")
        return {"arm": arm, "subsample_only": True, "epoch_log": epoch_log}

    model.load_state_dict(best_state)
    model.eval()
    test_metrics = _evaluate(model, test_loader, device)
    print(f"  [{arm}] best val F1={best_val_f1:.4f} (epoch {best_epoch}) -> "
          f"test F1={test_metrics['f1']:.4f}, test PR-AUC={test_metrics['pr_auc']:.4f}")

    MODELS_DIR.mkdir(exist_ok=True)
    torch.save(best_state, MODELS_DIR / f"stage9_ablation_{arm}_seed{SEED}.pt")
    joblib.dump(scaler, MODELS_DIR / f"stage9_ablation_{arm}_scaler_seed{SEED}.joblib")
    joblib.dump(
        {"feature_names": names, "feature_groups": groups, "n_structured": X_train.shape[1],
         "max_length": MAX_LENGTH, "bert_model": BERT_NAME, "arm_excluded": arm},
        MODELS_DIR / f"stage9_ablation_{arm}_feature_meta_seed{SEED}.joblib",
    )

    return {
        "arm": arm, "best_epoch": best_epoch, "best_val_f1": best_val_f1,
        "n_structured": X_train.shape[1], "test_metrics": test_metrics, "epoch_log": epoch_log,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epochs", type=int, default=EPOCHS)
    parser.add_argument("--subsample", type=int, default=None,
                         help="Sanity-check only: train/eval all 5 arms on a small "
                              "subsample. Does not save checkpoints or write results.json.")
    args = parser.parse_args()

    if not Path(SPLIT_CSV).exists():
        print(f"ERROR: {SPLIT_CSV} not found.", file=sys.stderr)
        sys.exit(1)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    if device.type != "cuda":
        print("WARNING: no CUDA device -- this will be very slow.", file=sys.stderr)

    df = pd.read_csv(SPLIT_CSV)
    train = df[df["split"] == "train"].reset_index(drop=True)
    val = df[df["split"] == "val"].reset_index(drop=True)
    test = df[df["split"] == "test"].reset_index(drop=True)

    if args.subsample:
        train = train.sample(n=min(args.subsample, len(train)), random_state=SEED).reset_index(drop=True)
        val = val.sample(n=min(max(args.subsample // 4, 20), len(val)), random_state=SEED).reset_index(drop=True)
        test = test.sample(n=min(max(args.subsample // 4, 20), len(test)), random_state=SEED).reset_index(drop=True)
        print(f"--subsample {args.subsample}: SANITY-CHECK RUN ONLY, not a result.")

    print(f"train: {len(train)} rows, val: {len(val)} rows, test: {len(test)} rows")

    full_seed0 = None
    if not args.subsample:
        if not FULL_MODEL_RESULTS_PATH.exists():
            print(f"ERROR: {FULL_MODEL_RESULTS_PATH} not found -- run "
                  f"stage9_test_eval.py first (ablation compares against its seed-0 "
                  f"result, Decision 4).", file=sys.stderr)
            sys.exit(1)
        with open(FULL_MODEL_RESULTS_PATH) as f:
            full_results = json.load(f)
        full_seed0 = full_results["main_model"]["per_seed"][0]
        print(f"Full model (seed 0, test) reference: F1={full_seed0['f1']:.4f} "
              f"PR-AUC={full_seed0['pr_auc']:.4f}")

    results = {"full_model_seed0_test": full_seed0, "arms": {}}
    if not args.subsample and RESULTS_PATH.exists():
        with open(RESULTS_PATH) as f:
            results = json.load(f)
        done = list(results.get("arms", {}).keys())
        if done:
            print(f"Resuming -- arms already done: {done}")
        results["full_model_seed0_test"] = full_seed0  # keep in sync with the freshly
        # re-read reference on every resume, so a stale value is never silently carried
        # forward across runs

    for arm in ARMS:
        if not args.subsample and arm in results.get("arms", {}):
            print(f"\n=== {arm}: already done, skipping ===")
            continue
        print(f"\n=== Ablation arm: {arm} ===")
        t0 = time.time()
        arm_result = train_one_arm(arm, train, val, test, device, args.epochs, bool(args.subsample))
        if args.subsample:
            print(f"  [{arm}] subsample sanity check finished in {time.time() - t0:.1f}s, no errors.")
            continue
        arm_result["delta_vs_full_seed0"] = {
            "f1": arm_result["test_metrics"]["f1"] - full_seed0["f1"],
            "pr_auc": arm_result["test_metrics"]["pr_auc"] - full_seed0["pr_auc"],
        }
        results["arms"][arm] = arm_result
        with open(RESULTS_PATH, "w") as f:
            json.dump(results, f, indent=2)
        print(f"  [{arm}] total {time.time() - t0:.1f}s. Written: {RESULTS_PATH}")

    if args.subsample:
        print("\nSanity check complete for all 5 arms -- no shape/column errors. "
              "Safe to run the real --epochs 5 pass now.")
        return

    print("\n" + "=" * 70)
    print("ABLATION SUMMARY (test, 1 seed/arm, vs full model seed 0)")
    print("=" * 70)
    print(f"{'Full model (seed 0)':28s} F1={full_seed0['f1']:.4f}  PR-AUC={full_seed0['pr_auc']:.4f}")
    for arm in ARMS:
        if arm not in results["arms"]:
            print(f"{'- ' + arm:28s} NOT YET RUN")
            continue
        r = results["arms"][arm]
        d = r["delta_vs_full_seed0"]
        print(f"{'- ' + arm:28s} F1={r['test_metrics']['f1']:.4f} ({d['f1']:+.4f})  "
              f"PR-AUC={r['test_metrics']['pr_auc']:.4f} ({d['pr_auc']:+.4f})")


if __name__ == "__main__":
    main()
