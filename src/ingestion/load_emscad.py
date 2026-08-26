"""
Stage 1 — Data ingestion & preprocessing
==========================================
An Explainable Credibility Scoring Framework for Online Recruitment Posts
O.K. Samarasinghe — COBSCCOMP242P-069

PURPOSE
    Load the raw EMSCAD CSV and apply every Stage 1 rule fixed by the data audit
    (2026-08-27) and the project guardrails (build.md section 5).

RULES APPLIED, IN ORDER (see docstrings on each function for the "why"):
    1. Map 't'/'f' string literals to 1/0 for the five boolean columns.
    2. Extract E2 contact/media tokens BEFORE any HTML stripping (Guardrail 7).
    3. Drop `in_balanced_dataset` (Guardrail 6 — leakage risk).
    4. Treat salary_range == "0-0" as missing, not a real value.
    5. Flag missingness per structured field. NEVER impute (Guardrail 8) —
       missingness is itself the E3 signal.

THIS MODULE DOES NOT:
    - Strip HTML from text (that's a later, separate step — E1 feature extraction)
    - Extract E1/E3/E4 features (Stage 4)
    - Split the data (Stage 3 — blocked on Decision 0.2)

DEFINITION OF DONE (per workplan.md):
    Reloading via this module must reproduce the audit's measured numbers exactly:
    17,880 rows; 866 fraud / 17,014 legit; token counts 7,362 / 1,377 / 657 postings
    for URL / EMAIL / PHONE. See tests/test_load_emscad.py.
"""

import re
import pandas as pd
import numpy as np

# ----------------------------------------------------------------------------
# Column groups (mirrors emscad_audit_fixed.py so ingestion and audit never drift)
# ----------------------------------------------------------------------------

BOOL_COLS = ["telecommuting", "has_company_logo", "has_questions",
             "fraudulent", "in_balanced_dataset"]

TEXT_COLS = ["title", "company_profile", "description", "requirements", "benefits"]

# The nine E3 completeness fields (telecommuting is boolean and always present,
# so it is not part of the completeness signal — see decisions.md).
STRUCT_COLS = ["department", "salary_range", "employment_type", "required_experience",
               "required_education", "industry", "function",
               "has_company_logo", "has_questions"]

# Token patterns — identical to the audit script. Any change here must be made
# in both places, or ingestion and the audit will silently disagree.
TOKEN_PATTERNS = {
    "url_token_count":   re.compile(r"#URL_[0-9a-fA-F]+#"),
    "email_token_count": re.compile(r"#EMAIL_[0-9a-fA-F]+#"),
    "phone_token_count": re.compile(r"#PHONE_[0-9a-fA-F]+#"),
}

TOKEN_SEARCH_COLS = ["description", "requirements", "benefits", "company_profile"]


def _to_int(series: pd.Series) -> pd.Series:
    """Map t/f (and common alternate encodings, defensively) onto 1/0."""
    m = {"t": 1, "f": 0, "T": 1, "F": 0, "1": 1, "0": 0,
         "true": 1, "false": 0, "True": 1, "False": 0}
    return series.map(lambda x: m.get(str(x).strip(), np.nan))


def load_raw(path: str) -> pd.DataFrame:
    """
    Load the CSV with the exact same read_csv arguments as the audit script.
    dtype=str keeps every field as text until we explicitly convert it — this
    avoids pandas silently inferring types (e.g. turning a numeric-looking
    salary_range into a float and losing the "0-0" placeholder string).
    """
    df = pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[""])
    return df


