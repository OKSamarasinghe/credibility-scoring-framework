"""
Stage 7 — Explainability (O4): SHAP over the structured evidence features, rule-message
summaries, and fidelity tests (comprehensiveness, sufficiency, rule-consistency) against
a random-attribution control
================================================================================================
An Explainable Credibility Scoring Framework for Online Recruitment Posts
O.K. Samarasinghe — COBSCCOMP242P-069

PURPOSE
    O4 requires the framework's score to come with an explanation, and requires that
    explanation's FIDELITY to be tested computationally, not assumed (decisions.md
    guardrail; `Research_Objectives_and_Questions_Final.docx`). This script:
      1. Computes SHAP (Shapley Additive Explanations) attributions over the 46
         structured E1-E4 features for a sample of postings, using the seed-0
         DistilBERT+evidence model (Stage 5) exactly as saved -- no retraining.
      2. Surfaces rule-message summaries directly from Stage 4's own `C{i}_evidence`
         string columns for whichever C1-C6 rules fired a contradiction on each posting
         (this needs no new logic -- extract_features.py already writes these strings;
         this script just selects them for the postings where a rule contradiction fired).
      3. Runs comprehensiveness and sufficiency (deletion/insertion) fidelity tests:
         comprehensiveness asks "does removing SHAP's top-ranked features hurt the
         prediction a lot?"; sufficiency asks "does keeping ONLY the top-ranked features
         preserve the prediction well?" Both are compared against a RANDOM-attribution
         control (same deletion/insertion mechanics, but ranking features randomly instead
         of by |SHAP value|) -- if SHAP's ranking does no better than random, the
         explanations are not faithful, and this script will show that rather than hide it.
      4. Runs a rule-consistency check: of the C1-C6 rules that fired a contradiction flag
         on a posting, what fraction have their corresponding E4 feature inside SHAP's
         top-K most important features for that same posting?

WHY SHAP OVER THE STRUCTURED FEATURES, NOT OVER RAW TOKENS
    LIME was dropped in favour of SHAP alone (decisions.md, 2026-09-20). Running SHAP over
    every DistilBERT input token would need hundreds of full transformer forward passes
    PER POSTING (one per coalition sample) -- expensive, and it would explain the model's
    use of raw text, not its use of the E1-E4 evidence taxonomy that is this project's
    actual explainability contribution. Instead:
      - DistilBERT's [CLS] pooled embedding is computed ONCE per posting (the text is
        fixed -- it is not what SHAP is varying).
      - KernelExplainer varies only the 46 structured features, and for each coalition it
        evaluates ONLY the model's small MLP head (`FusedModel.head`) on
        [fixed pooled embedding, candidate structured vector] -- never re-running
        DistilBERT. This is what makes SHAP tractable for ~260 postings within Day 4's
        budget (PROJECT_PLAN.md already flags Day 4 explainability compute as a risk).
    This explains the SAME 46 features Stage 9's ablation studies, at the same group
    granularity (E1/E2/E3/E4) -- SHAP values can be summed within a group for a
    group-level comparison against the ablation's group-level Delta-F1, if useful for
    Chapter 4/5 (not computed by default here; the per-feature values are saved so this is
    possible later without re-running SHAP).

VALIDATION, NOT TEST — A DECISION, LOGGED
    PROJECT_PLAN.md's Day-4 plan text said "consider sub-sampling the test set for the
    fidelity tests specifically." This script uses the VALIDATION split instead.
    Comprehensiveness/sufficiency only need the model's own predicted probability (no true
    label used anywhere in the masking/deletion math), and rule-consistency only needs a
    posting's own C1-C6 flags (also no true label) -- so arguably neither would leak a
    test LABEL into any decision. But "test used once" is one of the guardrails explicitly
    marked never-cut, and the safest way to honour it without relying on a fine distinction
    under deadline pressure is simply not to touch test here at all. See decisions.md for
    the full entry; this is the delegated call this script acts on.

SAMPLE COMPOSITON — NOT a prevalence-representative sample, logged as such
    Validation has only ~130 fraud rows (4.8% prevalence) out of 2682. A plain random
    sample of ~250 rows would carry only ~12 fraud postings -- too few for a stable
    rule-consistency or comprehensiveness estimate broken down by class. This script
    therefore takes ALL validation fraud rows plus an equal-sized random sample of
    validation legitimate rows (seeded, reproducible). This is a deliberate oversample of
    the minority class for explanation-fidelity STATISTICS ONLY -- it does not touch
    model training or Stage 9's test-set evaluation, and results here must not be read as
    "X% of postings have a rule-consistency of Y" at the true ~4.8% base rate; they are
    conditional summaries, reported separately by class where it matters.

METHOD DETAIL
    - KernelExplainer background = the saved StandardScaler's `mean_` (the TRAIN set's
      per-feature mean, in raw units) -- a single reference row. The exact same vector is
      used as the "mask value" in the comprehensiveness/sufficiency deletion/insertion
      tests, so SHAP's own notion of "missing" and the fidelity tests' notion of "removed"
      are the same operation, not two different conventions that happen to share a name.
    - l1_reg=0 (no sparsifying regression) so every one of the 46 features gets an
      attribution, instead of KernelExplainer's default AIC-based feature selection, which
      would silently zero out some features and understate how many of the 46 evidence
      signals the model is using.
    - nsamples=3000 per posting (above shap's own "auto" default of ~2n+2048=2140 for
      n=46, for a little extra regression stability) -- cheap, because each of the 3000
      coalition evaluations only runs the MLP head, not DistilBERT.
    - Comprehensiveness/sufficiency are evaluated at top-k in {2, 5, 10, 15, 23} (roughly
      5%, 11%, 22%, 33%, 50% of the 46 features), and compared against a random-ranking
      control averaged over 10 random permutations per posting (same k values, same mask
      value) -- enough reps that the random control's own variance doesn't swamp the
      SHAP-vs-random gap.
    - Rule-consistency is reported at top-K in {5, 10, 15} (a sensitivity sweep, not one
      cutoff) with a Wilson 95% confidence interval, not a bare mean -- only postings with
      >=1 fired C1-C6 rule count, which can be a small n, and a mean of 1.0 from a small n
      is weaker evidence than it looks.

WHY LOGIT SPACE, NOT PROBABILITY SPACE -- a correction made after seeing a real run
    The first real run of this script (output_space="prob", the original default) produced
    comprehensiveness/sufficiency numbers on the order of 0.001-0.002 -- technically a
    consistent, positive SHAP-vs-random gap at every k, but too small to be a convincing or
    even interpretable number in a results table. The cause: this model's raw probability
    output is heavily skewed toward 0 (consistent with Stage 6's calibrated-score mean of
    4.8/100), so most sampled postings' probabilities sit in the FLAT part of the sigmoid,
    where its derivative is near zero -- ANY feature's marginal effect on probability gets
    crushed there, faithful explanation or not. That is a property of the probability
    transform, not of SHAP's attributions.
    The fix: explain and fidelity-test the model's RAW LOGIT (pre-sigmoid) instead --
    unsaturated, so a feature's real effect on the model's score isn't compressed just
    because the posting's predicted probability happens to be near 0 or 1. This is a
    measurement correction, not a "threshold set after seeing results" in the sense
    decisions.md's guardrail warns against: nothing about WHAT counts as a good result
    changed (still: SHAP's ranking should beat a random one); what changed is choosing a
    scale on which that comparison isn't artificically compressed. `--output-space prob`
    is kept as a CLI option specifically so this before/after can still be shown, logged in
    decisions.md, rather than silently replaced.

WHAT THIS DOES NOT DO
    - Does not touch the test split, anywhere.
    - Does not retrain or fine-tune the Stage 5 model; loads the saved seed-0 checkpoint
      for inference only.
    - Does not run SHAP over raw tokens/text attention -- only over the 46 structured
      features, per the design above.

OUTPUT
    - reports/stage7_shap_values.npz -- per-posting SHAP values (n x 46), the feature
      names/order, the posting ids/labels in the sample, and the base/orig probabilities.
    - reports/stage7_explainability_results.json -- comprehensiveness/sufficiency means
      (SHAP vs random control) at each k, the comprehensiveness/sufficiency GAP (SHAP
      minus random -- the actual fidelity evidence), rule-consistency overall and per-rule,
      and a handful of example rule-message summaries for postings where rules fired.

USAGE
    First, a quick pipeline sanity check on a small subsample (seconds, not minutes):
        python -m src.explain.shap_explain --n-legit 5 --n-fraud 5 --nsamples 300

    Then the real run:
        python -m src.explain.shap_explain
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from src.models.train_baseline import TEXT_COLS, _build_text
    from src.models.train_distilbert import (
        BERT_NAME, FusedModel, SPLIT_CSV, build_structured_features,
    )
    from src.features.extract_features import extract_all
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from src.models.train_baseline import TEXT_COLS, _build_text  # noqa: E402
    from src.models.train_distilbert import (  # noqa: E402
        BERT_NAME, FusedModel, SPLIT_CSV, build_structured_features,
    )
    from src.features.extract_features import extract_all  # noqa: E402

MODELS_DIR = Path("models")
REPORTS_DIR = Path("reports")
SEED = 0  # canonical model, same convention as calibrate.py / train_distilbert.py
RULES = [1, 2, 3, 4, 5, 6]
TOPK_LIST = [2, 5, 10, 15, 23]
RULE_CONSISTENCY_TOPK = 10  # primary cutoff, kept for backward-compatible single-number reporting
RULE_CONSISTENCY_TOPK_LIST = [5, 10, 15]  # sensitivity sweep -- see run(), decisions.md
N_RANDOM_REPS = 10


# ============================================================================
# Pure functions -- no torch/transformers/GPU needed, smoke-tested with synthetic data
# ============================================================================

def fired_rules(row: pd.Series) -> list:
    """Which of C1-C6 fired a contradiction on this posting."""
    return [i for i in RULES if str(row.get(f"C{i}_contradiction", "N")).upper() == "Y"]


def rule_messages(row: pd.Series) -> list:
    """Human-readable evidence strings for whichever rules fired, straight from Stage 4's
    own `C{i}_evidence` columns -- no new text is generated here."""
    return [row[f"C{i}_evidence"] for i in fired_rules(row) if pd.notna(row.get(f"C{i}_evidence"))]


def rule_feature_indices(feature_names: list) -> dict:
    """Maps rule number -> index of its C{i}_contradiction feature within feature_names,
    for the rule-consistency check."""
    idx = {}
    for i in RULES:
        col = f"C{i}_contradiction"
        if col in feature_names:
            idx[i] = feature_names.index(col)
    return idx


def mask_features(x_row: np.ndarray, indices: np.ndarray, background: np.ndarray) -> np.ndarray:
    """Returns a copy of x_row with the given feature indices replaced by `background`'s
    values at those same indices -- the one masking convention used both inside
    KernelExplainer (via its background argument) and here, directly, for the
    deletion/insertion fidelity tests."""
    out = x_row.copy()
    out[indices] = background[indices]
    return out


def comprehensiveness_sufficiency_for_instance(
    predict_fn, x_row: np.ndarray, importance: np.ndarray, background: np.ndarray,
    topk_list: list, orig_prob: float = None,
) -> dict:
    """For ONE posting: rank its 46 features by `importance` (descending), and at each k in
    topk_list compute
      comprehensiveness[k] = orig_prob - prob(x with top-k features REMOVED/masked)
          (bigger is better -- means those features mattered to the prediction)
      sufficiency[k]       = orig_prob - prob(x with ONLY top-k features KEPT, rest masked)
          (smaller absolute value is better -- means top-k alone nearly reproduce the
          original prediction)
    `importance` can be |SHAP value| (the real explanation) or a random permutation's
    rank (the control) -- this function doesn't care which; the caller decides.
    """
    if orig_prob is None:
        orig_prob = float(predict_fn(x_row[None, :])[0])
    ranked = np.argsort(-importance)  # most important first
    comp, suff = {}, {}
    for k in topk_list:
        top_idx = ranked[:k]
        rest_idx = ranked[k:]
        comp_prob = float(predict_fn(mask_features(x_row, top_idx, background)[None, :])[0])
        suff_prob = float(predict_fn(mask_features(x_row, rest_idx, background)[None, :])[0])
        comp[k] = orig_prob - comp_prob
        suff[k] = orig_prob - suff_prob
    return {"orig_prob": orig_prob, "comprehensiveness": comp, "sufficiency": suff}


def random_control_for_instance(
    predict_fn, x_row: np.ndarray, background: np.ndarray, topk_list: list,
    n_features: int, n_reps: int, rng: np.random.Generator, orig_prob: float = None,
) -> dict:
    """Same mechanics as comprehensiveness_sufficiency_for_instance, but the "importance"
    ranking is a random permutation, averaged over n_reps draws -- the fidelity control."""
    if orig_prob is None:
        orig_prob = float(predict_fn(x_row[None, :])[0])
    comp_sum = {k: 0.0 for k in topk_list}
    suff_sum = {k: 0.0 for k in topk_list}
    for _ in range(n_reps):
        rand_importance = rng.permutation(n_features).astype(float)
        out = comprehensiveness_sufficiency_for_instance(
            predict_fn, x_row, rand_importance, background, topk_list, orig_prob=orig_prob
        )
        for k in topk_list:
            comp_sum[k] += out["comprehensiveness"][k]
            suff_sum[k] += out["sufficiency"][k]
    return {
        "orig_prob": orig_prob,
        "comprehensiveness": {k: comp_sum[k] / n_reps for k in topk_list},
        "sufficiency": {k: suff_sum[k] / n_reps for k in topk_list},
    }


def rule_consistency_for_instance(
    fired: list, shap_abs: np.ndarray, rule_idx_map: dict, topk: int,
) -> "float | None":
    """Fraction of this posting's fired rules whose E4 contradiction feature is within
    SHAP's top-`topk` most important features. Returns None if no rule fired (undefined,
    not zero -- a posting with nothing to be consistent ABOUT shouldn't count against the
    model)."""
    if not fired:
        return None
    top_idx = set(np.argsort(-shap_abs)[:topk].tolist())
    hits = sum(1 for i in fired if rule_idx_map.get(i) in top_idx)
    return hits / len(fired)


def wilson_ci(successes: int, n: int, z: float = 1.96) -> "tuple | None":
    """Wilson score 95% confidence interval for a proportion. Used because the usual
    normal-approximation interval breaks down exactly where it matters most here -- a
    proportion of 1.0 (or 0.0) from a small n, which is precisely what a rule-consistency
    figure can look like with only a handful of postings firing any rule at all."""
    if n == 0:
        return None
    p = successes / n
    denom = 1 + z ** 2 / n
    center = (p + z ** 2 / (2 * n)) / denom
    margin = (z / denom) * np.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2))
    return max(0.0, center - margin), min(1.0, center + margin)


# ============================================================================
# Model-dependent (GPU/torch) parts
# ============================================================================

def _load_seed0_model_and_meta(seed: int = SEED):
    import joblib
    import torch

    meta = joblib.load(MODELS_DIR / f"distilbert_structured_feature_meta_seed{seed}.joblib")
    scaler = joblib.load(MODELS_DIR / f"distilbert_structured_scaler_seed{seed}.joblib")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = FusedModel(n_structured=meta["n_structured"]).to(device)
    state_dict = torch.load(
        MODELS_DIR / f"distilbert_fused_state_dict_seed{seed}.pt", map_location=device
    )
    model.load_state_dict(state_dict)
    model.eval()
    return model, scaler, meta, device


def _sample_validation(n_fraud: "int | None", n_legit: "int | None", seed: int = SEED):
    """All validation fraud + a matched random sample of validation legit (see module
    docstring, 'SAMPLE COMPOSITION'). n_fraud/n_legit override the counts for a quick
    smoke run; None means 'use the full designed sample' (all fraud, matched legit)."""
    df = pd.read_csv(SPLIT_CSV)
    val = df[df["split"] == "val"].reset_index(drop=True)
    fraud = val[val["fraudulent"] == 1]
    legit = val[val["fraudulent"] == 0]
    if n_fraud is not None:
        fraud = fraud.sample(n=min(n_fraud, len(fraud)), random_state=seed)
    if n_legit is None:
        n_legit = len(fraud)
    legit = legit.sample(n=min(n_legit, len(legit)), random_state=seed)
    sample = pd.concat([fraud, legit]).reset_index(drop=True)
    return sample


def _pooled_embeddings(sample_text: list, model, tokenizer, device, max_length: int, batch_size: int = 16):
    import torch

    enc = tokenizer(sample_text, truncation=True, padding=True, max_length=max_length, return_tensors="pt")
    pooled_all = []
    n = len(sample_text)
    with torch.no_grad():
        for start in range(0, n, batch_size):
            end = min(start + batch_size, n)
            out = model.bert(
                input_ids=enc["input_ids"][start:end].to(device),
                attention_mask=enc["attention_mask"][start:end].to(device),
            )
            pooled_all.append(out.last_hidden_state[:, 0, :].cpu())
    return torch.cat(pooled_all, dim=0)  # (n, 768)


def _make_predict_fn(pooled_row, model, scaler, device, output: str = "logit"):
    """Returns f(X_raw: np.ndarray [m,46]) -> np.ndarray [m], for a FIXED posting's pooled
    [CLS] embedding, varying only the structured features. This is the function handed to
    KernelExplainer and to the fidelity tests -- it never re-runs DistilBERT; only
    `model.head` is called, once per batch.

    `output` selects what f returns:
      - "logit" (default) -- the raw pre-sigmoid score. Used as the PRIMARY space for SHAP
        and the fidelity tests (see module docstring, "WHY LOGIT SPACE, NOT PROBABILITY").
      - "prob"  -- sigmoid(logit), for human-readable display only (e.g. "this posting's
        predicted probability"). Not used for SHAP/fidelity math by default -- probability
        space saturates near 0/1, which compresses genuine feature importance into a tiny
        number regardless of whether the explanation is faithful.
    """
    import torch

    pooled_t = pooled_row.to(device)  # (768,)

    def f(X_raw: np.ndarray) -> np.ndarray:
        X_scaled = scaler.transform(X_raw).astype(np.float32)
        structured_t = torch.tensor(X_scaled, dtype=torch.float32, device=device)
        pooled_batch = pooled_t.unsqueeze(0).expand(structured_t.shape[0], -1)
        fused = torch.cat([pooled_batch, structured_t], dim=1)
        with torch.no_grad():
            logits = model.head(fused).squeeze(-1)
            out = logits if output == "logit" else torch.sigmoid(logits)
        return out.cpu().numpy()

    return f


def run(n_fraud=None, n_legit=None, nsamples=3000, topk_list=None, n_random_reps=N_RANDOM_REPS,
        seed=SEED, output_space="logit"):
    import time
    import torch
    from transformers import DistilBertTokenizerFast
    import shap

    topk_list = topk_list or TOPK_LIST
    assert output_space in ("logit", "prob")
    ckpt = MODELS_DIR / f"distilbert_fused_state_dict_seed{seed}.pt"
    if not ckpt.exists():
        print(f"ERROR: {ckpt} not found. Run Stage 5 first.", file=sys.stderr)
        sys.exit(1)

    print("Loading seed-0 model + structured-feature metadata ...")
    model, scaler, meta, device = _load_seed0_model_and_meta(seed)
    tokenizer = DistilBertTokenizerFast.from_pretrained(BERT_NAME)

    print("Sampling validation postings (all fraud + matched random legit) ...")
    sample = _sample_validation(n_fraud, n_legit, seed=seed)
    print(f"Sample: {len(sample)} postings ({int(sample['fraudulent'].sum())} fraud, "
          f"{int((sample['fraudulent'] == 0).sum())} legit)")

    sample_feat = extract_all(sample)
    X_struct, feature_names, groups = build_structured_features(sample_feat)
    if feature_names != meta["feature_names"]:
        raise RuntimeError(
            "Structured feature names/order don't match the saved model's metadata -- "
            "extract_features.py or train_distilbert.py may have changed since Stage 5 ran."
        )
    n_features = len(feature_names)
    background = scaler.mean_.astype(np.float32)  # raw-units train mean; one shared "neutral" value

    sample_text = _build_text(sample).tolist()
    print("Computing DistilBERT [CLS] embeddings (once per posting) ...")
    pooled = _pooled_embeddings(sample_text, model, tokenizer, device, meta["max_length"])

    rule_idx_map = rule_feature_indices(feature_names)
    rng = np.random.default_rng(seed)

    shap_values = np.zeros((len(sample), n_features), dtype=np.float32)
    orig_outputs = np.zeros(len(sample), dtype=np.float32)  # in `output_space` units
    orig_probs = np.zeros(len(sample), dtype=np.float32)  # always probability, for display
    comp_shap = {k: [] for k in topk_list}
    suff_shap = {k: [] for k in topk_list}
    comp_rand = {k: [] for k in topk_list}
    suff_rand = {k: [] for k in topk_list}
    rule_consistency_scores = {k: [] for k in RULE_CONSISTENCY_TOPK_LIST}
    rule_consistency_by_rule = {k: {i: [] for i in RULES} for k in RULE_CONSISTENCY_TOPK_LIST}
    example_rule_messages = []

    print(f"Running KernelSHAP per posting (nsamples={nsamples}, output_space={output_space}) ...")
    t_start = time.time()
    for i in range(len(sample)):
        predict_fn = _make_predict_fn(pooled[i], model, scaler, device, output=output_space)
        predict_fn_prob = _make_predict_fn(pooled[i], model, scaler, device, output="prob")
        explainer = shap.KernelExplainer(predict_fn, background[None, :])
        x_row = X_struct[i]
        sv = explainer.shap_values(x_row[None, :], nsamples=nsamples, l1_reg=0, silent=True)
        sv = np.asarray(sv).reshape(-1)
        shap_values[i] = sv
        orig_output = float(predict_fn(x_row[None, :])[0])
        orig_outputs[i] = orig_output
        orig_probs[i] = float(predict_fn_prob(x_row[None, :])[0])  # display only, never fed into fidelity math

        shap_abs = np.abs(sv)
        out_shap = comprehensiveness_sufficiency_for_instance(
            predict_fn, x_row, shap_abs, background, topk_list, orig_prob=orig_output
        )
        out_rand = random_control_for_instance(
            predict_fn, x_row, background, topk_list, n_features, n_random_reps, rng, orig_prob=orig_output
        )
        for k in topk_list:
            comp_shap[k].append(out_shap["comprehensiveness"][k])
            suff_shap[k].append(out_shap["sufficiency"][k])
            comp_rand[k].append(out_rand["comprehensiveness"][k])
            suff_rand[k].append(out_rand["sufficiency"][k])

        row = sample_feat.iloc[i]
        fired = fired_rules(row)
        for k in RULE_CONSISTENCY_TOPK_LIST:
            rc = rule_consistency_for_instance(fired, shap_abs, rule_idx_map, k)
            if rc is not None:
                rule_consistency_scores[k].append(rc)
                top_idx = set(np.argsort(-shap_abs)[:k].tolist())
                for r in fired:
                    rule_consistency_by_rule[k][r].append(1.0 if rule_idx_map.get(r) in top_idx else 0.0)
        if fired and len(example_rule_messages) < 10:
            msgs = rule_messages(row)
            if msgs:
                example_rule_messages.append({
                    "sample_index": int(i),  # position within this sample's dataframe; EMSCAD has no stable posting id in stage3_split.csv
                    "fraudulent": int(row["fraudulent"]),
                    "fired_rules": fired,
                    "messages": msgs,
                    "credibility_prob_raw": float(orig_probs[i]),  # np.float32 isn't JSON-serializable; cast explicitly
                })

        if (i + 1) % 20 == 0 or i == len(sample) - 1:
            elapsed = time.time() - t_start
            print(f"  {i + 1}/{len(sample)} postings done ({elapsed:.1f}s elapsed, "
                  f"{elapsed / (i + 1):.2f}s/posting avg)")
    runtime_seconds = time.time() - t_start

    def _mean(d):
        return {str(k): float(np.mean(v)) for k, v in d.items()}

    rule_consistency_report = {}
    for k in RULE_CONSISTENCY_TOPK_LIST:
        scores = rule_consistency_scores[k]
        n_fired = len(scores)
        successes = int(round(sum(scores)))  # scores are 0/fraction/1 per posting; sum = effective successes
        ci = wilson_ci(successes, n_fired) if n_fired else None
        rule_consistency_report[str(k)] = {
            "mean": float(np.mean(scores)) if scores else None,
            "n_postings_with_fired_rule": n_fired,
            "wilson_95ci": list(ci) if ci else None,
            "by_rule_mean": {
                f"C{i}": (float(np.mean(v)) if v else None)
                for i, v in rule_consistency_by_rule[k].items()
            },
            "by_rule_n": {f"C{i}": len(v) for i, v in rule_consistency_by_rule[k].items()},
        }

    results = {
        "seed": seed,
        "n_sample": len(sample),
        "n_fraud": int(sample["fraudulent"].sum()),
        "n_legit": int((sample["fraudulent"] == 0).sum()),
        "sample_note": (
            "All validation fraud + a matched random sample of validation legit -- NOT "
            "prevalence-representative. Split used: VALIDATION, not test (see module "
            "docstring / decisions.md)."
        ),
        "shap_config": {
            "nsamples": nsamples, "l1_reg": 0, "background": "scaler.mean_ (train mean, raw units)",
            "output_space": output_space,
            "output_space_note": (
                "SHAP and the fidelity tests explain the model's RAW LOGIT, not the "
                "post-sigmoid probability, unless output_space='prob' was explicitly "
                "requested. Probability space saturates near 0/1 (the sigmoid derivative "
                "goes to ~0 there), which compresses genuine feature importance into a "
                "tiny, hard-to-interpret number -- this was observed on a first run and "
                "corrected before being written up; see decisions.md."
            ) if output_space == "logit" else (
                "Probability-space run -- kept for comparison against the logit-space "
                "default; expect smaller, saturation-compressed magnitudes, see decisions.md."
            ),
        },
        "runtime_seconds": runtime_seconds,
        "fidelity": {
            "topk_list": topk_list,
            "output_space": output_space,
            "comprehensiveness_shap_mean": _mean(comp_shap),
            "comprehensiveness_random_mean": _mean(comp_rand),
            "comprehensiveness_gap_shap_minus_random": {
                str(k): float(np.mean(comp_shap[k]) - np.mean(comp_rand[k])) for k in topk_list
            },
            "sufficiency_shap_mean_abs": {str(k): float(np.mean(np.abs(suff_shap[k]))) for k in topk_list},
            "sufficiency_random_mean_abs": {str(k): float(np.mean(np.abs(suff_rand[k]))) for k in topk_list},
            "sufficiency_gap_random_minus_shap_abs": {
                str(k): float(np.mean(np.abs(suff_rand[k])) - np.mean(np.abs(suff_shap[k]))) for k in topk_list
            },
            "n_random_reps": n_random_reps,
        },
        "rule_consistency": {
            "primary_topk": RULE_CONSISTENCY_TOPK,
            "sensitivity_by_topk": rule_consistency_report,
            "note": (
                "Reported with a Wilson 95% CI, not as a bare mean -- n is small (only "
                "postings with >=1 fired C1-C6 rule count), and a mean of 1.0 from a small "
                "n is weaker evidence than it looks. Sparse binary features (most postings "
                "have contradiction=0) sit far from the background/mean value when they DO "
                "fire, which structurally tends to earn them large SHAP attributions -- "
                "high rule-consistency is plausible for this reason as well as, or instead "
                "of, the model genuinely relying on that rule; this script doesn't have a "
                "way to tell those apart and the discussion chapter should say so."
            ),
        },
        "example_rule_messages": example_rule_messages,
    }

    REPORTS_DIR.mkdir(exist_ok=True)
    np.savez(
        REPORTS_DIR / "stage7_shap_values.npz",
        shap_values=shap_values, feature_names=np.array(feature_names, dtype=object),
        groups=np.array(groups, dtype=object), orig_outputs=orig_outputs, orig_probs=orig_probs,
        output_space=output_space,
        sample_index=np.arange(len(sample)),  # position within this sample; EMSCAD has no stable posting id in stage3_split.csv
        fraudulent=sample_feat["fraudulent"].values,
    )
    with open(REPORTS_DIR / "stage7_explainability_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n=== Fidelity summary (SHAP vs random control, {output_space}-space) ===")
    for k in topk_list:
        print(
            f"k={k}: comprehensiveness SHAP={np.mean(comp_shap[k]):.4f} "
            f"random={np.mean(comp_rand[k]):.4f} "
            f"(gap={np.mean(comp_shap[k]) - np.mean(comp_rand[k]):+.4f})  |  "
            f"sufficiency |SHAP|={np.mean(np.abs(suff_shap[k])):.4f} "
            f"|random|={np.mean(np.abs(suff_rand[k])):.4f}"
        )
    print("\n=== Rule-consistency (sensitivity by top-k, with Wilson 95% CI) ===")
    for k in RULE_CONSISTENCY_TOPK_LIST:
        rep = rule_consistency_report[str(k)]
        if rep["mean"] is not None:
            lo, hi = rep["wilson_95ci"]
            print(f"top-{k}: mean={rep['mean']:.4f}  95% CI=[{lo:.3f}, {hi:.3f}]  "
                  f"n={rep['n_postings_with_fired_rule']} postings with >=1 fired rule")
    print(f"\nRuntime: {runtime_seconds:.1f}s total, {runtime_seconds / len(sample):.2f}s/posting avg")
    print(f"\nWritten: {REPORTS_DIR / 'stage7_explainability_results.json'}, "
          f"{REPORTS_DIR / 'stage7_shap_values.npz'}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-fraud", type=int, default=None, help="override fraud sample count (default: all)")
    parser.add_argument("--n-legit", type=int, default=None, help="override legit sample count (default: matched to fraud)")
    parser.add_argument("--nsamples", type=int, default=3000, help="KernelSHAP coalitions per posting")
    parser.add_argument("--n-random-reps", type=int, default=N_RANDOM_REPS)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument(
        "--output-space", choices=["logit", "prob"], default="logit",
        help="space SHAP/fidelity are computed in (default: logit -- avoids probability "
             "saturation; see decisions.md)",
    )
    args = parser.parse_args()
    run(
        n_fraud=args.n_fraud, n_legit=args.n_legit, nsamples=args.nsamples,
        n_random_reps=args.n_random_reps, seed=args.seed, output_space=args.output_space,
    )


if __name__ == "__main__":
    main()
