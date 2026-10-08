"""
Stage 8 smoke test — run this BEFORE starting the server, to catch import/shape errors
fast without the HTTP layer in the way. Exercises the real pipeline end-to-end on two
hand-written postings (one with several red flags, one looking ordinary) via the same
functions src/api/main.py calls.

Usage (from the project root, in your real venv with torch/transformers/shap installed):
    python -m src.api.stage8_smoke_test
"""
import json
import time

from src.api.schemas import ScoreRequest
from src.api import pipeline


EXAMPLES = {
    "suspicious": ScoreRequest(
        text=(
            "URGENT HIRING! Work from home and earn $500 a day, no experience necessary. "
            "Act now, limited spots! Send a small registration fee to start and we will "
            "ship your starter kit immediately. Contact us directly at our personal email "
            "for faster processing."
        ),
        title="Work From Home - Immediate Start",
        telecommuting=False,  # text says remote, field says on-site -- should fire C1
    ),
    "ordinary": ScoreRequest(
        text=(
            "We are looking for a mid-level backend engineer to join our platform team. "
            "You will work on our payments infrastructure alongside senior engineers, "
            "with a focus on reliability and testing."
        ),
        title="Backend Engineer, Payments",
        company_profile="Acme Software Ltd is a 200-person fintech company based in London, "
                         "building payment infrastructure for small businesses since 2014.",
        location="United Kingdom, , London",
        employment_type="Full-time",
        required_experience="Mid-Senior level",
        required_education="Bachelor's Degree",
        department="Engineering",
        industry="Financial Technology",
        function="Engineering",
        salary_range="55000-70000",
        has_company_logo=True,
        has_questions=True,
        telecommuting=False,
    ),
}


def main():
    print("Loading model/scaler/tokenizer/calibrator (first call only) ...")
    t0 = time.time()
    state = pipeline.get_state()
    print(f"  loaded in {time.time() - t0:.1f}s, device={state.device}")

    for name, req in EXAMPLES.items():
        print(f"\n=== {name} ===")
        t0 = time.time()
        df_row = pipeline.build_posting_row(req)
        features_df, X_raw, X_scaled = pipeline.compute_features(df_row, state)
        inference = pipeline.run_inference(df_row, X_scaled, state)
        explanation = pipeline.build_explanation(features_df, X_raw, inference["pooled_embedding"], state)
        elapsed = time.time() - t0

        result = {
            "credibility_score": inference["score"],
            "risk_band": inference["risk_band"],
            "raw_fraud_prob": round(inference["raw_fraud_prob"], 4),
            "calibrated_fraud_prob": round(inference["calibrated_fraud_prob"], 4),
            "credibility_prob": round(inference["credibility_prob"], 4),
            "top_reasons": explanation["top_reasons"],
            "suspicious_phrases": explanation["suspicious_phrases"],
            "contradictions": [c.model_dump() for c in explanation["contradictions"]],
            "verification_checklist": explanation["verification_checklist"],
        }
        print(json.dumps(result, indent=2))
        print(f"  ({elapsed:.2f}s)")


if __name__ == "__main__":
    main()
