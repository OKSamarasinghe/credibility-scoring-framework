"""
Stage 9 — Part 3: Tier 2 transfer (T1/T2/T3) + source-probe leakage test
===========================================================================
An Explainable Credibility Scoring Framework for Online Recruitment Posts
O.K. Samarasinghe — COBSCCOMP242P-069

PURPOSE
    The last piece of Stage 9. Four experiments against the full 154-posting Tier 2 set
    (24 fraud, 130 legit) -- see decisions.md, 2026-10-08, "Stage 9, Part 3 design
    decisions" (4 entries) for what each one means and why it's built this way. All of it
    is fast (minutes, not the ablation's ~2.25 hours) -- T1/T2 are pure inference with
    models already trained, T3 fine-tunes briefly on ~77 rows, the leakage probe is a
    small LogisticRegression.

T1 -- temporal transfer
    The 3 existing main-model checkpoints (seeds 0/1/2, no retraining) evaluated on all
    154 Tier 2 postings. Same 3-seed treatment the main model got on EMSCAD test
    (Decision 3, Stage 9 Part 1) -- parity, and it's cheap since this is inference only.

T2 -- signal durability
    The 5 ablation checkpoints already trained for the EMSCAD-side ablation (NOT retrained
    here) evaluated on the same 154 Tier 2 postings. Compares each category's Δ-vs-full-
    model on Tier 2 against its Δ on EMSCAD test -- does a category's importance look the
    same on 2026 postings as it did on 2012-2014 ones?

T3 -- domain adaptation
    Tier 2 split 50/50, stratified by fraudulent (fixed seed) -- any smaller split leaves
    too few fraud examples per portion to mean anything. The frozen seed-0 EMSCAD
    checkpoint is evaluated zero-shot on the eval half FIRST, then fine-tuned for 3 epochs
    (pre-committed, NOT validated against anything -- disclosed, not hidden) on the other
    half, then evaluated again on the same eval half. The reported "fine-tuned" result is
    the state after all 3 epochs, not a best-epoch selection.

Source-probe leakage test
    A class-weighted LogisticRegression trying to tell EMSCAD rows from Tier 2 rows using
    the SAME 46 structured E1-E4 features the fraud model uses (not text -- EMSCAD's text
    is anonymised, Tier 2's isn't, so text would trivially and uninterestingly leak
    source). EMSCAD TRAIN split (test untouched) + all 154 Tier 2 rows, stratified 80/20
    probe split. Reported as ROC-AUC and balanced accuracy, not raw accuracy -- the
    combined set is ~98.8% EMSCAD, so raw accuracy would be high and meaningless.

USAGE
    python -m src.evaluation.stage9_tier2_and_leakage

OUTPUT
    reports/stage9_tier2_and_leakage_results.json
    models/stage9_t3_finetuned_seed0.pt -- the T3 fine-tuned checkpoint, for reference.
"""
import json
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader

try:
    from src.models.train_baseline import _build_text
    from src.models.train_distilbert import (
        FusedDataset, FusedModel, build_structured_features, _evaluate,
    )
    from src.features.extract_features import extract_all
    from src.api.stage8b_select import TIER2_FRAUD, TIER2_LEGIT, _load_jsonl, record_to_request
    from src.api import pipeline as api_pipeline
    from src.evaluation.stage9_ablation import ARMS as ABLATION_ARMS, build_ablation_features
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from src.models.train_baseline import _build_text  # noqa: E402
    from src.models.train_distilbert import (  # noqa: E402
        FusedDataset, FusedModel, build_structured_features, _evaluate,
    )
    from src.features.extract_features import extract_all  # noqa: E402
    from src.api.stage8b_select import (  # noqa: E402
        TIER2_FRAUD, TIER2_LEGIT, _load_jsonl, record_to_request,
    )
    from src.api import pipeline as api_pipeline  # noqa: E402
    from src.evaluation.stage9_ablation import ARMS as ABLATION_ARMS, build_ablation_features  # noqa: E402

