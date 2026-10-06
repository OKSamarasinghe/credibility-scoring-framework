"""
Tests for Stage 3 — leakage-controlled partitioning.

Run against the real EMSCAD CSV (same convention as tests/test_load_emscad.py):
default path is the EMSCAD_CSV_PATH env var, falling back to data/raw/DataSet.csv.
"""
import os

import pytest

from src.ingestion.load_emscad import load_emscad
from src.partitioning.split_data import (
    SPLIT_SEED,
    compute_groups,
    group_aware_stratified_split,
    grouping_report,
    run,
    verify_split,
)

CSV_PATH = os.environ.get("EMSCAD_CSV_PATH", "data/raw/DataSet.csv")


@pytest.fixture(scope="module")
def df():
    return load_emscad(CSV_PATH)


@pytest.fixture(scope="module")
def group_id(df):
    return compute_groups(df)


@pytest.fixture(scope="module")
def split(df, group_id):
    return group_aware_stratified_split(df, group_id)


def test_every_row_has_a_group(df, group_id):
    assert group_id.notna().all()
    assert len(group_id) == len(df)


def test_grouping_report_sane(df, group_id):
    report = grouping_report(df, group_id)
    assert report["n_rows"] == 17880
    # Description-hash-only grouping should reproduce the already-verified August audit
    # figure almost exactly (sources.md #5: 4,762 records / 26.6%). A tight tolerance
    # catches a regression (e.g. the title-hash over-merging bug found 2026-10-06, which
    # produced 10,134 — a completely different order of result) without being brittle
    # over a handful of records from minor implementation differences.
    assert abs(report["records_in_duplicate_group"] - 4762) <= 50


def test_zero_group_overlap(df, group_id, split):
    result = verify_split(df, group_id, split)
    assert result["zero_group_overlap"] is True
    assert result["n_crossing_groups"] == 0


def test_all_rows_assigned(df, group_id, split):
    result = verify_split(df, group_id, split)
    assert result["all_rows_assigned"] is True


def test_fraud_count_conserved(df, group_id, split):
    result = verify_split(df, group_id, split)
    assert result["fraud_total_conserved"] is True
    assert sum(result["fraud_counts"].values()) == 866


def test_split_fractions_close_to_target(df, group_id, split):
    result = verify_split(df, group_id, split)
    fracs = result["row_fractions"]
    assert abs(fracs["train"] - 0.70) < 0.03
    assert abs(fracs["val"] - 0.15) < 0.03
    assert abs(fracs["test"] - 0.15) < 0.03


def test_fraud_rate_roughly_preserved_per_partition(df, group_id, split):
    result = verify_split(df, group_id, split)
    for name in ("train", "val", "test"):
        pct = result["fraud_pct"][name]
        assert pct is not None
        # Overall rate is 4.84%. A wider band is allowed here because group-aware
        # splitting can't hit stratification exactly — whole groups move together.
        assert 2.0 <= pct <= 9.0


def test_reproducible_with_fixed_seed(df, group_id):
    split_a = group_aware_stratified_split(df, group_id, seed=SPLIT_SEED)
    split_b = group_aware_stratified_split(df, group_id, seed=SPLIT_SEED)
    assert (split_a == split_b).all()


def test_run_end_to_end():
    out_df, summary = run(CSV_PATH)
    assert "split" in out_df.columns
    assert "group_id" in out_df.columns
    assert summary["verification"]["zero_group_overlap"] is True
    assert summary["seed"] == SPLIT_SEED
