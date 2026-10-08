"""
Stage 5 — Improved model (O3): DistilBERT fine-tuned + fused structured evidence (E1-E4)
===========================================================================================
An Explainable Credibility Scoring Framework for Online Recruitment Posts
O.K. Samarasinghe — COBSCCOMP242P-069

PURPOSE (today's run)
    ONE timed fine-tuning pass (Decision, decisions.md 2026-10-06, "Ablation seed count is
    conditional, decided on Day 3 from a real timing, not guessed now"). Default --epochs 1,
    one seed. The point of today's run is the number this script prints at the end --
    seconds/epoch and peak GPU memory -- which is what decides whether 3 seeds x 5 ablation
    arms (Stage 9) fits what's left of the week, or must drop to 1 seed per decisions.md's
    already-agreed fallback. That decision is made from this measurement, not guessed.

    Once the per-epoch cost is known, re-run with a higher --epochs to produce the actual
    Stage 5 improved-model result for methodology.md's O3 table. This script is written to
    serve both purposes (timing run today, real result later) rather than being thrown away
    after the timing is known.

WHAT THIS DOES NOT DO
    - Does not touch the test split (same guardrail as train_baseline.py). Validation only.
    - Does not retune the baseline's text scope, class-imbalance approach, or split. It
      imports `_build_text` and `TEXT_COLS` directly from `train_baseline.py` so both arms
      of the O2-vs-O3 comparison see IDENTICALLY constructed input text -- this removes one
      possible source of an uncontrolled difference between the two arms.
    - Does not decide the seed count or epoch budget for you. It prints the numbers; the
      decision is yours to make and log in decisions.md (template at the bottom of this
      file's final print statement).

ARCHITECTURE — "DistilBERT + structured evidence" (methodology.md's O3 table name)
    1. DistilBERT (distilbert-base-uncased) tokenizes and encodes the same text the
       baseline sees (title+description+requirements+benefits), truncated to --max-length
       tokens (default 256 -- a documented, not-tuned-against-performance choice; most
       EMSCAD postings are shorter than this, per the Stage 1 audit).
    2. The [CLS] token's final hidden state (768-dim) is concatenated with the structured
       evidence vector built from Stage 4's E1-E4 output (see STRUCTURED_FEATURE_GROUPS
       below), after StandardScaler scaling fit on TRAIN ONLY.
    3. A small MLP head (concat -> 128 -> 1 logit) sits on top. Fine-tuned end-to-end
       (Decision, decisions.md 2026-09-20: "fine-tune, not frozen").

STRUCTURED_FEATURE_GROUPS is the ablation unit
    Stage 9's leave-one-category-out ablation (decisions.md 2026-10-06, Decision 2: "E1,
    E2, E3, E4, has_company_logo -- 5 arms") removes exactly one of these named groups'
    columns at a time (zeroed out or dropped, the mechanism is Stage 9's to decide) and
    re-evaluates. Building the grouping into this script now, rather than retrofitting it
    at Stage 9, means the ablation arms call the same `build_structured_features()` with a
    group excluded, instead of a second, possibly-inconsistent feature-building path.

WHY E1 IS IN THE STRUCTURED VECTOR, EVEN THOUGH DISTILBERT ALREADY READS THE SAME TEXT
    E1 (suspicious-phrase lexicon hits) is computed FROM the same text DistilBERT reads
    directly -- so in principle DistilBERT could learn an equivalent signal on its own
    during fine-tuning, and including E1 here is not adding genuinely new information in
    the strict information-theoretic sense. It is still included, deliberately, because:
      (a) decisions.md names E1 as one of the five ablation arms, which requires E1 to
          exist as a distinct, removable INPUT to the fused model -- not merely be
          implicitly present inside the raw token sequence, where it can't be ablated
          without ablating the text itself;
      (b) a hand-coded lexicon match is a much lower-variance signal than whatever
          DistilBERT might or might not extract from the same tokens in a short
          fine-tuning run -- handing the model the explicit flag is a deliberate inductive
          bias, not redundant input.
    This is a real design choice being made explicit for the first time in this script,
    not one already sitting in decisions.md. >>> LOG THIS IN decisions.md <<< once you've
    read this far -- it changes how "ablating E1" should be described in Chapter 4/5:
    the ablation removes the lexicon-flag shortcut, not the underlying words (DistilBERT's
    text input is unchanged either way).

CLASS IMBALANCE — equivalent, not identical, to the baseline
    `pos_weight` in `nn.BCEWithLogitsLoss`, computed from the TRAINING FOLD's class counts
    as n_negative / n_positive. This is the nearest loss-level analogue to sklearn's
    `class_weight="balanced"` (used identically on both baseline models per the
    2026-08-07 decision) -- but it is NOT a numerically identical transformation:
    sklearn's "balanced" reweights BOTH classes by n_samples/(n_classes * n_samples_class);
    `pos_weight` only reweights the positive-class term inside the BCE loss. Same
    direction, same order of magnitude, not the same formula. If asked in a viva whether
    the two models use "identical" class weighting, the honest answer is "the same
    PRINCIPLE, applied at the point each architecture allows it to be applied, not a
    literal shared formula" -- log this distinction in decisions.md so the controlled-
    comparison claim in Chapter 3/4 isn't overstated.

INPUT
    data/interim/stage3_split.csv — same file train_baseline.py reads.

OUTPUT
    reports/stage5_distilbert_timing.json — timing, peak GPU memory, per-epoch val metrics,
    and the exact config used (epochs, batch size, max length, lr, seed). Overwritten each
    run; rename it to stage5_distilbert_results.json once this is the real (not timing-only)
    run you intend to cite in methodology.md.

USAGE
    First, a quick pipeline sanity check on a small subsample (seconds, not minutes) BEFORE
    committing GPU time to the real run -- catches shape/column bugs cheaply:
        python -m src.models.train_distilbert --subsample 200 --epochs 1

    Then the real timed run (this is the one whose printed seconds/epoch and peak-memory-MB
    answer the Day 3 seed-count decision):
        python -m src.models.train_distilbert --epochs 1

    Later, once the seed/epoch budget is decided, the real Stage 5 result:
        python -m src.models.train_distilbert --epochs <N>
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader, Dataset

try:
    from src.models.train_baseline import TEXT_COLS, _build_text, _metrics
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from src.models.train_baseline import TEXT_COLS, _build_text, _metrics  # noqa: E402

try:
    from src.features.extract_features import extract_all
except ImportError:
    from src.features.extract_features import extract_all  # noqa: E402

SPLIT_CSV = "data/interim/stage3_split.csv"
REPORTS_DIR = Path("reports")
MODELS_DIR = Path("models")
BERT_NAME = "distilbert-base-uncased"

# ---------------------------------------------------------------------------
# Structured evidence vector -- grouped by E-category for Stage 9's ablation.
# Each group lists the RAW columns `extract_all()` produces. "cat" columns are
# one-hot encoded; everything else is numeric (binary flags, counts, or the
# E3 completeness score) and gets StandardScaler-ed alongside the rest.
# ---------------------------------------------------------------------------
_E3_FIELDS = [
    "department", "salary_range", "employment_type", "required_experience",
    "required_education", "industry", "function", "has_company_logo", "has_questions",
]
_LOCATION_SPECIFICITY_CATEGORIES = ["none", "country_only", "region", "city"]

STRUCTURED_FEATURE_GROUPS = {
    "E1": {
        "numeric": [
            "E1_phrase_advance_fee", "E1_phrase_unrealistic_earnings",
            "E1_phrase_off_platform_contact", "E1_phrase_urgency_pressure",
            "E1_phrase_personal_info_request", "E1_phrase_vague_employer",
            "E1_suspicious_phrase_count",
        ],
        "categorical": {},
    },
    "E2": {
        "numeric": [
            "E2_company_profile_present", "E2_company_profile_length",
            "E2_url_token_count", "E2_email_token_count", "E2_phone_token_count",
        ],
        "categorical": {"E2_location_specificity": _LOCATION_SPECIFICITY_CATEGORIES},
    },
    "E3": {
        "numeric": [f"E3_{field}_present" for field in _E3_FIELDS] + ["E3_completeness_score"],
        "categorical": {},
    },
    "E4": {
        "numeric": (
            [f"C{i}_field_present" for i in range(1, 7)]
            + [f"C{i}_evaluable" for i in range(1, 7)]
            + [f"C{i}_contradiction" for i in range(1, 7)]
            + ["C6_text_salary_field_absent", "E4_contradiction_count"]
        ),
        "categorical": {},
    },
}


def _yn_to_bin(series: pd.Series) -> np.ndarray:
    """Y -> 1, everything else (N, NA, NaN) -> 0. Used for the Y/N/NA string columns
    E4 produces (field_present, evaluable, contradiction) -- 'NA' collapses to 0 here
    because the numeric 'evaluable' flag already separately records "could we even check,"
    so the contradiction flag only needs to answer "did it contradict, yes or no.")"""
    return (series.astype(str).str.upper() == "Y").astype(np.float32).values


def build_structured_features(
    features_df: pd.DataFrame, exclude_groups: "list[str] | None" = None
):
    """Turn extract_all()'s output into a numeric matrix.

    Returns (X: float32 ndarray [n, d], feature_names: list[str], groups: list[str])
    where groups[j] names which E-category produced feature_names[j] -- Stage 9's
    leave-one-category-out ablation re-calls this with exclude_groups=["E1"] (etc.)
    rather than hand-building a second feature matrix.
    """
    exclude_groups = set(exclude_groups or [])
    cols, names, groups = [], [], []

    for group, spec in STRUCTURED_FEATURE_GROUPS.items():
        if group in exclude_groups:
            continue
        for col in spec["numeric"]:
            if col not in features_df.columns:
                raise KeyError(f"expected column '{col}' from extract_all() not found")
            raw = features_df[col]
            if pd.api.types.is_numeric_dtype(raw):
                vec = raw.astype(np.float32).values
            else:
                # Y/N/NA columns -- checked by content, not `dtype == object`, because
                # pandas >= 2.x (and pandas 3's default string backend) can give these a
                # dedicated StringDtype rather than `object`; an `== object` check silently
                # mis-handled them during this script's own smoke test (ValueError: could
                # not convert string to float: 'Y') -- caught before being handed off.
                vec = _yn_to_bin(raw)
            cols.append(vec)
            names.append(col)
            groups.append(group)
        for col, categories in spec["categorical"].items():
            raw = features_df[col].astype(str)
            for cat in categories:
                cols.append((raw == cat).astype(np.float32).values)
                names.append(f"{col}={cat}")
                groups.append(group)

    X = np.column_stack(cols).astype(np.float32)
    return X, names, groups


# ---------------------------------------------------------------------------
# Dataset / model
# ---------------------------------------------------------------------------
class FusedDataset(Dataset):
    def __init__(self, encodings, structured: np.ndarray, labels: np.ndarray):
        self.input_ids = encodings["input_ids"]
        self.attention_mask = encodings["attention_mask"]
        self.structured = torch.tensor(structured, dtype=torch.float32)
        self.labels = torch.tensor(labels, dtype=torch.float32)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return {
            "input_ids": self.input_ids[idx],
            "attention_mask": self.attention_mask[idx],
            "structured": self.structured[idx],
            "label": self.labels[idx],
        }


class FusedModel(nn.Module):
    def __init__(self, n_structured: int, hidden: int = 128, dropout: float = 0.2):
        super().__init__()
        from transformers import DistilBertModel

        self.bert = DistilBertModel.from_pretrained(BERT_NAME)
        bert_dim = self.bert.config.hidden_size
        self.head = nn.Sequential(
            nn.Linear(bert_dim + n_structured, hidden),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden, 1),
        )

    def forward(self, input_ids, attention_mask, structured):
        out = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        pooled = out.last_hidden_state[:, 0, :]  # [CLS]
        fused = torch.cat([pooled, structured], dim=1)
        return self.head(fused).squeeze(-1)  # logits, not probabilities


@torch.no_grad()
def _evaluate(model, loader, device) -> dict:
    model.eval()
    all_logits, all_labels = [], []
    for batch in loader:
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


def run(
    split_csv: str = SPLIT_CSV,
    epochs: int = 1,
    batch_size: int = 16,
    max_length: int = 256,
    lr: float = 2e-5,
    seed: int = 0,
    subsample: "int | None" = None,
):
    if not Path(split_csv).exists():
        print(f"ERROR: {split_csv} not found. Run Stage 3 first.", file=sys.stderr)
        sys.exit(1)

    torch.manual_seed(seed)
    np.random.seed(seed)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}" + (f" ({torch.cuda.get_device_name(0)})" if device.type == "cuda" else ""))
    if device.type != "cuda":
        print(
            "WARNING: no CUDA device found -- this will be very slow and the timing from "
            "this run must NOT be used for the Day 3 seed-count decision. Check "
            "torch.cuda.is_available() / your CUDA-build torch install before the real run.",
            file=sys.stderr,
        )

    print(f"Loading {split_csv} ...")
    df = pd.read_csv(split_csv)
    for col in TEXT_COLS + ["fraudulent", "split"]:
        if col not in df.columns:
            raise KeyError(f"expected column '{col}' not found in {split_csv}")

    train = df[df["split"] == "train"].reset_index(drop=True)
    val = df[df["split"] == "val"].reset_index(drop=True)
    if subsample:
        # Pipeline sanity check only -- NOT a valid timing or result. Keeps class balance
        # roughly intact by sampling within each split rather than just df.head(n).
        train = train.sample(n=min(subsample, len(train)), random_state=seed).reset_index(drop=True)
        val = val.sample(n=min(max(subsample // 4, 20), len(val)), random_state=seed).reset_index(drop=True)
        print(f"--subsample {subsample}: SANITY-CHECK RUN ONLY, not a timing or a result.")

    print(f"train: {len(train)} rows ({train['fraudulent'].sum()} fraud)")
    print(f"val:   {len(val)} rows ({val['fraudulent'].sum()} fraud)")

    print("Computing E1-E4 structured features (extract_all) ...")
    train_feat = extract_all(train)
    val_feat = extract_all(val)

    X_train_struct, feature_names, feature_groups = build_structured_features(train_feat)
    X_val_struct, _, _ = build_structured_features(val_feat)
    print(f"Structured vector: {len(feature_names)} features across groups "
          f"{sorted(set(feature_groups))}")

    scaler = StandardScaler().fit(X_train_struct)
    X_train_struct = scaler.transform(X_train_struct).astype(np.float32)
    X_val_struct = scaler.transform(X_val_struct).astype(np.float32)

    y_train = train["fraudulent"].astype(int).values
    y_val = val["fraudulent"].astype(int).values

    print(f"Tokenizing ({BERT_NAME}, max_length={max_length}) ...")
    from transformers import DistilBertTokenizerFast

    tokenizer = DistilBertTokenizerFast.from_pretrained(BERT_NAME)
    train_text = _build_text(train).tolist()
    val_text = _build_text(val).tolist()
    train_enc = tokenizer(train_text, truncation=True, padding=True, max_length=max_length, return_tensors="pt")
    val_enc = tokenizer(val_text, truncation=True, padding=True, max_length=max_length, return_tensors="pt")

    train_ds = FusedDataset(train_enc, X_train_struct, y_train)
    val_ds = FusedDataset(val_enc, X_val_struct, y_val)
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

    model = FusedModel(n_structured=X_train_struct.shape[1]).to(device)

    n_pos = int(y_train.sum())
    n_neg = int(len(y_train) - n_pos)
    pos_weight = torch.tensor([n_neg / max(n_pos, 1)], dtype=torch.float32, device=device)
    print(f"pos_weight (n_neg/n_pos) = {pos_weight.item():.3f}")
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr)

    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats()

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
        if device.type == "cuda":
            torch.cuda.synchronize()
        epoch_time = time.time() - t0
        peak_mem_mb = (
            torch.cuda.max_memory_allocated() / 1e6 if device.type == "cuda" else None
        )
        val_metrics = _evaluate(model, val_loader, device)
        print(
            f"epoch {epoch}: {epoch_time:.1f}s, train_loss={running_loss / len(train_ds):.4f}, "
            f"peak_gpu_mem_mb={peak_mem_mb}, val={val_metrics}"
        )
        epoch_log.append(
            {"epoch": epoch, "seconds": epoch_time, "peak_gpu_mem_mb": peak_mem_mb,
             "train_loss": running_loss / len(train_ds), "val_metrics": val_metrics}
        )

    summary = {
        "seed": seed,
        "n_train": len(train),
        "n_val": len(val),
        "subsample": subsample,
        "config": {
            "epochs": epochs, "batch_size": batch_size, "max_length": max_length, "lr": lr,
            "bert_model": BERT_NAME,
        },
        "structured_feature_count": len(feature_names),
        "structured_feature_groups_included": sorted(set(feature_groups)),
        "pos_weight": pos_weight.item(),
        "device": str(device),
        "epoch_log": epoch_log,
    }

    REPORTS_DIR.mkdir(exist_ok=True)
    out_path = REPORTS_DIR / "stage5_distilbert_timing.json"
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nWritten: {out_path}")

    if not subsample:
        print(
            "\n>>> Use epoch_log[0].seconds above (per-epoch time) and peak_gpu_mem_mb to "
            "make the Day 3 ablation seed-count call, then log it in decisions.md: what "
            "the timing was, 3x5 vs 1x5, and the self-check 'why is a different seed count "
            "for the ablation arms vs. the main comparison still defensible.' <<<"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split-csv", default=SPLIT_CSV)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--max-length", type=int, default=256)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--subsample", type=int, default=None,
                         help="Sanity-check only: train/eval on a small subsample. Not a timing or a result.")
    args = parser.parse_args()
    run(
        split_csv=args.split_csv, epochs=args.epochs, batch_size=args.batch_size,
        max_length=args.max_length, lr=args.lr, seed=args.seed, subsample=args.subsample,
    )