SPLIT_CSV = "data/interim/stage3_split.csv"
MODELS_DIR = Path("models")
REPORTS_DIR = Path("reports")
OUT_PATH = REPORTS_DIR / "stage9_tier2_and_leakage_results.json"

MAIN_SEEDS = [0, 1, 2]
T3_SEED = 0
T3_EPOCHS = 3
T3_BATCH_SIZE = 16
T3_LR = 2e-5
PROBE_SEED = 0


def _mean_sd(per_seed: list) -> dict:
    keys = per_seed[0].keys()
    out = {}
    for k in keys:
        vals = np.array([m[k] for m in per_seed])
        out[k] = {"mean": float(vals.mean()), "sd": float(vals.std(ddof=1)) if len(vals) > 1 else 0.0}
    return out


def build_tier2_df() -> pd.DataFrame:
    """Reuses the exact Stage 8b per-row pipeline (record_to_request + build_posting_row)
    so Tier 2 gets identical Stage-1-shaped preprocessing to what EMSCAD rows get -- not a
    second, possibly-inconsistent loader."""
    rows = []
    for src_path, source_name in [(TIER2_FRAUD, "fraud"), (TIER2_LEGIT, "legit")]:
        for i, row in enumerate(_load_jsonl(src_path)):
            req = record_to_request(row)
            df_row = api_pipeline.build_posting_row(req)
            df_row["fraudulent"] = int(row["fraudulent"])
            df_row["_source_file"] = source_name
            df_row["_source_index"] = i
            rows.append(df_row)
    return pd.concat(rows, ignore_index=True)


@torch.no_grad()
def _eval_main_seed(seed: int, eval_df: pd.DataFrame, eval_feat: pd.DataFrame, device) -> dict:
    scaler = joblib.load(MODELS_DIR / f"distilbert_structured_scaler_seed{seed}.joblib")
    meta = joblib.load(MODELS_DIR / f"distilbert_structured_feature_meta_seed{seed}.joblib")
    X, names, _groups = build_structured_features(eval_feat)
    if names != meta["feature_names"]:
        raise RuntimeError(f"seed {seed}: feature name/order mismatch vs training meta")
    X = scaler.transform(X).astype(np.float32)

    from transformers import DistilBertTokenizerFast
    tok = DistilBertTokenizerFast.from_pretrained(meta["bert_model"])
    text = _build_text(eval_df).tolist()
    enc = tok(text, truncation=True, padding=True, max_length=meta["max_length"], return_tensors="pt")
    y = eval_df["fraudulent"].astype(int).values
    ds = FusedDataset(enc, X, y)
    loader = DataLoader(ds, batch_size=16, shuffle=False)

    model = FusedModel(n_structured=meta["n_structured"]).to(device)
    model.load_state_dict(
        torch.load(MODELS_DIR / f"distilbert_fused_state_dict_seed{seed}.pt", map_location=device)
    )
    model.eval()
    return _evaluate(model, loader, device)


@torch.no_grad()
def _eval_ablation_arm(arm: str, eval_df: pd.DataFrame, eval_feat: pd.DataFrame, device) -> dict:
    scaler = joblib.load(MODELS_DIR / f"stage9_ablation_{arm}_scaler_seed0.joblib")
    meta = joblib.load(MODELS_DIR / f"stage9_ablation_{arm}_feature_meta_seed0.joblib")
    X, names, _groups = build_ablation_features(eval_feat, arm)
    if names != meta["feature_names"]:
        raise RuntimeError(f"arm {arm}: feature name/order mismatch vs training meta")
    X = scaler.transform(X).astype(np.float32)

    from transformers import DistilBertTokenizerFast
    tok = DistilBertTokenizerFast.from_pretrained(meta["bert_model"])
    text = _build_text(eval_df).tolist()
    enc = tok(text, truncation=True, padding=True, max_length=meta["max_length"], return_tensors="pt")
    y = eval_df["fraudulent"].astype(int).values
    ds = FusedDataset(enc, X, y)
    loader = DataLoader(ds, batch_size=16, shuffle=False)

    model = FusedModel(n_structured=meta["n_structured"]).to(device)
    model.load_state_dict(
        torch.load(MODELS_DIR / f"stage9_ablation_{arm}_seed0.pt", map_location=device)
    )
    model.eval()
    return _evaluate(model, loader, device)


