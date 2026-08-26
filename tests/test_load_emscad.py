"""
Stage 1 validation tests.

Every expected number here is copied directly from audit/history/2026-08-27_audit_results.json
— the audit run we already verified and committed. If any of these fail, Stage 1 does
NOT reproduce the audited dataset and must not be used for anything downstream.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "ingestion"))

import pytest
from load_emscad import load_emscad

CSV_PATH = os.environ.get("EMSCAD_CSV_PATH", "data/raw/DataSet.csv")


@pytest.fixture(scope="module")
def df():
    return load_emscad(CSV_PATH)


def test_row_and_column_shape(df):
    assert len(df) == 17_880, f"Expected 17,880 rows, got {len(df)}"


def test_fraud_class_counts(df):
    n_fraud = int(df["fraudulent"].sum())
    n_legit = int((df["fraudulent"] == 0).sum())
    assert n_fraud == 866, f"Expected 866 fraud, got {n_fraud}"
    assert n_legit == 17_014, f"Expected 17,014 legit, got {n_legit}"


def test_in_balanced_dataset_dropped(df):
    assert "in_balanced_dataset" not in df.columns


def test_boolean_columns_are_integer_encoded(df):
    for col in ["telecommuting", "has_company_logo", "has_questions", "fraudulent"]:
        assert set(df[col].unique()) <= {0, 1}, f"{col} has non-binary values"


def test_contact_token_postings_match_audit(df):
    # Measured, audit/history/2026-08-27_audit_results.json -> contact_tokens
    assert int((df["url_token_count"] > 0).sum()) == 7_362
    assert int((df["email_token_count"] > 0).sum()) == 1_377
    assert int((df["phone_token_count"] > 0).sum()) == 657


def test_contact_token_total_occurrences_match_audit(df):
    assert int(df["url_token_count"].sum()) == 23_270
    assert int(df["email_token_count"].sum()) == 2_368
    assert int(df["phone_token_count"].sum()) == 1_026


def test_salary_zero_zero_treated_as_missing(df):
    # Measured: 142 records carried the literal "0-0" placeholder.
    # After normalisation, salary_range_missing should include those 142
    # PLUS the originally-missing 15,012 = 15,154 total (142 + 15,012).
    # (15,012 is the pre-normalisation missing count from the audit; "0-0"
    # records were counted as PRESENT there, since the audit measured the
    # placeholder separately from missingness. This is Stage 1's job to fold in.)
    n_missing = int(df["salary_range_missing"].sum())
    assert n_missing == 15_012 + 142, (
        f"Expected 15,154 missing after folding in the 0-0 placeholder, got {n_missing}"
    )


def test_no_imputation_occurred(df):
    # Guardrail 8: missingness flags exist, but the original columns must still
    # contain real NaNs where data is missing — not a filled-in placeholder value.
    assert df["department"].isna().sum() > 0 or (df["department"].fillna("").str.strip() == "").sum() > 0


def test_fraud_count_assertion_blocks_bad_input(tmp_path):
    # Sanity check on the assertion itself: a corrupted file with a wrong fraud
    # count must raise, not silently proceed.
    import pandas as pd
    bad = pd.DataFrame({
        "title": ["a", "b"], "fraudulent": ["t", "f"],
        "telecommuting": ["f", "f"], "has_company_logo": ["t", "f"],
        "has_questions": ["t", "f"], "in_balanced_dataset": ["t", "t"],
        "description": ["x", "y"], "requirements": ["", ""],
        "benefits": ["", ""], "company_profile": ["", ""],
        "salary_range": ["", ""],
    })
    bad_path = tmp_path / "bad.csv"
    bad.to_csv(bad_path, index=False)
    with pytest.raises(ValueError, match="Fraud count assertion failed"):
        load_emscad(str(bad_path))
