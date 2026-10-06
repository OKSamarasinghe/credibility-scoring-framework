"""
Tier 2 legitimate-posting sourcing — Greenhouse + Lever public job-board APIs.

Both APIs are public, unauthenticated, intended for embedding job boards on
company websites, and are documented as such by the vendors themselves. This
is API access, not scraping, and was already logged as verified on 2026-09-20
(decisions.md). Confirmed live tonight (2026-10-07) against the real
Greenhouse endpoint for "airbnb" with content=true.

HOW THIS WORKS
    1. Try every candidate slug against both platforms.
    2. Keep only the slugs that actually respond with job listings — most
       guessed slugs will 404, and that's expected and fine. This script
       does NOT assume any specific slug is correct; it finds out by asking.
    3. Cap postings-per-company so Tier 2 isn't dominated by one company's
       boilerplate style (diversity matters more than volume here).
    4. Normalise into a schema aligned with EMSCAD's columns where a field
       exists, leaving it explicitly null (not fabricated) where the API
       doesn't provide an equivalent. Stage 4 (E1–E4 extraction) runs on
       this output later — this script's only job is honest, provenance-
       tagged acquisition.
    5. Every record is tagged with source platform, company slug, source
       URL, and retrieval timestamp — required for the provenance record
       Decision log / Day-1 plan calls for.

WHAT THIS DOES NOT DO
    - It does not source the fraud-side Tier 2 postings. That's a separate,
      harder problem (documented scam repositories/advisories), not a public
      JSON API, and needs to happen as its own step with its own provenance
      trail — see tier2_fraud_sourcing notes (not yet built).
    - It does not touch EMSCAD, training, or any Tier 1 data.
    - It does not merge into Tier 1 at any point (never allowed — see
      decisions.md, 2026-08-07).

USAGE
    python -m src.ingestion.tier2_sourcing

OUTPUT
    data/raw/tier2/tier2_legit_raw.jsonl   (gitignored — raw data, like Tier 1)
    reports/tier2_sourcing_summary.json    (committed — per-slug status, counts)
"""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Candidate slugs. These are good-faith guesses from general knowledge of
# which companies use Greenhouse or Lever for their public job boards — NOT
# verified in advance. The script finds out which ones are real by calling
# the API. A 404 here is normal and expected, not an error in this script.
# ---------------------------------------------------------------------------

GREENHOUSE_CANDIDATES = [
    "airbnb", "doordash", "robinhood", "coinbase", "stripe", "figma",
    "asana", "webflow", "canva", "brex", "plaid", "rippling", "vercel",
    "discord", "pinterest", "lyft", "reddit", "squarespace", "gitlab",
    "docker", "elastic", "mongodb", "twilio", "okta", "datadog",
    "cloudflare", "snowflake", "affirm", "chime", "flexport",
]

LEVER_CANDIDATES = [
    "netflix", "box", "eventbrite", "shopify", "yelp", "attentive",
    "carta", "chime", "ro", "ironclad", "ethos", "github", "zocdoc",
    "lever", "palantir", "lyft", "zillow", "scaleai", "scale",
    "glossier", "instacart", "postmates", "patreon", "wish",
    "betterup", "whoop", "ramp", "mercury", "deel", "clari",
]

PER_COMPANY_CAP = 5  # diversity over volume
TARGET_TOTAL = 50
REQUEST_TIMEOUT = 15
SLEEP_BETWEEN_CALLS = 0.5  # be a polite API citizen