def run_t1(tier2_df, tier2_feat, device) -> dict:
    print("\n=== T1: temporal transfer (3 seeds, EMSCAD-trained model on Tier 2) ===")
    results = []
    for seed in MAIN_SEEDS:
        t0 = time.time()
        m = _eval_main_seed(seed, tier2_df, tier2_feat, device)
        results.append(m)
        print(f"  seed {seed}: {time.time() - t0:.1f}s -- f1={m['f1']:.4f} pr_auc={m['pr_auc']:.4f}")
    return {"per_seed": results, "mean_sd": _mean_sd(results)}


def run_t2(tier2_df, tier2_feat, device, full_seed0_tier2: dict) -> dict:
    print("\n=== T2: signal durability (5 ablation arms, reused checkpoints, on Tier 2) ===")
    results = {}
    for arm in ABLATION_ARMS:
        t0 = time.time()
        m = _eval_ablation_arm(arm, tier2_df, tier2_feat, device)
        delta = {"f1": m["f1"] - full_seed0_tier2["f1"], "pr_auc": m["pr_auc"] - full_seed0_tier2["pr_auc"]}
        results[arm] = {"test_metrics": m, "delta_vs_full_seed0_tier2": delta}
        print(f"  {arm}: {time.time() - t0:.1f}s -- f1={m['f1']:.4f} (d{delta['f1']:+.4f})  "
              f"pr_auc={m['pr_auc']:.4f} (d{delta['pr_auc']:+.4f})")
    return results


