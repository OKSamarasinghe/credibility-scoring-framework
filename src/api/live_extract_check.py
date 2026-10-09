"""
Live extraction check — real HTTP requests to a running server's new /extract-url route,
against real external job-posting URLs.

WHY THIS EXISTS, AND WHY CLAUDE COULD NOT RUN IT
    Every fetch tool available to Claude in its own sandbox (and in the separate Linux VM
    used to edit this project's files) is itself blocked by an outbound proxy from
    reaching arbitrary external websites -- a direct test against ikman.lk failed
    identically in both with "Tunnel connection failed: 403 Forbidden". That means the
    /extract-url route's logic (domain exclusion, robots.txt check, trafilatura wiring)
    was tested with mocked network calls (see test_new_routes.py, run in Claude's sandbox,
    11/11 checks passed) but its REAL behaviour against REAL websites was never executed
    end-to-end by Claude. Only this machine -- with normal, unrestricted internet access
    -- can do that. This script is that real check, mirroring live_api_check.py's existing
    pattern for the same reason: a result Claude could reason about but not personally
    witness.

WHAT "PASS" MEANS HERE
    This is NOT a claim that every URL should succeed. Some are expected to be rejected
    on purpose (LinkedIn, topjobs.lk) -- that is correct behaviour, not a bug. "Pass" means
    each URL's outcome matches what we predicted it would be. A URL in the "uncertain"
    group (xpress.jobs) succeeding OR failing are both acceptable outcomes -- only report
    it as broken if it returns a 500 (an unhandled server error) rather than a clean 4xx/
    5xx with a readable message.

USAGE
    Terminal 1:  uvicorn src.api.main:app --reload
    Terminal 2:  python -m src.api.live_extract_check
"""
import sys

import requests

BASE_URL = "http://127.0.0.1:8000"

# Expected outcome per URL, decided BEFORE running this (see decisions.md, 2026-10-09):
#   "extract"   -> expect a 200 with usable text
#   "excluded"  -> expect a 4xx with a clear "cannot fetch this site" message
#                  (hardcoded exclusion for LinkedIn, or robots.txt disallow for
#                  topjobs.lk -- either is correct, both land here as "handled, not a bug")
#   "uncertain" -> no prediction either way; just must not be a raw 500
#
# IMPORTANT: these are ILLUSTRATIVE PLACEHOLDERS, not the real URLs. Replace each one
# below with the actual 6 URLs you have (the ikman.lk x2, rooster.jobs, linkedin.com,
# topjobs.lk, and xpress.jobs postings) before running this -- Claude does not have your
# exact URLs saved verbatim and will not fabricate ones that look real.
CASES = [
    ("https://ikman.lk/REPLACE-WITH-YOUR-FIRST-REAL-URL", "extract"),
    ("https://ikman.lk/REPLACE-WITH-YOUR-SECOND-REAL-URL", "extract"),
    ("https://rooster.jobs/REPLACE-WITH-YOUR-REAL-URL", "extract"),
    ("https://www.linkedin.com/REPLACE-WITH-YOUR-REAL-URL", "excluded"),
    ("https://www.topjobs.lk/REPLACE-WITH-YOUR-REAL-URL", "excluded"),
    ("https://xpress.jobs/REPLACE-WITH-YOUR-REAL-URL", "uncertain"),
]


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

    print()
    print("IMPORTANT: replace the placeholder URLs in CASES (this file) with your own 6 "
          "real job-posting URLs before trusting these results -- the ones committed here "
          "are examples only, not necessarily still-live postings.\n")

    all_ok = True
    for url, expectation in CASES:
        print(f"=== {url}  (expected: {expectation}) ===")
        try:
            resp = requests.post(f"{BASE_URL}/extract-url", json={"url": url}, timeout=30)
        except Exception as e:
            print(f"  REQUEST FAILED: {e}")
            all_ok = False
            continue

        print(f"  HTTP {resp.status_code}")
        if resp.status_code >= 500:
            print(f"  SERVER ERROR (unexpected regardless of category): {resp.text[:300]}")
            all_ok = False
            continue

        try:
            body = resp.json()
        except Exception:
            print(f"  Non-JSON response: {resp.text[:300]}")
            all_ok = False
            continue

        if resp.status_code == 200:
            text_preview = (body.get("text") or "")[:160].replace("\n", " ")
            print(f"  title: {body.get('title')!r}")
            print(f"  text preview: {text_preview!r}")
            if expectation == "excluded":
                print("  NOTE: expected this one to be excluded, but it succeeded. "
                      "Not necessarily wrong -- just re-check which category it should be in.")
        else:
            print(f"  detail: {body.get('detail')}")

        print()

    print("=" * 70)
    print("No raw 500s or unreachable-server errors." if all_ok
          else "Some requests failed outright (see REQUEST FAILED / SERVER ERROR above) "
               "-- investigate before trusting this feature.")
    print("Read each case above yourself: a 4xx with a clear message is success for an "
          "'excluded' case, not a failure.")
    print("=" * 70)
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
