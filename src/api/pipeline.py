"""
Stage 8 — Real pipeline wiring behind /score
=================================================================
An Explainable Credibility Scoring Framework for Online Recruitment Posts
O.K. Samarasinghe — COBSCCOMP242P-069

WHAT THIS MODULE DOES
    Implements the four seams `src/api/main.py` calls (preprocess -> extract_features ->
    predict -> explain) with the REAL Stage 1/4/5/6/7 code, loaded exactly as each stage
    saved it -- no retraining, no re-fitting, no new feature logic. Model/tokenizer/scaler/
    calibrator are loaded ONCE (PipelineState, lazily constructed on first request) rather
    than per-request, since the DistilBERT checkpoint alone is ~250MB.

WHY A SEPARATE MODULE FROM main.py
    main.py stays a thin FastAPI route; everything that can be unit-tested without spinning
    up a server lives here.

REUSE, NOT REIMPLEMENTATION (the point of building Stage 1/4/5/6/7 first)
    - Stage 1 token extraction / salary placeholder / missingness: imported directly from
      `src.ingestion.load_emscad` (extract_contact_tokens, normalise_salary_placeholder,
      flag_missingness) -- NOT `load_emscad()` itself, which is batch-CSV-specific (asserts
      a fraud count, requires a `fraudulent` column neither of which a live request has).
    - Stage 4 features: `extract_all()` from `src.features.extract_features`, unmodified.
    - Stage 5 model/structured-vector building: `FusedModel`, `build_structured_features`,
      `BERT_NAME` from `src.models.train_distilbert`; `_build_text` from
      `src.models.train_baseline` (same text scope as training: title+description+
      requirements+benefits).
    - Stage 6 calibration: whichever calibrator `src.calibration.calibrate` saved
      (models/stage6_calibrator.joblib) is loaded and applied generically (isotonic vs.
      Platt detected by class name, since each needs a different input -- see
      `_apply_calibrator`), not hardcoded to isotonic even though isotonic is what won
      2026-10-08's run.
    - Stage 7 explainability: `_load_seed0_model_and_meta`, `_make_predict_fn`,
      `fired_rules`, `rule_feature_indices` imported directly from `src.explain.shap_explain`
      so live-request SHAP uses the exact same KernelExplainer configuration (background =
      scaler.mean_, l1_reg=0, logit-space) already validated in Stage 7, not a second,
      possibly-drifted implementation.

INPUT CONTRACT (decisions.md, 2026-10-08, "Stage 8 wiring: API input contract resolved")
    A live ScoreRequest's optional structured fields are turned into exactly the same
    EMSCAD-shaped one-row DataFrame Stage 1 would have produced from a CSV row, with
    unsupplied fields genuinely missing (not guessed, not defaulted to "present"). Two
    caveats logged there and worth repeating at the point they matter:
      - `telecommuting` has no "missing" state in EMSCAD (always present) and defaults to
        False/on-site here if the caller doesn't say -- can produce a spurious C1 flag if
        the posting text itself describes remote work.
      - `E2_*_token_count` only matches EMSCAD's own anonymisation placeholder format
        (#EMAIL_xxxx#, etc.), not a real email/phone/URL in live text -- these three
        features are structurally 0 for every live request (Finding 2, decisions.md).

OUTPUT MAPPING (new Stage 8 design work, not a re-litigation of Stage 7)
    `top_reasons` / `suspicious_phrases` / `verification_checklist` are template-generated
    from SHAP attributions, the E1 lexicon's actual regex matches, and E3/E2 presence flags
    respectively -- deterministic, rule-based text (consistent with RQ4's "model-agnostic
    explanation methods AND rule-based evidence summaries"), not a measured result requiring
    separate validation. Reasonable first draft; review the wording in
    `_describe_feature` / `_build_checklist` and adjust freely -- these are UX templates below
    the measured science Stage 7 already validated, not Stage 7's fidelity claims themselves.
"""
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from src.ingestion.load_emscad import (
    extract_contact_tokens, normalise_salary_placeholder, flag_missingness,
)
from src.features.extract_features import extract_all, E1_TEXT_COLS, _E1_COMPILED
from src.models.train_baseline import _build_text
from src.models.train_distilbert import build_structured_features
from src.explain.shap_explain import (
    _load_seed0_model_and_meta, _make_predict_fn, fired_rules, rule_feature_indices,
)
from src.api.schemas import Contradiction, ScoreRequest