def run_t3(tier2_df, device) -> dict:
    print("\n=== T3: domain adaptation (50/50 stratified split, fine-tune 3 epochs) ===")
    idx = np.arange(len(tier2_df))
    y_all = tier2_df["fraudulent"].astype(int).values
    ft_idx, eval_idx = train_test_split(idx, test_size=0.5, stratify=y_all, random_state=T3_SEED)
    ft_df = tier2_df.iloc[ft_idx].reset_index(drop=True)
    eval_df = tier2_df.iloc[eval_idx].reset_index(drop=True)
    print(f"  fine-tune portion: {len(ft_df)} rows ({int(ft_df['fraudulent'].sum())} fraud)")
    print(f"  eval portion:      {len(eval_df)} rows ({int(eval_df['fraudulent'].sum())} fraud)")

    ft_feat = extract_all(ft_df)
    eval_feat = extract_all(eval_df)

    print("  zero-shot (no fine-tuning) on eval portion ...")
    zero_shot = _eval_main_seed(0, eval_df, eval_feat, device)
    print(f"    zero-shot: f1={zero_shot['f1']:.4f} pr_auc={zero_shot['pr_auc']:.4f}")

    scaler = joblib.load(MODELS_DIR / "distilbert_structured_scaler_seed0.joblib")
    meta = joblib.load(MODELS_DIR / "distilbert_structured_feature_meta_seed0.joblib")

    X_ft, names, _groups = build_structured_features(ft_feat)
    if names != meta["feature_names"]:
        raise RuntimeError("T3: feature name/order mismatch vs seed-0 training meta")
    X_ft = scaler.transform(X_ft).astype(np.float32)
    X_eval, names_eval, _ = build_structured_features(eval_feat)
    if names_eval != meta["feature_names"]:
        raise RuntimeError("T3: feature name/order mismatch (eval portion) vs seed-0 training meta")
    X_eval = scaler.transform(X_eval).astype(np.float32)

    from transformers import DistilBertTokenizerFast
    tok = DistilBertTokenizerFast.from_pretrained(meta["bert_model"])
    ft_text = _build_text(ft_df).tolist()
    eval_text = _build_text(eval_df).tolist()
    ft_enc = tok(ft_text, truncation=True, padding=True, max_length=meta["max_length"], return_tensors="pt")
    eval_enc = tok(eval_text, truncation=True, padding=True, max_length=meta["max_length"], return_tensors="pt")

    y_ft = ft_df["fraudulent"].astype(int).values
    y_eval = eval_df["fraudulent"].astype(int).values
    ft_ds = FusedDataset(ft_enc, X_ft, y_ft)
    eval_ds = FusedDataset(eval_enc, X_eval, y_eval)
    ft_loader = DataLoader(ft_ds, batch_size=T3_BATCH_SIZE, shuffle=True)
    eval_loader = DataLoader(eval_ds, batch_size=T3_BATCH_SIZE, shuffle=False)

    torch.manual_seed(T3_SEED)
    np.random.seed(T3_SEED)
    model = FusedModel(n_structured=meta["n_structured"]).to(device)
    model.load_state_dict(
        torch.load(MODELS_DIR / "distilbert_fused_state_dict_seed0.pt", map_location=device)
    )

    n_pos = int(y_ft.sum())
    n_neg = int(len(y_ft) - n_pos)
    pos_weight = torch.tensor([n_neg / max(n_pos, 1)], dtype=torch.float32, device=device)
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    optimizer = torch.optim.AdamW(model.parameters(), lr=T3_LR)

    epoch_log = []
    for epoch in range(T3_EPOCHS):
        model.train()
        t0 = time.time()
        running_loss = 0.0
        for batch in ft_loader:
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
        eval_metrics = _evaluate(model, eval_loader, device)
        print(f"    epoch {epoch}: {time.time() - t0:.1f}s train_loss={running_loss / len(ft_ds):.4f} "
              f"eval_f1={eval_metrics['f1']:.4f}")
        epoch_log.append({"epoch": epoch, "train_loss": running_loss / len(ft_ds), "eval_metrics": eval_metrics})

    fine_tuned = epoch_log[-1]["eval_metrics"]  # state after all T3_EPOCHS epochs -- not a
    # best-epoch selection, this is literally the final epoch's number
    print(f"  fine-tuned (after {T3_EPOCHS} epochs): f1={fine_tuned['f1']:.4f} pr_auc={fine_tuned['pr_auc']:.4f}")

    MODELS_DIR.mkdir(exist_ok=True)
    torch.save(model.state_dict(), MODELS_DIR / "stage9_t3_finetuned_seed0.pt")

    return {
        "n_finetune": len(ft_df), "n_finetune_fraud": int(ft_df["fraudulent"].sum()),
        "n_eval": len(eval_df), "n_eval_fraud": int(eval_df["fraudulent"].sum()),
        "epochs": T3_EPOCHS,
        "zero_shot": zero_shot,
        "fine_tuned": fine_tuned,
        "delta_from_finetuning": {
            "f1": fine_tuned["f1"] - zero_shot["f1"],
            "pr_auc": fine_tuned["pr_auc"] - zero_shot["pr_auc"],
        },
        "epoch_log": epoch_log,
    }