def encode_booleans(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rule 1 (Stage 1 ordering constraint #1): map t/f to 1/0 for all five boolean
    columns, and ASSERT the fraud count is exactly 866 before proceeding — if it
    isn't, something about the input file has changed and every downstream
    number would be silently wrong.
    """
    df = df.copy()
    for col in BOOL_COLS:
        if col in df.columns:
            df[col] = _to_int(df[col])

    n_fraud = int(df["fraudulent"].sum())
    if n_fraud != 866:
        raise ValueError(
            f"Fraud count assertion failed: expected 866, got {n_fraud}. "
            f"Do not proceed — the input file does not match the audited dataset."
        )
    return df


def extract_contact_tokens(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rule 2 / Guardrail 7: extract #EMAIL_#/#PHONE_#/#URL_# token counts from the
    RAW text columns, before any HTML stripping happens anywhere in the pipeline.
    This function must run before any function that touches markup — reversing
    the order silently destroys the entire E2 token signal.

    Adds one integer column per token type, counting occurrences per posting
    across description + requirements + benefits + company_profile (matching
    the audit script's search scope).
    """
    df = df.copy()
    search_cols = [c for c in TOKEN_SEARCH_COLS if c in df.columns]
    blob = df[search_cols].fillna("").agg(" ".join, axis=1)

    for out_col, pattern in TOKEN_PATTERNS.items():
        df[out_col] = blob.str.count(pattern)

    return df


def drop_leakage_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rule 3 / Guardrail 6: in_balanced_dataset flags the dataset authors' OWN
    train/test subset choice. Using it as a feature would leak that choice into
    the model. Drop it entirely, unconditionally.
    """
    df = df.copy()
    if "in_balanced_dataset" in df.columns:
        df = df.drop(columns=["in_balanced_dataset"])
    return df


def normalise_salary_placeholder(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rule 4: salary_range == "0-0" is a placeholder meaning "not provided", not a
    real salary of zero to zero. Convert it to NaN so downstream missingness
    logic (Rule 5) treats it correctly.
    """
    df = df.copy()
    if "salary_range" in df.columns:
        df["salary_range"] = df["salary_range"].replace("0-0", np.nan)
    return df


def flag_missingness(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rule 5 / Guardrail 8: add one boolean "_missing" flag column per structured
    field. NEVER impute a value into the original column — missingness is the
    E3 signal itself, not noise to be cleaned away.

    Two of the nine STRUCT_COLS (has_company_logo, has_questions) are boolean
    fields already converted to integer 0/1 by encode_booleans() earlier in the
    pipeline, so they have no string representation to strip. The audit
    measured both at 0% missing — real values only, never null — so their flag
    is simply isna(), consistent with every other numeric column. All other
    STRUCT_COLS remain plain text at this point and use the string-based check.
    """
    df = df.copy()
    for col in STRUCT_COLS:
        if col not in df.columns:
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col + "_missing"] = df[col].isna()
        else:
            df[col + "_missing"] = df[col].isna() | (df[col].fillna("").str.strip() == "")
    return df


def load_emscad(path: str) -> pd.DataFrame:
    """
    Full Stage 1 pipeline, in the mandatory order:
      1. load raw
      2. extract contact tokens (BEFORE anything touches markup)
      3. encode booleans + assert fraud count
      4. drop in_balanced_dataset
      5. normalise the salary_range placeholder
      6. flag missingness (never impute)

    Note tokens are extracted (step 2) before booleans are encoded (step 3) —
    order between those two doesn't matter for correctness, but token
    extraction must never move after any HTML-stripping step introduced later
    in the pipeline (that stripping does not happen in this module at all).
    """
    df = load_raw(path)
    df = extract_contact_tokens(df)
    df = encode_booleans(df)
    df = drop_leakage_columns(df)
    df = normalise_salary_placeholder(df)
    df = flag_missingness(df)
    return df


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "DataSet.csv"
    result = load_emscad(path)
    print(f"Loaded {len(result):,} rows, {len(result.columns)} columns")
    print(f"Fraud: {int(result['fraudulent'].sum()):,} / "
          f"Legit: {int((result['fraudulent'] == 0).sum()):,}")
    print(f"in_balanced_dataset present: {'in_balanced_dataset' in result.columns}")
    print(f"Token postings — URL: {int((result['url_token_count'] > 0).sum()):,}, "
          f"EMAIL: {int((result['email_token_count'] > 0).sum()):,}, "
          f"PHONE: {int((result['phone_token_count'] > 0).sum()):,}")
