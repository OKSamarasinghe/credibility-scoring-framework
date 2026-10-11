"""
Stage 9 -- calibration test-set evaluation (O4): the one figure Stage 9's main pass
didn't compute.

PURPOSE
    methodology.md's Calibration (O4) section says explicitly: "the final, citable
    calibration result is whatever Stage 9 reports when this same frozen isotonic
    calibrator is applied once to the untouched test set." stage9_test_eval.py never
    computed it. This script closes that out -- nothing else.

WHY THIS DOES NOT VIOLATE "TEST USED ONCE" (decisions.md, 2026-10-08, Decision 2)
    Decision 2's own wording: "'used once' means the test labels are never used to
    make a further design, hyperparameter, threshold, or model-selection choice."
    This script changes none of those -- the calibrator was already selected and
    frozen on VALIDATION, before test was ever touched (Stage 6). This script loads
    it with .transform() only, never .fit(). No model architecture, feature set, seed,
    or ablation design is touched or could change as a result of this number.

WHAT THIS DOES NOT DO
    - Does not refit or reselect the calibrator (stage6_calibrator.joblib loaded as-is).
    - Does not retrain the seed-0 checkpoint (loaded exactly as Stage 5 produced it).
    - Does not touch validation.

USAGE
    python -m src.evaluation.stage9_calibration_eval
"""
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import brier_score_loss

try:
    from src.models.train_baseline import _build_text
    from src.models.train_distilbert import FusedModel, build_structured_features
    from src.features.extract_features import extract_all
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from src.models.train_baseline import _build_text  # noqa: E402
    from src.models.train_distilbert import FusedModel, build_structured_features  # noqa: E402
    from src.features.extract_features import extract_all  # noqa: E402

SPLIT_CSV = "data/interim/stage3_split.csv"
MODELS_DIR = Path("models")
REPORTS_DIR = Path("reports")
SEED = 0  # the calibrator was fit against the seed-0 model's output -- must match
N_BINS = 10


def _expected_calibration_error(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = N_BINS) -> float:
    """Identical to calibrate.py's own implementation -- same binning, same formula,
    so this number is directly comparable to the validation-side ECE already reported."""
    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    n = len(y_true)
    for lo, hi in zip(bin_edges[:-1], bin_edges[1:]):
        mask = (y_prob >= lo) & (y_prob < hi) if hi < 1.0 else (y_prob >= lo) & (y_prob <= hi)
        if mask.sum() == 0:
            continue
        bin_acc = y_true[mask].mean()
        bin_conf = y_prob[mask].mean()
        ece += (mask.sum() / n) * abs(bin_acc - bin_conf)
    return float(ece)


def _reliability_bins(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = N_BINS) -> list:
    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    bins = []
    for lo, hi in zip(bin_edges[:-1], bin_edges[1:]):
        mask = (y_prob >= lo) & (y_prob < hi) if hi < 1.0 else (y_prob >= lo) & (y_prob <= hi)
        bins.append({
            "bin_lo": float(lo), "bin_hi": float(hi), "n": int(mask.sum()),
            "mean_confidence": float(y_prob[mask].mean()) if mask.sum() else None,
            "fraction_positive": float(y_true[mask].mean()) if mask.sum() else None,
        })
    return bins


@torch.no_grad()
def main():
    if not Path(SPLIT_CSV).exists():
        print(f"ERROR: {SPLIT_CSV} not found.", file=sys.stderr)
        sys.exit(1)
    calibrator_path = MODELS_DIR / "stage6_calibrator.joblib"
    if not calibrator_path.exists():
        print(f"ERROR: {calibrator_path} not found -- run Stage 6 first.", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(SPLIT_CSV)
    test = df[df["split"] == "test"].reset_index(drop=True)
    y_test = test["fraudulent"].astype(int).values
    print(f"test: {len(test)} rows ({y_test.sum()} fraud) -- loading already-generated "
          f"split, not re-deriving it")

    meta = joblib.load(MODELS_DIR / f"distilbert_structured_feature_meta_seed{SEED}.joblib")
    scaler = joblib.load(MODELS_DIR / f"distilbert_structured_scaler_seed{SEED}.joblib")

    print("Computing E1-E4 structured features for test split (extract_all) ...")
    test_feat = extract_all(test)
    X_test_struct, names, _groups = build_structured_features(test_feat)
    if names != meta["feature_names"]:
        raise RuntimeError(
            "structured feature name/order mismatch vs. the saved training-time meta -- "
            "aborting rather than silently misaligning columns."
        )
    X_test_struct = scaler.transform(X_test_struct).astype(np.float32)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"device: {device}")

    from transformers import DistilBertTokenizerFast
    tokenizer = DistilBertTokenizerFast.from_pretrained(meta["bert_model"])
    test_text = _build_text(test).tolist()
    enc = tokenizer(
        test_text, truncation=True, padding=True, max_length=meta["max_length"], return_tensors="pt"
    )

    model = FusedModel(n_structured=meta["n_structured"]).to(device)
    state_dict = torch.load(
        MODELS_DIR / f"distilbert_fused_state_dict_seed{SEED}.pt", map_location=device
    )
    model.load_state_dict(state_dict)
    model.eval()

    batch_size = 32
    n = len(test)
    logits_all = []
    for start in range(0, n, batch_size):
        end = min(start + batch_size, n)
        logits = model(
            enc["input_ids"][start:end].to(device),
            enc["attention_mask"][start:end].to(device),
            torch.tensor(X_test_struct[start:end], dtype=torch.float32).to(device),
        )
        logits_all.append(logits.cpu().numpy())
    logits = np.concatenate(logits_all)
    raw_prob = 1 / (1 + np.exp(-logits))

    print("Applying the already-frozen isotonic calibrator (transform only, no fit) ...")
    calibrator = joblib.load(calibrator_path)
    calibrated_prob = calibrator.transform(raw_prob)

    brier = float(brier_score_loss(y_test, calibrated_prob))
    ece = _expected_calibration_error(y_test, calibrated_prob)
    print(f"\nTEST-SET calibration (seed {SEED}, n={n}): Brier={brier:.4f}  ECE={ece:.4f}")

    summary = {
        "seed": SEED,
        "n_test": n,
        "n_fraud_test": int(y_test.sum()),
        "calibrator": "isotonic (frozen from Stage 6, transform only -- not refit)",
        "metrics": {"brier": brier, "ece": ece},
        "reliability_bins": _reliability_bins(y_test, calibrated_prob),
        "note": (
            "This is the citable calibration result methodology.md's Calibration (O4) "
            "section pre-committed to: the frozen isotonic calibrator applied once to "
            "the untouched test set. Computed after the main Stage 9 test pass; see "
            "decisions.md entry logged alongside this run for why this does not reopen "
            "the 'test used once' guardrail (Decision 2, 2026-10-08)."
        ),
    }
    REPORTS_DIR.mkdir(exist_ok=True)
    out_path = REPORTS_DIR / "stage9_calibration_test_results.json"
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nWritten: {out_path}")


if __name__ == "__main__":
    main()