def run_source_probe(tier2_feat: pd.DataFrame, train_split_df: pd.DataFrame) -> dict:
    print("\n=== Source-probe leakage test ===")
    print("  computing E1-E4 structured features for EMSCAD train split (12,516 rows) ...")
    emscad_feat = extract_all(train_split_df)
    X_emscad, names_e, _ = build_structured_features(emscad_feat)
    X_tier2, names_t, _ = build_structured_features(tier2_feat)
    if names_e != names_t:
        raise RuntimeError("source-probe: feature name/order mismatch between EMSCAD and Tier 2")

    X = np.vstack([X_emscad, X_tier2])
    y = np.array([0] * len(X_emscad) + [1] * len(X_tier2))  # 0=EMSCAD, 1=Tier2
    print(f"  combined: {len(X)} rows ({int(y.sum())} Tier 2 / {len(X) - int(y.sum())} EMSCAD)")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=PROBE_SEED
    )
    probe = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=PROBE_SEED)
    probe.fit(X_train, y_train)
    proba = probe.predict_proba(X_test)[:, 1]
    pred = (proba >= 0.5).astype(int)
    roc_auc = roc_auc_score(y_test, proba)
    bal_acc = balanced_accuracy_score(y_test, pred)
    print(f"  probe test ROC-AUC={roc_auc:.4f}  balanced_accuracy={bal_acc:.4f}")

    return {
        "n_total": len(X), "n_emscad": int(len(X_emscad)), "n_tier2": int(len(X_tier2)),
        "n_probe_test": len(X_test),
        "probe_test_roc_auc": float(roc_auc),
        "probe_test_balanced_accuracy": float(bal_acc),
    }


def main():
    if not Path(SPLIT_CSV).exists():
        print(f"ERROR: {SPLIT_CSV} not found.", file=sys.stderr)
        sys.exit(1)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    print("Building Tier 2 DataFrame (154 postings via the same pipeline Stage 8b uses) ...")
    tier2_df = build_tier2_df()
    print(f"  {len(tier2_df)} rows ({int(tier2_df['fraudulent'].sum())} fraud)")
    print("  computing E1-E4 structured features for the full Tier 2 set ...")
    tier2_feat = extract_all(tier2_df)

    t1 = run_t1(tier2_df, tier2_feat, device)
    full_seed0_tier2 = t1["per_seed"][0]  # seed 0 is first in MAIN_SEEDS

    t2 = run_t2(tier2_df, tier2_feat, device, full_seed0_tier2)
    t3 = run_t3(tier2_df, device)

    split_df = pd.read_csv(SPLIT_CSV)
    train_split_df = split_df[split_df["split"] == "train"].reset_index(drop=True)
    probe = run_source_probe(tier2_feat, train_split_df)

    summary = {
        "n_tier2": len(tier2_df), "n_tier2_fraud": int(tier2_df["fraudulent"].sum()),
        "T1_temporal_transfer": t1,
        "T2_signal_durability": t2,
        "T3_domain_adaptation": t3,
        "source_probe_leakage": probe,
    }
    REPORTS_DIR.mkdir(exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 70)
    print("STAGE 9 PART 3 SUMMARY")
    print("=" * 70)
    ms = t1["mean_sd"]
    print(f"T1 Tier 2 (3 seeds):  F1={ms['f1']['mean']:.4f}+/-{ms['f1']['sd']:.4f}  "
          f"PR-AUC={ms['pr_auc']['mean']:.4f}+/-{ms['pr_auc']['sd']:.4f}")
    print(f"  (for comparison, EMSCAD test seed 0: F1=0.6449 PR-AUC=0.6881)")
    print("T2 (vs full model seed 0 on Tier 2):")
    for arm in ABLATION_ARMS:
        r = t2[arm]
        print(f"  - {arm:18s} F1={r['test_metrics']['f1']:.4f} (d{r['delta_vs_full_seed0_tier2']['f1']:+.4f})  "
              f"PR-AUC={r['test_metrics']['pr_auc']:.4f} (d{r['delta_vs_full_seed0_tier2']['pr_auc']:+.4f})")
    print(f"T3: zero-shot F1={t3['zero_shot']['f1']:.4f} -> fine-tuned F1={t3['fine_tuned']['f1']:.4f} "
          f"(d{t3['delta_from_finetuning']['f1']:+.4f})")
    print(f"Source-probe: ROC-AUC={probe['probe_test_roc_auc']:.4f}  "
          f"balanced_accuracy={probe['probe_test_balanced_accuracy']:.4f}")
    print(f"\nWritten: {OUT_PATH}")


if __name__ == "__main__":
    main()
