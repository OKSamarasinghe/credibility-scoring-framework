"""
Stage 2 — Stratified sampling for the manual taxonomy-validation audit (O1)
=============================================================================
An Explainable Credibility Scoring Framework for Online Recruitment Posts
O.K. Samarasinghe — COBSCCOMP242P-069

PURPOSE
    Draw a reproducible 200-posting sample (100 fraudulent / 100 legitimate)
    for MANUAL audit, and produce a worksheet ready for a human coder to fill in.

WHY UNIQUE-NORMALISED-DESCRIPTIONS ONLY
    The data audit (2026-08-27) measured entire near-duplicate campaigns of
    20+ postings sharing near-identical text. Sampling from the raw corpus
    could pull in several copies of the same underlying posting, letting one
    posting's manual judgement count multiple times and silently inflating
    the audit's apparent agreement rate. Sampling from unique normalised
    descriptions (14,375 available per the audit) avoids this without
    requiring Decision 0.2 (the full near-duplicate grouping policy for
    Stage 3) to be resolved first — this is a narrower, self-contained fix.

WHAT THIS SCRIPT PRE-FILLS, AND WHY THAT'S HONEST
    Two kinds of column go into the worksheet:
      - MECHANICAL columns (field presence, provisional-pattern evaluability):
        these are facts about the data, not judgement calls, so the script
        fills them in. They reuse the same provisional patterns from the
        audit script (REMOTE/ONSITE/PARTTIME/YEARS/EDU/MONEY) — labelled
        clearly as "reference only, provisional" per decisions.md 0.1.
      - MANUAL JUDGEMENT columns (does a human reader consider this a genuine
        contradiction?): these are left BLANK. Filling them is Stage 2's
        actual audit work and cannot be automated without invalidating O1.

KNOWN DUPLICATION TO RESOLVE AT STAGE 4
    The normalise() function and the C1-C6 provisional patterns below are
    copied from audit/emscad_audit_fixed.py, not imported from it (that
    script executes top-level logic on import, so importing it would be
    unsafe). Keep the two in sync manually until Stage 4 builds the real,
    canonical lexicon module and this duplication is retired.

OUTPUT
    reports/stage2_manual_audit_worksheet.csv — one row per sampled posting.
    reports/stage2_sample_manifest.json — the exact posting indices sampled,
    the seed used, and summary counts, so the sample is fully reproducible
    and auditable independent of the CSV.
"""

import re
import json
import hashlib
import sys
import pandas as pd
import numpy as np

# ----------------------------------------------------------------------------
# Sampling parameters — DECIDED AND FIXED. Log in decisions.md if changed.
# ----------------------------------------------------------------------------
SAMPLE_SIZE_PER_CLASS = 100      # 100 fraud + 100 legit = 200 total
RANDOM_SEED = 42                 # fixed for reproducibility; report this seed

# ----------------------------------------------------------------------------
# Text normalisation — copied from audit/emscad_audit_fixed.py (kept identical)
# ----------------------------------------------------------------------------

def normalise(s):
    s = str(s or "")
    s = re.sub(r"<[^>]+>", " ", s)                 # strip markup
    s = re.sub(r"#[A-Z_]+_[0-9a-fA-F]+#", " ", s)  # strip anonymisation tokens
    s = s.lower()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def strip_html_for_display(s):
    """Light HTML stripping for the human-readable snippet column only —
    NOT the same as normalise(), which is for hashing/deduplication."""
    s = str(s or "")
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


# ----------------------------------------------------------------------------
# Provisional patterns — copied from audit/emscad_audit_fixed.py (reference only)
# ----------------------------------------------------------------------------
REMOTE = re.compile(r"\b(?:work from home|remote|telecommut|home based|home-based|virtual office|anywhere)\b")
ONSITE = re.compile(r"\b(?:on site|onsite|in office|in-office|in person|relocat|commute|our office|headquarters|must be located|based in our)\b")
ARRANGEMENT = re.compile(REMOTE.pattern + "|" + ONSITE.pattern)
PARTTIME = re.compile(r"\b(?:part time|parttime|part-time|contract|temporary|freelance|internship)\b")
YEARS = re.compile(r"\b\d{1,2}\s*\+?\s*(?:or more\s*)?year")
EDU = re.compile(r"\b(?:degree|diploma|bachelor|master|phd|graduate|qualification|certificat)\b")
MONEY = re.compile(r"(?:\$|usd|eur|gbp|salary|per month|per year|per annum|monthly|annually)")

