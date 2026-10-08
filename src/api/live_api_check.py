"""
Live API check — Stage 8b's three real-world cases, re-sent over real HTTP to a
running `/score` server, and checked against the already-verified direct-pipeline-call
results in reports/stage8b_demonstration.json.

WHY THIS EXISTS, SEPARATELY FROM stage8_smoke_test.py AND stage8b_select.py
    Both of those call pipeline.py's functions directly, in-process. Neither one ever
    goes through FastAPI's own request parsing, Pydantic validation, the actual route
    function in main.py, or a real TCP connection. This script is the first time the full
    stack is exercised as a genuinely running server receiving real HTTP requests — it
    confirms the wiring itself (request JSON -> ScoreRequest -> route -> ScoreResponse ->
    response JSON), not the pipeline logic a second time (already validated by Stage 8b).

WHAT "PASS" MEANS HERE
    Because this sends the exact same three postings Stage 8b already scored, a pass is
    "the live HTTP server reproduces the already-reported numbers exactly" — not a new
    measurement. If any number differs, that's a wiring bug (e.g. the API dropping or
    mis-mapping a field), not a model result, and must be investigated before anything is
    reported as working.

USAGE
    Terminal 1:  uvicorn src.api.main:app --reload
    Terminal 2:  python -m src.api.live_api_check
"""
import json
import sys
from pathlib import Path

import requests

BASE_URL = "http://127.0.0.1:8000"
EXPECTED_PATH = Path("reports/stage8b_demonstration.json")
TIER2_FRAUD = Path("data/raw/tier2/tier2_fraud_raw.jsonl")
TIER2_LEGIT = Path("data/raw/tier2/tier2_legit_raw.jsonl")

STRUCTURED_FIELDS = [
    "title", "company_profile", "requirements", "benefits", "location",
    "telecommuting", "has_company_logo", "has_questions", "department",
    "salary_range", "employment_type", "required_experience",
    "required_education", "industry", "function",
]


def _load_jsonl(path: Path) -> list:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def row_to_request_json(row: dict) -> dict:
    """Same field mapping as stage8b_select.record_to_request, but building a plain
    dict for requests.post() instead of a ScoreRequest object — this script never
    imports pipeline.py, deliberately, so it cannot share any in-process state with
    the server under test."""
    payload = {"text": row.get("description")}
    for f in STRUCTURED_FIELDS:
        v = row.get(f)
        if v is not None:
            payload[f] = v
    return payload


def main():
    print(f"Checking server is up at {BASE_URL} ...")
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        r.raise_for_status()
        print(f"  /health -> {r.json()}")
    except Exception as e:
        print(f"  FAILED to reach {BASE_URL}/health: {e}")
        print("  Is `uvicorn src.api.main:app --reload` running in another terminal?")
        sys.exit(1)

    expected = json.loads(EXPECTED_PATH.read_text(encoding="utf-8"))["results"]
    fraud_rows = _load_jsonl(TIER2_FRAUD)
    legit_rows = _load_jsonl(TIER2_LEGIT)

    cases = {
        "clear_fraud": fraud_rows[expected["clear_fraud"]["source_index"]],
        "ambiguous": fraud_rows[expected["ambiguous"]["source_index"]],
        "clear_legit": legit_rows[expected["clear_legit"]["source_index"]],
    }

    all_pass = True
    results = {}
    for name, row in cases.items():
        payload = row_to_request_json(row)
        print(f"\n=== {name} (source_index={expected[name]['source_index']}) ===")
        resp = requests.post(f"{BASE_URL}/score", json=payload, timeout=120)
        if resp.status_code != 200:
            print(f"  HTTP {resp.status_code}: {resp.text[:500]}")
            all_pass = False
            continue
        body = resp.json()
        exp = expected[name]
        score_match = body["credibility_score"] == exp["credibility_score"]
        band_match = body["risk_band"] == exp["risk_band"]
        print(f"  live:     credibility_score={body['credibility_score']}  risk_band={body['risk_band']}")
        print(f"  expected: credibility_score={exp['credibility_score']}  risk_band={exp['risk_band']}")
        print(f"  score match: {score_match}   risk_band match: {band_match}")
        if not (score_match and band_match):
            all_pass = False
        results[name] = {
            "live_response": body,
            "expected_score": exp["credibility_score"],
            "expected_risk_band": exp["risk_band"],
            "score_match": score_match,
            "risk_band_match": band_match,
        }

    out_path = Path("reports/stage_live_api_check_results.json")
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nWritten: {out_path}")

    print("\n" + "=" * 70)
    print("ALL CASES MATCH — live HTTP server reproduces Stage 8b's numbers exactly." if all_pass
          else "MISMATCH FOUND — see above, do not report the API as verified yet.")
    print("=" * 70)
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