MODELS_DIR = Path("models")
REPORTS_DIR = Path("reports")
SEED = 0  # canonical model -- same convention as calibrate.py / shap_explain.py
DEFAULT_RISK_THRESHOLDS = (33, 66)  # fallback only; real run reads reports/stage6_calibration_results.json

RULE_FIELD = {
    1: "telecommuting", 2: "location", 3: "employment_type",
    4: "required_experience", 5: "required_education", 6: "salary_range",
}


# ============================================================================
# Model/scaler/tokenizer/calibrator -- loaded once, reused across requests
# ============================================================================

class PipelineState:
    def __init__(self):
        import joblib
        from transformers import DistilBertTokenizerFast

        ckpt = MODELS_DIR / f"distilbert_fused_state_dict_seed{SEED}.pt"
        if not ckpt.exists():
            raise RuntimeError(
                f"{ckpt} not found. Run Stage 5 (src.models.train_distilbert) and Stage 6 "
                f"(src.calibration.calibrate) before starting the API."
            )

        # Reuses Stage 7's own loader, not a second implementation -- same model/scaler/
        # meta/device every one of Stage 5/6/7/8 ends up using for seed 0.
        self.model, self.scaler, self.meta, self.device = _load_seed0_model_and_meta(SEED)
        self.tokenizer = DistilBertTokenizerFast.from_pretrained(self.meta["bert_model"])

        calibrator_path = MODELS_DIR / "stage6_calibrator.joblib"
        self.calibrator = joblib.load(calibrator_path) if calibrator_path.exists() else None
        if self.calibrator is None:
            print(
                "WARNING: models/stage6_calibrator.joblib not found -- serving RAW, "
                "uncalibrated probabilities. Run src.calibration.calibrate first."
            )

        self.risk_thresholds = DEFAULT_RISK_THRESHOLDS
        results_path = REPORTS_DIR / "stage6_calibration_results.json"
        if results_path.exists():
            with open(results_path) as f:
                bands = json.load(f)["risk_bands_0_100"]
            # calibrate.py's own dict keys name the SCORE band position, not risk level --
            # see decisions.md 2026-10-08 Finding 1. We only take the two boundary numbers
            # (the real measured terciles); the risk DIRECTION is handled separately in
            # risk_band_from_score().
            self.risk_thresholds = (bands["low"][1], bands["medium"][1])

        self.feature_names = self.meta["feature_names"]
        self.rule_idx_map = rule_feature_indices(self.feature_names)


_STATE: "PipelineState | None" = None


def get_state() -> PipelineState:
    global _STATE
    if _STATE is None:
        _STATE = PipelineState()
    return _STATE


# ============================================================================
# Stage 1 seam -- preprocess()
# ============================================================================

def build_posting_row(req: ScoreRequest) -> pd.DataFrame:
    """ONE live posting -> the same EMSCAD-shaped one-row DataFrame Stage 4 expects.
    Reuses Stage 1's own token-extraction / salary-placeholder / missingness functions
    directly so this can never silently drift from how the training data was built.
    Does NOT call `load_emscad.load_emscad()` itself -- that function is batch-CSV
    specific (asserts a fraud count, needs a `fraudulent` column) and wrong for one
    live row.
    """
    row = {
        "title": req.title or "",
        "description": req.text or "",
        "requirements": req.requirements or "",
        "benefits": req.benefits or "",
        "company_profile": req.company_profile or "",
        "location": req.location or "",
        # telecommuting has no "missing" state in EMSCAD -- defaults to 0 (on-site) if
        # unsupplied. See module docstring / decisions.md 2026-10-08 for the known risk
        # this creates (a spurious C1 flag if the text itself describes remote work).
        "telecommuting": 1 if req.telecommuting else 0,
        # has_company_logo/has_questions: unlike EMSCAD (never missing), genuinely missing
        # here if the caller doesn't say -- NaN, not a guessed 0, so E3's completeness
        # score reflects real uncertainty rather than a fabricated "no logo" fact.
        "has_company_logo": float(req.has_company_logo) if req.has_company_logo is not None else np.nan,
        "has_questions": float(req.has_questions) if req.has_questions is not None else np.nan,
        "department": req.department,
        "salary_range": req.salary_range,
        "employment_type": req.employment_type,
        "required_experience": req.required_experience,
        "required_education": req.required_education,
        "industry": req.industry,
        "function": req.function,
    }
    df = pd.DataFrame([row])
    df = extract_contact_tokens(df)        # Stage 1 Rule 2, reused verbatim
    df = normalise_salary_placeholder(df)  # Stage 1 Rule 4, reused verbatim
    df = flag_missingness(df)              # Stage 1 Rule 5, reused verbatim
    return df