def _field_str(row, key):
    """NaN-safe field access.

    pandas can store a genuinely blank cell as a float NaN even when the
    CSV is loaded with dtype=str and na_values=[""] -- the column still
    exists, so row.get(key, "") returns that NaN itself rather than the
    default ("" is only used when the KEY is missing). str(NaN) is then the
    non-empty string "nan", which silently defeats a `!= ""` presence
    check and makes a genuinely blank field read as "present". Discovered
    2026-10-07 when the Stage 2 coding tool asked the student to judge
    C3/C4/C5 contradictions on postings where those fields were actually
    blank (decisions.md). Route every field-presence check through this
    helper instead of `str(row.get(key, "") or "").strip()`.
    """
    v = row.get(key)
    if v is None:
        return ""
    try:
        if pd.isna(v):
            return ""
    except (TypeError, ValueError):
        pass
    return str(v).strip()


def build_sample(csv_path: str, seed: int = RANDOM_SEED, n_per_class: int = SAMPLE_SIZE_PER_CLASS):
    df = pd.read_csv(csv_path, dtype=str, keep_default_na=False, na_values=[""])
    df["fraudulent_i"] = df["fraudulent"].map({"t": 1, "f": 0})

    # Deduplicate by normalised description BEFORE sampling.
    df["_norm_hash"] = df["description"].fillna("").map(normalise).map(
        lambda t: hashlib.md5(t.encode()).hexdigest()
    )
    deduped = df.drop_duplicates(subset="_norm_hash", keep="first").copy()

    n_fraud_available = int((deduped["fraudulent_i"] == 1).sum())
    n_legit_available = int((deduped["fraudulent_i"] == 0).sum())
    if n_fraud_available < n_per_class:
        raise ValueError(
            f"Only {n_fraud_available} unique fraudulent postings available, "
            f"need {n_per_class}. Reduce n_per_class or revisit the sampling design."
        )

    fraud_sample = deduped[deduped["fraudulent_i"] == 1].sample(
        n=n_per_class, random_state=seed
    )
    legit_sample = deduped[deduped["fraudulent_i"] == 0].sample(
        n=n_per_class, random_state=seed
    )
    sample = pd.concat([fraud_sample, legit_sample]).sample(
        frac=1, random_state=seed  # shuffle so fraud/legit aren't in visible blocks
    ).reset_index(drop=False)  # keep original CSV row index as 'index' column

    return sample, {
        "n_fraud_available_after_dedup": n_fraud_available,
        "n_legit_available_after_dedup": n_legit_available,
        "n_unique_after_dedup": int(len(deduped)),
        "n_total_before_dedup": int(len(df)),
    }


