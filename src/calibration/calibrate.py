"""
Stage 6 — Calibration (O4): Platt vs. isotonic, chosen on validation
========================================================================
An Explainable Credibility Scoring Framework for Online Recruitment Posts
O.K. Samarasinghe — COBSCCOMP242P-069

PURPOSE
    The DistilBERT+evidence model (Stage 5) outputs a probability, but nothing about how
    it was trained (cross-entropy loss) guarantees that probability is well-calibrated --
    a 0.70 output has no guarantee of meaning "70% likely fraudulent" until this stage
    checks and, if needed, corrects it. This script fits two standard calibrators (Platt
    scaling, isotonic regression) on validation, measures which one actually improves
    calibration (Brier score, Expected Calibration Error, reliability curve), and saves
    whichever one wins -- or neither, if the raw output is already calibrated enough that
    adding one would just add variance for no benefit. The 0-100 `credibility_score` Stage
    8's API returns is this calibrated probability x 100, not the raw model output.

WHICH MODEL GETS CALIBRATED
    Seed 0 of the DistilBERT+evidence model (models/distilbert_fused_state_dict_seed0.pt),
    matching the "seed 0 is the canonical saved model" convention already used in
    train_baseline.py and train_distilbert.py for exactly this reason -- Stage 8's API
    needs ONE fixed model to load, and seed 0 was arbitrarily designated that one from the
    start. The baseline models are NOT calibrated here: they're the O2 comparison point,
    not part of the deployed artefact.

WHAT THIS DOES NOT DO
    - Does not touch the test split. Calibrators are fit AND evaluated on validation only
      (guardrail: "hyperparameters/threshold/calibrator on validation only, test used
      once"). This means the Brier/ECE numbers below are a VALIDATION-set estimate, used to
      choose between Platt/isotonic/none -- the unbiased, citable Brier/ECE number comes
      from Stage 9's one-time test evaluation, applying whichever calibrator this script
      chose, without re-choosing it.
    - Does not re-tune the model. The DistilBERT+evidence seed-0 checkpoint from Stage 5 is
      loaded exactly as saved and only used for inference (forward pass, no gradient).

METHOD
    - Platt scaling: fit a single-feature LogisticRegression on the model's raw PRE-SIGMOID
      LOGIT (not the post-sigmoid probability -- this is Platt's original formulation) to
      predict the true label, producing a recalibrated probability via that logistic fit.
    - Isotonic regression: fit sklearn's IsotonicRegression (monotonic, non-parametric) on
      the raw POST-SIGMOID PROBABILITY to predict the true label.
    - Both are standard scikit-learn calibration methods (matches sklearn.calibration's own
      'sigmoid' and 'isotonic' options) implemented directly here (not via
      CalibratedClassifierCV) because that class expects to refit a classifier, and ours is
      already trained -- fitting the calibrators directly on saved logits/probabilities is
      simpler and avoids reloading the model inside sklearn's wrapper.
    - Selection criterion: lower Expected Calibration Error (ECE) on validation wins --
      chosen over Brier as the PRIMARY criterion because ECE directly measures "how far is
      a stated probability from the true frequency," which is exactly what Chapter 3's
      "0-100 score should mean X% probability" claim depends on. Brier is reported
      alongside as a secondary check (it blends calibration and sharpness, so it's a
      slightly different question). If ECE and Brier disagree about which calibrator is
      best, both are reported and the disagreement is noted, not hidden. "None" (the raw,
      uncalibrated probability) wins if it already has the lowest ECE -- calibration is not
      assumed to help, only applied if it measurably does.

OUTPUT
    - reports/stage6_calibration_results.json -- Brier/ECE before and after each
      calibrator, which one was selected and why, reliability-curve bin data for all three
      (raw/Platt/isotonic), and provisional risk-band thresholds.
    - reports/stage6_reliability_curve.png -- the reliability diagram, if matplotlib is
      available (skipped, not fatal, if it isn't).
    - models/stage6_calibrator.joblib -- the WINNING calibrator only (or nothing, if "none"
      won), for Stage 8's API to load and apply to the raw model output at inference time.

RISK BANDS (provisional)
    Simple terciles on the CALIBRATED 0-100 score (Low 0-33, Medium 34-66, High 67-100).
    Logged here as provisional because `PROJECT_PLAN.md` already records "success
    thresholds per objective" as an open item pending supervisor input -- these bands are a
    reasonable placeholder, not a value validated against any external standard, and
    Chapter 5 should say so if they haven't been revisited by submission.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss

try:
    from src.models.train_baseline import TEXT_COLS, _build_text
    from src.models.train_distilbert import (
        BERT_NAME, FusedModel, SPLIT_CSV, build_structured_features,
    )
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from src.models.train_baseline import TEXT_COLS, _build_text  # noqa: E402
    from src.models.train_distilbert import (  # noqa: E402
        BERT_NAME, FusedModel, SPLIT_CSV, build_structured_features,
    )
from src.features.extract_features import extract_all

MODELS_DIR = Path("models")
REPORTS_DIR = Path("reports")
SEED = 0  # canonical model, matches train_baseline.py / train_distilbert.py convention
N_BINS = 10  # standard ECE bin count


def _expected_calibration_error(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = N_BINS) -> float:
    """Standard equal-width-bin ECE: sum over bins of (bin size / N) * |bin accuracy -
    bin mean confidence|. A direct, unweighted implementation (not sklearn's
    calibration_curve, which drops empty bins silently) so every bin's absence or presence
    is explicit and auditable."""
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
def _get_val_logits_and_labels(seed: int = SEED, split_csv: str = SPLIT_CSV, batch_size: int = 32):
    import joblib
    from transformers import DistilBertTokenizerFast

    df = pd.read_csv(split_csv)
    val = df[df["split"] == "val"].reset_index(drop=True)
    y_val = val["fraudulent"].astype(int).values

    meta = joblib.load(MODELS_DIR / f"distilbert_structured_feature_meta_seed{seed}.joblib")
    scaler = joblib.load(MODELS_DIR / f"distilbert_structured_scaler_seed{seed}.joblib")

    val_feat = extract_all(val)
    X_val_struct, feature_names, _ = build_structured_features(val_feat)
    if feature_names != meta["feature_names"]:
        raise RuntimeError(
            "Structured feature names/order don't match the saved model's metadata -- "
            "extract_features.py or train_distilbert.py may have changed since Stage 5 "
            "ran. Re-run Stage 5 before calibrating, don't silently proceed."
        )
    X_val_struct = scaler.transform(X_val_struct).astype(np.float32)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = DistilBertTokenizerFast.from_pretrained(BERT_NAME)
    val_text = _build_text(val).tolist()
    enc = tokenizer(val_text, truncation=True, padding=True, max_length=meta["max_length"], return_tensors="pt")

    model = FusedModel(n_structured=meta["n_structured"]).to(device)
    state_dict = torch.load(
        MODELS_DIR / f"distilbert_fused_state_dict_seed{seed}.pt", map_location=device
    )
    model.load_state_dict(state_dict)
    model.eval()

    structured_t = torch.tensor(X_val_struct, dtype=torch.float32)
    n = len(val)
    logits_all = []
    for start in range(0, n, batch_size):
        end = min(start + batch_size, n)
        logits = model(
            enc["input_ids"][start:end].to(device),
            enc["attention_mask"][start:end].to(device),
            structured_t[start:end].to(device),
        )
        logits_all.append(logits.cpu().numpy())
    logits = np.concatenate(logits_all)
    return logits, y_val


def run():
    if not (MODELS_DIR / f"distilbert_fused_state_dict_seed{SEED}.pt").exists():
        print(
            f"ERROR: models/distilbert_fused_state_dict_seed{SEED}.pt not found. "
            f"Run Stage 5 (src.models.train_distilbert --epochs 5 --seed {SEED}) first.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Running seed-{SEED} model inference on validation set ...")
    logits, y_val = _get_val_logits_and_labels(seed=SEED)
    raw_prob = 1 / (1 + np.exp(-logits))
    print(f"val: {len(y_val)} rows ({y_val.sum()} fraud)")

    # --- Platt scaling: fit on the raw LOGIT, not the probability ---
    platt = LogisticRegression()
    platt.fit(logits.reshape(-1, 1), y_val)
    platt_prob = platt.predict_proba(logits.reshape(-1, 1))[:, 1]

    # --- Isotonic regression: fit on the raw PROBABILITY ---
    isotonic = IsotonicRegression(out_of_bounds="clip")
    isotonic.fit(raw_prob, y_val)
    isotonic_prob = isotonic.transform(raw_prob)

    candidates = {"none": raw_prob, "platt": platt_prob, "isotonic": isotonic_prob}
    metrics = {}
    for name, probs in candidates.items():
        metrics[name] = {
            "brier": float(brier_score_loss(y_val, probs)),
            "ece": _expected_calibration_error(y_val, probs),
        }
        print(f"{name}: brier={metrics[name]['brier']:.4f}, ece={metrics[name]['ece']:.4f}")

    selected = min(metrics, key=lambda k: metrics[k]["ece"])
    print(f"\nSelected calibrator: {selected} (lowest ECE on validation)")
    if min(metrics, key=lambda k: metrics[k]["brier"]) != selected:
        print(
            f"NOTE: Brier score's own pick ({min(metrics, key=lambda k: metrics[k]['brier'])}) "
            f"disagrees with the ECE-based pick ({selected}) -- both are reported in the "
            f"JSON; the discrepancy is worth a sentence in Chapter 4, not silently dropped."
        )

    MODELS_DIR.mkdir(exist_ok=True)
    if selected == "platt":
        import joblib
        joblib.dump(platt, MODELS_DIR / "stage6_calibrator.joblib")
        print(f"Saved Platt calibrator to {MODELS_DIR}/stage6_calibrator.joblib")
    elif selected == "isotonic":
        import joblib
        joblib.dump(isotonic, MODELS_DIR / "stage6_calibrator.joblib")
        print(f"Saved isotonic calibrator to {MODELS_DIR}/stage6_calibrator.joblib")
    else:
        print("No calibrator saved -- raw model output already had the lowest ECE.")

    final_prob = candidates[selected]
    scores_0_100 = final_prob * 100
    risk_bands = {
        "low": [0, 33], "medium": [34, 66], "high": [67, 100],
        "note": "Provisional terciles, not validated against an external standard -- "
                "PROJECT_PLAN.md already logs success thresholds as open pending "
                "supervisor input.",
    }

    summary = {
        "seed": SEED,
        "n_val": len(y_val),
        "metrics": metrics,
        "selected_calibrator": selected,
        "selection_criterion": "lowest ECE on validation (Brier reported as secondary check)",
        "reliability_bins": {name: _reliability_bins(y_val, probs) for name, probs in candidates.items()},
        "risk_bands_0_100": risk_bands,
        "calibrated_score_summary": {
            "mean": float(scores_0_100.mean()), "min": float(scores_0_100.min()),
            "max": float(scores_0_100.max()),
        },
    }
    REPORTS_DIR.mkdir(exist_ok=True)
    out_path = REPORTS_DIR / "stage6_calibration_results.json"
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nWritten: {out_path}")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(6, 6))
        ax.plot([0, 1], [0, 1], "k--", label="Perfect calibration")
        for name, probs in candidates.items():
            bins = _reliability_bins(y_val, probs)
            xs = [b["mean_confidence"] for b in bins if b["mean_confidence"] is not None]
            ys = [b["fraction_positive"] for b in bins if b["fraction_positive"] is not None]
            ax.plot(xs, ys, marker="o", label=f"{name} (ECE={metrics[name]['ece']:.3f})")
        ax.set_xlabel("Mean predicted probability")
        ax.set_ylabel("Fraction positive (actual)")
        ax.set_title("Reliability curve — validation set")
        ax.legend()
        fig.tight_layout()
        fig.savefig(REPORTS_DIR / "stage6_reliability_curve.png", dpi=150)
        print(f"Written: {REPORTS_DIR}/stage6_reliability_curve.png")
    except ImportError:
        print("matplotlib not installed -- skipped the reliability-curve plot (metrics/bin data still in the JSON).")


if __name__ == "__main__":
    run()