# ============================================================================
# Stage 4 seam -- extract_features()
# ============================================================================

def compute_features(df_row: pd.DataFrame, state: PipelineState):
    """Returns (features_df, X_raw, X_scaled). Raises if the live feature vector's
    name/order doesn't match the saved model's metadata -- that would mean
    extract_features.py or train_distilbert.py changed since Stage 5 trained, and
    serving against a mismatched vector would silently corrupt every prediction."""
    features_df = extract_all(df_row)
    X_raw, names, _groups = build_structured_features(features_df)
    if names != state.feature_names:
        raise RuntimeError(
            "Structured feature name/order mismatch vs. the saved model's metadata -- "
            "extract_features.py or train_distilbert.py changed since Stage 5 trained. "
            "Re-run Stage 5 and Stage 6 before serving; don't serve against a mismatched "
            "feature vector."
        )
    X_scaled = state.scaler.transform(X_raw).astype(np.float32)
    return features_df, X_raw.astype(np.float32), X_scaled


# ============================================================================
# Stage 5/6 seam -- predict()
# ============================================================================

def risk_band_from_score(score: int, thresholds: tuple) -> str:
    """credibility_score is 'higher = more credible' (schemas.py), so a LOW score is HIGH
    risk. calibrate.py's own risk_bands_0_100 dict keys ("low"/"medium"/"high") name the
    SCORE band position, not the risk direction -- see decisions.md 2026-10-08 Finding 1.
    Direction is corrected here; the two threshold numbers are Stage 6's real measured
    terciles (33/66), never guessed."""
    lo, hi = thresholds
    if score <= lo:
        return "High"
    if score <= hi:
        return "Medium"
    return "Low"


def _apply_calibrator(calibrator, logit: np.ndarray, raw_prob: np.ndarray) -> np.ndarray:
    """Isotonic was what 2026-10-08's run selected, but this stays generic (keyed on the
    saved object's class, not hardcoded) in case calibration is re-run and Platt wins
    instead -- each needs a different input (calibrate.py: isotonic on the probability,
    Platt on the raw logit)."""
    if calibrator is None:
        return raw_prob
    cls_name = type(calibrator).__name__
    if cls_name == "IsotonicRegression":
        return calibrator.transform(raw_prob)
    if cls_name == "LogisticRegression":
        return calibrator.predict_proba(logit.reshape(-1, 1))[:, 1]
    raise RuntimeError(f"Unrecognised calibrator type: {cls_name}")