def build_worksheet(sample: pd.DataFrame) -> pd.DataFrame:
    """One row per sampled posting. Mechanical columns pre-filled; manual
    judgement columns left blank for the human coder."""
    body = sample[["description", "requirements", "benefits"]].fillna("").agg(" ".join, axis=1)
    body_norm = body.map(normalise)
    desc_norm = sample["description"].fillna("").map(normalise)

    rows = []
    for i, (_, r) in enumerate(sample.iterrows()):
        row = {
            "sample_id": f"S{i+1:03d}",
            "original_csv_index": r["index"],
            "fraudulent": "fraud" if r["fraudulent_i"] == 1 else "legit",
            "title": r["title"],
            "description_snippet": strip_html_for_display(r["description"])[:400],

            # --- Manual judgement: overall taxonomy observability (O1) ---
            # Fill Y / N / PARTIAL for each. See STAGE2_CODING_INSTRUCTIONS.md.
            "E1_observable_MANUAL": "",
            "E2_observable_MANUAL": "",
            "E3_observable_MANUAL": "",
            "E4_observable_MANUAL": "",
        }

        # --- C1: telecommuting vs remote/on-site language ---
        row["C1_field_present"] = "Y"  # telecommuting is always present (boolean)
        row["C1_pattern_evaluable_REFERENCE_ONLY"] = "Y" if bool(re.search(ARRANGEMENT, desc_norm.iloc[i])) else "N"
        row["C1_manual_contradiction_MANUAL"] = ""  # Y / N / NA

        # --- C2: location vs location named in description ---
        loc = _field_str(r, "location")
        has_city = len(loc.split(",")) >= 3 and loc.split(",")[2].strip() != ""
        row["C2_field_present"] = "Y" if (loc != "" and has_city) else "N"
        row["C2_pattern_evaluable_REFERENCE_ONLY"] = "NOT MEASURED (deferred, see decisions.md)"
        row["C2_manual_contradiction_MANUAL"] = ""

        # --- C3: employment_type vs arrangement language ---
        et = _field_str(r, "employment_type")
        row["C3_field_present"] = "Y" if et != "" else "N"
        row["C3_pattern_evaluable_REFERENCE_ONLY"] = "Y" if bool(re.search(PARTTIME, body_norm.iloc[i])) else "N"
        row["C3_manual_contradiction_MANUAL"] = ""

        # --- C4: required_experience vs "N years" ---
        re_exp = _field_str(r, "required_experience")
        row["C4_field_present"] = "Y" if re_exp != "" else "N"
        row["C4_pattern_evaluable_REFERENCE_ONLY"] = "Y" if bool(re.search(YEARS, body_norm.iloc[i])) else "N"
        row["C4_manual_contradiction_MANUAL"] = ""

        # --- C5: required_education vs qualification words ---
        re_edu = _field_str(r, "required_education")
        row["C5_field_present"] = "Y" if re_edu != "" else "N"
        row["C5_pattern_evaluable_REFERENCE_ONLY"] = "Y" if bool(re.search(EDU, body_norm.iloc[i])) else "N"
        row["C5_manual_contradiction_MANUAL"] = ""

        # --- C6: salary_range vs money figures ---
        sr = _field_str(r, "salary_range")
        sr_usable = bool(re.match(r"^\s*\d+\s*-\s*\d+\s*$", sr)) and sr != "0-0"
        row["C6_field_present"] = "Y" if sr_usable else "N"
        row["C6_pattern_evaluable_REFERENCE_ONLY"] = "Y" if bool(re.search(MONEY, body_norm.iloc[i])) else "N"
        row["C6_manual_contradiction_MANUAL"] = ""

        row["notes_MANUAL"] = ""
        rows.append(row)

    return pd.DataFrame(rows)


if __name__ == "__main__":
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "data/raw/DataSet.csv"

    sample, stats = build_sample(csv_path)
    worksheet = build_worksheet(sample)

    worksheet.to_csv("reports/stage2_manual_audit_worksheet.csv", index=False)

    manifest = {
        "seed": RANDOM_SEED,
        "n_per_class": SAMPLE_SIZE_PER_CLASS,
        "sampled_original_indices": sorted(int(x) for x in sample["index"].tolist()),
        **stats,
    }
    with open("reports/stage2_sample_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Sampled {len(worksheet)} postings "
          f"({(worksheet['fraudulent'] == 'fraud').sum()} fraud / "
          f"{(worksheet['fraudulent'] == 'legit').sum()} legit)")
    print(f"Drawn from {stats['n_unique_after_dedup']:,} unique normalised "
          f"descriptions (of {stats['n_total_before_dedup']:,} total records)")
    print(f"Seed: {RANDOM_SEED}")
    print("Written: reports/stage2_manual_audit_worksheet.csv, "
          "reports/stage2_sample_manifest.json")
