"""
Stage 8b — select 3 real postings (clear fraud, clear legit, genuinely ambiguous) from
Tier 2, by a pre-specified, mechanical rule (no cherry-picking -- see decisions.md,
2026-10-08, "Stage 8b selection method"), run them through the REAL /score pipeline
(src/api/pipeline.py -- the exact same code src/api/main.py calls), and write the full
result to reports/stage8b_demonstration.json for methodology.md.

SELECTION RULE (decided and logged BEFORE looking at any individual posting's score):
    1. Score every Tier 2 posting (24 fraud + 130 legit = 154) through the trained, frozen
       pipeline -- score only, no SHAP (SHAP/explanation computed only for the 3 finally
       selected, to avoid 154 unneeded KernelExplainer runs).
    2. clear_fraud = the TRUE-fraud posting with the HIGHEST calibrated P(fraud).
    3. clear_legit = the TRUE-legit posting with the LOWEST calibrated P(fraud).
    4. ambiguous   = the posting (either true label) with calibrated P(fraud) CLOSEST to 0.50.
    Mechanical and blind to posting content -- applied to the model's own output only.

WHY TIER 2, NOT EMSCAD TEST
    EMSCAD's test split stays untouched until Stage 9's one-time evaluation. Tier 2 is real,
    external, contemporary data never used for training -- using 3 of its 154 postings here
    doesn't spend or bias Stage 9's later full-154 Tier 2 temporal-transfer result; this is
    demonstration ("does it work at all"), not evaluation ("how well") -- a different DSR
    stage with a different purpose.

USAGE
    python -m src.api.stage8b_select
"""
import json
from pathlib import Path

from src.api.schemas import ScoreRequest
from src.api import pipeline

TIER2_FRAUD = Path("data/raw/tier2/tier2_fraud_raw.jsonl")
TIER2_LEGIT = Path("data/raw/tier2/tier2_legit_raw.jsonl")
OUT_PATH = Path("reports/stage8b_demonstration.json")


def _load_jsonl(path: Path) -> list:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def record_to_request(row: dict) -> ScoreRequest:
    """Tier 2's JSONL rows already carry EMSCAD-shaped field names -- map them straight
    onto ScoreRequest (description -> text), same input contract a real caller would use."""

    def _b(v):
        return bool(v) if v is not None else None

    return ScoreRequest(
        text=row.get("description"),
        title=row.get("title"),
        company_profile=row.get("company_profile"),
        requirements=row.get("requirements"),
        benefits=row.get("benefits"),
        location=row.get("location"),
        telecommuting=_b(row.get("telecommuting")),
        has_company_logo=_b(row.get("has_company_logo")),
        has_questions=_b(row.get("has_questions")),
        department=row.get("department"),
        salary_range=row.get("salary_range"),
        employment_type=row.get("employment_type"),
        required_experience=row.get("required_experience"),
        required_education=row.get("required_education"),
        industry=row.get("industry"),
        function=row.get("function"),
    )


def main():
    print("Loading model/scaler/tokenizer/calibrator ...")
    state = pipeline.get_state()

    records = []
    for src_path, source_name in [(TIER2_FRAUD, "fraud"), (TIER2_LEGIT, "legit")]:
        for i, row in enumerate(_load_jsonl(src_path)):
            records.append({"source_file": source_name, "source_index": i, "row": row})

    print(f"Scoring {len(records)} Tier 2 postings (score only, no SHAP) ...")
    scored = []
    for rec in records:
        row = rec["row"]
        try:
            req = record_to_request(row)
            df_row = pipeline.build_posting_row(req)
            _features_df, _X_raw, X_scaled = pipeline.compute_features(df_row, state)
            inference = pipeline.run_inference(df_row, X_scaled, state)
        except Exception as e:
            print(f"  SKIPPED {rec['source_file']}#{rec['source_index']}: {type(e).__name__}: {e}")
            continue
        scored.append({
            **rec,
            "true_fraudulent": int(row["fraudulent"]),
            "calibrated_fraud_prob": inference["calibrated_fraud_prob"],
            "credibility_score": inference["score"],
            "risk_band": inference["risk_band"],
        })

    fraud_true = [s for s in scored if s["true_fraudulent"] == 1]
    legit_true = [s for s in scored if s["true_fraudulent"] == 0]
    print(f"\nScored {len(scored)}/{len(records)} postings successfully "
          f"({len(fraud_true)} true-fraud, {len(legit_true)} true-legit).")
    if not fraud_true or not legit_true:
        raise RuntimeError("Need at least one scored posting in each true class to select from.")

    clear_fraud = max(fraud_true, key=lambda s: s["calibrated_fraud_prob"])
    clear_legit = min(legit_true, key=lambda s: s["calibrated_fraud_prob"])
    ambiguous = min(scored, key=lambda s: abs(s["calibrated_fraud_prob"] - 0.5))

    selections = {"clear_fraud": clear_fraud, "clear_legit": clear_legit, "ambiguous": ambiguous}
    results = {}
    for label, sel in selections.items():
        row = sel["row"]
        req = record_to_request(row)
        df_row = pipeline.build_posting_row(req)
        features_df, X_raw, X_scaled = pipeline.compute_features(df_row, state)
        inference = pipeline.run_inference(df_row, X_scaled, state)
        explanation = pipeline.build_explanation(features_df, X_raw, inference["pooled_embedding"], state)
        results[label] = {
            "source_file": sel["source_file"],
            "source_index": sel["source_index"],
            "source_url": row.get("source_url"),
            "source_company_name": row.get("source_company_name"),
            "true_fraudulent": sel["true_fraudulent"],
            "title": row.get("title"),
            "credibility_score": inference["score"],
            "risk_band": inference["risk_band"],
            "calibrated_fraud_prob": round(inference["calibrated_fraud_prob"], 4),
            "top_reasons": explanation["top_reasons"],
            "suspicious_phrases": explanation["suspicious_phrases"],
            "contradictions": [c.model_dump() for c in explanation["contradictions"]],
            "verification_checklist": explanation["verification_checklist"],
        }
        print(f"\n=== {label} (true_fraudulent={sel['true_fraudulent']}) ===")
        print(json.dumps(results[label], indent=2))

    OUT_PATH.parent.mkdir(exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump({
            "selection_rule": (
                "clear_fraud = true-fraud posting with max calibrated P(fraud); "
                "clear_legit = true-legit posting with min calibrated P(fraud); "
                "ambiguous = any posting with calibrated P(fraud) closest to 0.5. "
                "Pre-specified before looking at any posting individually -- decisions.md, "
                "2026-10-08, 'Stage 8b selection method'."
            ),
            "n_tier2_total": len(records),
            "n_scored": len(scored),
            "results": results,
        }, f, indent=2)
    print(f"\nWritten: {OUT_PATH}")


if __name__ == "__main__":
    main()