def run_inference(df_row: pd.DataFrame, X_scaled: np.ndarray, state: PipelineState) -> dict:
    """Tokenizes exactly as training did (_build_text: title+description+requirements+
    benefits), runs DistilBERT once to get the [CLS] pooled embedding, fuses it with the
    scaled structured vector through the trained MLP head, applies the saved calibrator.
    Returns the pooled embedding too, so explain() can re-use it -- SHAP never re-runs
    DistilBERT, the same tractability trick Stage 7 depends on."""
    import torch

    text = _build_text(df_row).tolist()
    enc = state.tokenizer(
        text, truncation=True, padding=True, max_length=state.meta["max_length"],
        return_tensors="pt",
    )
    with torch.no_grad():
        bert_out = state.model.bert(
            input_ids=enc["input_ids"].to(state.device),
            attention_mask=enc["attention_mask"].to(state.device),
        )
        pooled = bert_out.last_hidden_state[:, 0, :]  # (1, 768)
        structured_t = torch.tensor(X_scaled, dtype=torch.float32, device=state.device)
        fused = torch.cat([pooled, structured_t], dim=1)
        logit = state.model.head(fused).squeeze(-1)  # (1,)

    logit_np = logit.cpu().numpy()
    raw_prob = 1.0 / (1.0 + np.exp(-logit_np))
    # calibrated_fraud_prob is calibrated P(fraudulent=1) -- the model was trained on
    # y = train["fraudulent"] (train_distilbert.py) and calibrate.py's Platt/isotonic
    # calibrators were both fit to predict that same label. credibility_score is the
    # COMPLEMENT of this, never this value directly.
    #
    # Caught via the first real smoke-test run, not by inspection: an obvious-scam example
    # scored 71 ("Low risk") and a clean, complete posting scored 2 ("High risk") --
    # exactly backwards. Root cause: calibrate.py's own docstring/output
    # (`calibrated_score_summary`, mean 4.85 on validation -- matching the ~4.8% fraud
    # base rate almost exactly, i.e. clearly P(fraud), not P(credible)) calls
    # `final_prob * 100` the "credibility_score" Stage 8 should return. That calibration
    # itself (Brier/ECE, which calibrator won) is unaffected and still correct -- only the
    # LABEL "credibility" attached to the raw calibrated number was backwards. See
    # decisions.md, 2026-10-08, "Stage 8 smoke test caught an inverted credibility score".
    calibrated_fraud_prob = _apply_calibrator(state.calibrator, logit_np, raw_prob)
    credibility_prob = 1.0 - float(calibrated_fraud_prob[0])

    score = int(round(credibility_prob * 100))
    score = max(0, min(100, score))

    return {
        "logit": float(logit_np[0]),
        "raw_fraud_prob": float(raw_prob[0]),
        "calibrated_fraud_prob": float(calibrated_fraud_prob[0]),
        "credibility_prob": credibility_prob,
        "score": score,
        "risk_band": risk_band_from_score(score, state.risk_thresholds),
        "pooled_embedding": pooled.cpu(),  # (1, 768) -- reused by explain(), not recomputed
    }


# ============================================================================
# Stage 7 seam -- explain()
# ============================================================================