OUT_DIR = Path("data/raw/tier2")
REPORT_DIR = Path("reports")
OUT_FILE = OUT_DIR / "tier2_legit_raw.jsonl"
SUMMARY_FILE = REPORT_DIR / "tier2_sourcing_summary.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _strip_html(html: str) -> str:
    """Minimal tag stripper — good enough for a readable text field here.
    Stage 1's real HTML handling (src/ingestion) is the authoritative version
    used downstream; this is just for a human-readable raw capture."""
    if not html:
        return ""
    import re
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def fetch_greenhouse(slug: str):
    """Returns (status, list_of_raw_jobs) where status is 'ok', 'not_found',
    or 'error:<detail>'."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as exc:
        return f"error:{exc}", []
    if resp.status_code == 404:
        return "not_found", []
    if resp.status_code != 200:
        return f"error:http_{resp.status_code}", []
    try:
        data = resp.json()
    except ValueError:
        return "error:bad_json", []
    jobs = data.get("jobs", [])
    return "ok", jobs


def fetch_lever(slug: str):
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as exc:
        return f"error:{exc}", []
    if resp.status_code == 404:
        return "not_found", []
    if resp.status_code != 200:
        return f"error:http_{resp.status_code}", []
    try:
        data = resp.json()
    except ValueError:
        return "error:bad_json", []
    if not isinstance(data, list):
        return "error:unexpected_shape", []
    return "ok", data


def normalise_greenhouse(job: dict, slug: str) -> dict:
    location_name = None
    if isinstance(job.get("location"), dict):
        location_name = job["location"].get("name")

    return {
        # EMSCAD-aligned fields (null where the API gives no equivalent —
        # NOT imputed, per guardrail 8: missingness is itself the E3 signal)
        "title": job.get("title"),
        "location": location_name,
        "department": None,
        "salary_range": None,
        "company_profile": None,
        "description": _strip_html(job.get("content", "")),
        "requirements": None,
        "benefits": None,
        "telecommuting": None,  # Stage 4 infers this from text/location, not guessed here
        "has_company_logo": None,
        "has_questions": None,
        "employment_type": None,
        "required_experience": None,
        "required_education": None,
        "industry": None,
        "function": None,
        "fraudulent": 0,  # Tier 2 legit-side by construction of this script
        # Provenance (required — Day 1 plan)
        "source_platform": "greenhouse",
        "source_company_slug": slug,
        "source_company_name": job.get("company_name"),
        "source_url": job.get("absolute_url"),
        "source_job_id": job.get("id"),
        "retrieved_at": _now(),
    }


def normalise_lever(job: dict, slug: str) -> dict:
    categories = job.get("categories", {}) or {}
    return {
        "title": job.get("text"),
        "location": categories.get("location"),
        "department": categories.get("team"),
        "salary_range": None,
        "company_profile": None,
        "description": job.get("descriptionPlain") or _strip_html(job.get("description", "")),
        "requirements": None,
        "benefits": None,
        "telecommuting": None,
        "has_company_logo": None,
        "has_questions": None,
        "employment_type": categories.get("commitment"),
        "required_experience": None,
        "required_education": None,
        "industry": None,
        "function": None,
        "fraudulent": 0,
        "source_platform": "lever",
        "source_company_slug": slug,
        "source_company_name": slug,
        "source_url": job.get("hostedUrl"),
        "source_job_id": job.get("id"),
        "retrieved_at": _now(),
    }


def run():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    records = []
    per_slug_status = {}

    for slug in GREENHOUSE_CANDIDATES:
        status, jobs = fetch_greenhouse(slug)
        kept = 0
        if status == "ok":
            for job in jobs[:PER_COMPANY_CAP]:
                records.append(normalise_greenhouse(job, slug))
                kept += 1
        per_slug_status[f"greenhouse:{slug}"] = {"status": status, "available": len(jobs), "kept": kept}
        time.sleep(SLEEP_BETWEEN_CALLS)

    for slug in LEVER_CANDIDATES:
        status, jobs = fetch_lever(slug)
        kept = 0
        if status == "ok":
            for job in jobs[:PER_COMPANY_CAP]:
                records.append(normalise_lever(job, slug))
                kept += 1
        per_slug_status[f"lever:{slug}"] = {"status": status, "available": len(jobs), "kept": kept}
        time.sleep(SLEEP_BETWEEN_CALLS)

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    ok_slugs = {k: v for k, v in per_slug_status.items() if v["status"] == "ok"}
    summary = {
        "run_at": _now(),
        "total_candidates_tried": len(GREENHOUSE_CANDIDATES) + len(LEVER_CANDIDATES),
        "slugs_that_responded": len(ok_slugs),
        "total_postings_collected": len(records),
        "target_total": TARGET_TOTAL,
        "target_met": len(records) >= TARGET_TOTAL,
        "per_company_cap": PER_COMPANY_CAP,
        "per_slug_status": per_slug_status,
    }

    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(json.dumps(summary, indent=2))
    print(f"\nWritten: {OUT_FILE} (gitignored), {SUMMARY_FILE}")
    return summary


if __name__ == "__main__":
    run()