def _describe_feature(name: str, value: float, shap_value: float) -> str:
    """Templates a human-readable reason from one structured feature's name, raw value,
    and signed SHAP contribution. First-draft UX text -- reasonable defaults, meant to be
    reviewed/edited, not a measured claim itself (the measured claim is that SHAP beats
    random at ranking these features at all; Stage 7 already tested that)."""
    # shap_value is the feature's attribution on the raw LOGIT (output="logit" in
    # _make_predict_fn, same space Stage 7 explains) -- the model was trained toward
    # y=fraudulent, so a HIGHER logit means MORE fraud-like, i.e. LOWER credibility.
    # "the score" here means credibility_score (what the API actually returns), so the
    # direction is the OPPOSITE of the raw SHAP sign. See decisions.md, 2026-10-08,
    # "Stage 8 smoke test caught an inverted credibility score" -- same root cause as the
    # score-computation fix in run_inference(), caught in the same pass.
    #
    # "for this posting" suffix added 2026-10-09 (decisions.md) -- a real live result (a
    # posting with 0% of structured fields filled in) produced FOUR separate lines reading
    # "<field> was missing, which raised the score", which a user can easily misread as a
    # general rule ("leaving fields blank is good"). It isn't: each of these is a single
    # KernelSHAP attribution for THIS ONE prediction, conditioned on every other feature's
    # value in this specific posting -- not a trend, not advice, and not guaranteed to hold
    # the same way on a different posting. Deliberately kept the literal substrings "raised
    # the score" / "lowered the score" byte-for-byte unchanged (only appending text after
    # them) because frontend/index.html's renderResults() keys its red/green colouring off
    # exactly those two substrings -- this is a wording-only change, nothing computational,
    # and the frontend needed no corresponding edit.
    direction = "lowered" if shap_value > 0 else "raised"
    base, _, cat = name.partition("=")

    if base == "E3_completeness_score":
        return f"Only {value * 100:.0f}% of standard posting fields were filled in, which {direction} the score for this posting."
    if base.startswith("E3_") and base.endswith("_present"):
        field = base[len("E3_"):-len("_present")]
        state_word = "was provided" if value >= 0.5 else "was missing"
        return f"The '{field}' field {state_word}, which {direction} the score for this posting."
    if base == "E2_company_profile_present":
        state_word = "was provided" if value >= 0.5 else "was missing"
        return f"An employer profile {state_word}, which {direction} the score for this posting."
    if base == "E2_company_profile_length":
        return f"The employer profile is {value:.0f} characters long, which {direction} the score for this posting."
    if base in ("E2_url_token_count", "E2_email_token_count", "E2_phone_token_count"):
        kind = base.split("_")[1]
        return (
            f"The posting text contains {value:.0f} embedded {kind} reference(s), "
            f"which {direction} the score for this posting."
        )
    if base == "E2_location_specificity":
        label = cat or "none"
        state_word = "was specified at this level" if value >= 0.5 else "was NOT specified at this level"
        return f"The posting's location ({label}) {state_word}, which {direction} the score for this posting."
    if base.startswith("E1_phrase_"):
        group = base[len("E1_phrase_"):].replace("_", " ")
        state_word = "was found" if value >= 0.5 else "was NOT found"
        return f"Text matching the '{group}' phrase group {state_word}, which {direction} the score for this posting."
    if base == "E1_suspicious_phrase_count":
        return f"{value:.0f} suspicious-phrase group(s) matched in the text, which {direction} the score for this posting."
    # C1-C6 "field_present" -- was this metadata detail even given, independent of
    # whether it's consistent with the text (that's the separate C{i}_contradiction
    # feature, already shown via its own evidence string). Added 2026-10-09 (decisions.md)
    # after a student couldn't read "C2_field_present" in the UI -- same wording style as
    # the E3_*_present template above, using RULE_FIELD for the plain field name.
    m = re.fullmatch(r"C([1-6])_field_present", base)
    if m:
        field_label = RULE_FIELD.get(int(m.group(1)), base).replace("_", " ")
        state_word = "was given" if value >= 0.5 else "was left blank"
        return f"The posting's '{field_label}' detail {state_word}, which {direction} the score for this posting."
    if base == "E4_contradiction_count":
        return (
            f"{value:.0f} of the posting's details didn't match what the text said "
            f"(out of up to 6 checked), which {direction} the score for this posting."
        )
    # C1-C6 "contradiction" itself, for the NOT-fired case only -- a FIRED contradiction
    # (value=1) is already excluded here and shown instead via its own evidence string in
    # top_reasons (see `covered` in build_explanation). This branch only runs for value=0,
    # which SHAP can still rank as important (e.g. "no contradiction" being reassuring).
    # Added 2026-10-09 in the same pass as C{i}_field_present, after checking exhaustively
    # for every C1-C6/E4 feature rather than stopping at the two the student had seen.
    m = re.fullmatch(r"C([1-6])_contradiction", base)
    if m:
        field_label = RULE_FIELD.get(int(m.group(1)), base).replace("_", " ")
        return (
            f"No mismatch was found between the posting's '{field_label}' detail and the "
            f"text, which {direction} the score for this posting."
        )
    if base == "C6_text_salary_field_absent":
        state_word = "was found" if value >= 0.5 else "was NOT found"
        return (
            f"A dollar figure mentioned in the text despite no salary range being listed "
            f"{state_word}, which {direction} the score for this posting."
        )
    return f"The '{name}' signal {direction} the score for this posting."


def _is_bookkeeping_feature(name: str) -> bool:
    """C{i}_evaluable records whether a C-rule COULD be checked at all (field present AND
    recognisable text language to compare it to) -- it is not itself evidence of fraud, so
    there is no honest 'which raised/lowered the score' sentence for it (unlike
    C{i}_field_present, which IS a real signal -- missing metadata). Excluded from
    'Why this score' entirely rather than given a misleading template. Added 2026-10-09,
    same pass as the C{i}_field_present fix above -- see decisions.md."""
    base, _, _ = name.partition("=")
    return bool(re.fullmatch(r"C[1-6]_evaluable", base))


def _build_checklist(row: pd.Series) -> list:
    """Rule-based (not learned) verification prompts from E2/E3 presence flags --
    deterministic template text, first draft, review freely."""
    items = []
    if row.get("E3_salary_range_present", 0) == 0:
        items.append("No salary range was given — ask the recruiter directly before proceeding.")
    if row.get("E2_company_profile_present", 0) == 0:
        items.append(
            "No employer description was given — independently verify the company exists "
            "(its own website, LinkedIn, or a business registry)."
        )
    if row.get("E3_department_present", 0) == 0 and row.get("E3_industry_present", 0) == 0:
        items.append("Department and industry weren't specified — ask what team and sector this role sits in.")
    if (
        row.get("E2_url_token_count", 0) == 0
        and row.get("E2_email_token_count", 0) == 0
        and row.get("E2_phone_token_count", 0) == 0
    ):
        items.append(
            "No direct contact channel was detected in the text — confirm how you're "
            "expected to apply or follow up."
        )
    if not items:
        items.append(
            "This posting includes most standard fields — still verify details directly "
            "with the employer before sharing personal information."
        )
    return items


def build_explanation(
    features_df: pd.DataFrame, X_raw: np.ndarray, pooled_embedding, state: PipelineState,
    nsamples: int = 2000,
) -> dict:
    """SHAP over the same 46 structured features Stage 7 explains, for this one posting,
    using the exact KernelExplainer configuration Stage 7 validated (background =
    scaler.mean_, l1_reg=0, logit space) via the shared `_make_predict_fn` import --
    not a second, possibly-drifted implementation."""
    import shap

    row = features_df.iloc[0]
    fired = fired_rules(row)
    contradictions = [
        Contradiction(rule=f"C{i}", field=RULE_FIELD[i], detail=str(row[f"C{i}_evidence"]))
        for i in fired
        if pd.notna(row.get(f"C{i}_evidence"))
    ]

    # X_raw arrives as shape (1, n_features) -- build_structured_features() is written for
    # a whole DataFrame and returns a one-ROW BATCH here, not a flat per-feature vector.
    # Flatten once, up front, so every per-feature index below is unambiguous. (Caught on
    # the first real smoke-test run: `float(X_raw[idx])` was silently indexing the ROW axis
    # -- idx=0 returned the entire 46-length row instead of one scalar, which crashed with
    # "only 0-dimensional arrays can be converted to Python scalars" instead of a quieter,
    # more dangerous wrong-number bug. Logged in decisions.md.)
    x_row = X_raw.reshape(-1)

    predict_fn = _make_predict_fn(pooled_embedding[0], state.model, state.scaler, state.device, output="logit")
    background = state.scaler.mean_.astype(np.float32)
    explainer = shap.KernelExplainer(predict_fn, background[None, :])
    sv = explainer.shap_values(x_row[None, :], nsamples=nsamples, l1_reg=0, silent=True)
    shap_vals = np.asarray(sv).reshape(-1)
    shap_abs = np.abs(shap_vals)
    ranked = np.argsort(-shap_abs)

    # Don't repeat a rule's own evidence string as a second, generic SHAP-templated reason
    # for the same underlying C{i}_contradiction feature.
    covered = {state.rule_idx_map[i] for i in fired if i in state.rule_idx_map}
    top_reasons = [c.detail for c in contradictions]
    for idx in ranked:
        if len(top_reasons) >= 5:
            break
        if idx in covered:
            continue
        name = state.feature_names[idx]
        if _is_bookkeeping_feature(name):
            continue
        top_reasons.append(_describe_feature(name, float(x_row[idx]), float(shap_vals[idx])))
    if not top_reasons:
        top_reasons = ["No single feature dominated this prediction."]

    # Suspicious phrases -- the actual matched text from E1's lexicon, not just group names.
    blob = " ".join(str(row.get(c, "")) for c in E1_TEXT_COLS)
    suspicious_phrases = []
    for patterns in _E1_COMPILED.values():
        for pat in patterns:
            m = pat.search(blob)
            if m:
                suspicious_phrases.append(m.group(0).strip())
                break

    return {
        "top_reasons": top_reasons,
        "suspicious_phrases": suspicious_phrases,
        "contradictions": contradictions,
        "verification_checklist": _build_checklist(row),
    }
