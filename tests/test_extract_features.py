"""
Tests for Stage 4 — multi-signal evidence extraction (E1-E4).

Unit tests use small constructed text, not the real EMSCAD CSV, because each covers one
rule's logic in isolation (including the four precision bugs found and fixed during the
2026-10-08 full-corpus run — see extract_features.py's inline notes at each fix site).
The end-to-end test at the bottom runs against the real CSV (same convention as
tests/test_split_data.py) as a smoke test only: it checks shape and sane bounds, not
specific figures, since the real coverage numbers belong in methodology.md, not asserted
here as if they were a fixed contract.
"""
import os

import pandas as pd
import pytest

from src.ingestion.load_emscad import load_emscad
from src.features.extract_features import (
    _c1_row,
    _c2_row,
    _c3_row,
    _c4_row,
    _c5_row,
    _c6_row,
    _norm_text,
    _years_of_experience_mentions,
    coverage_report,
    extract_all,
    extract_e3,
)

CSV_PATH = os.environ.get("EMSCAD_CSV_PATH", "data/raw/DataSet.csv")


# ---------------------------------------------------------------------------
# C1 — telecommuting vs. remote/on-site language
# ---------------------------------------------------------------------------

def test_c1_unambiguous_remote_contradicts_onsite_field():
    evaluable, contra, _ = _c1_row(0, _norm_text("This is a fully remote position."))
    assert evaluable == "Y"
    assert contra == "Y"


def test_c1_unambiguous_remote_matches_remote_field():
    evaluable, contra, _ = _c1_row(1, _norm_text("This is a fully remote position."))
    assert evaluable == "Y"
    assert contra == "N"


def test_c1_onsite_language_contradicts_remote_field():
    evaluable, contra, _ = _c1_row(1, _norm_text("You must relocate to our Chicago office."))
    assert evaluable == "Y"
    assert contra == "Y"


def test_c1_no_language_not_evaluable():
    evaluable, contra, _ = _c1_row(0, _norm_text("We are hiring a sales associate."))
    assert evaluable == "N"
    assert contra == "NA"


def test_c1_wfh_perk_framing_is_not_a_position_claim():
    """Regression: 'ability to occasionally work from home' is a flexible-working perk,
    not a claim the role is remote. Found in the full-corpus run: 197/223 original C1
    'contradictions' traced to this exact conflation."""
    text = _norm_text(
        "Flexible working hours, with the ability to occasionally work from home."
    )
    evaluable, contra, _ = _c1_row(0, text)
    assert evaluable == "N"
    assert contra == "NA"


def test_c1_wfh_with_position_cue_is_a_position_claim():
    text = _norm_text("This is a work from home position. All training is remote.")
    evaluable, contra, _ = _c1_row(0, text)
    assert evaluable == "Y"
    assert contra == "Y"


def test_c1_negated_remote_phrase_is_not_counted():
    """Regression: literal-phrase matching ignored negation, so 'this is NOT a remote
    position' still matched 'remote position' and was flagged as a contradiction even
    though the text and field (telecommuting == 0) actually agree."""
    text = _norm_text(
        "You must work from our Beverly Hills office - this is not a remote position."
    )
    evaluable, contra, _ = _c1_row(0, text)
    # Either correctly read as onsite (contradiction "N" against telecommuting=0), or
    # correctly excluded as not evaluable -- never a false "remote" contradiction.
    assert not (evaluable == "Y" and contra == "Y")


def test_c1_both_signals_present_is_ambiguous():
    text = _norm_text("Fully remote, though you must relocate to our office.")
    evaluable, contra, _ = _c1_row(0, text)
    assert evaluable == "N"
    assert contra == "NA"


# ---------------------------------------------------------------------------
# C2 — location field vs. place named via an explicit cue phrase
# ---------------------------------------------------------------------------

def test_c2_cue_phrase_matching_field_country():
    text = _norm_text("This position is located in London.")
    evaluable, contra, _ = _c2_row("GB, LND, London", text)
    assert evaluable == "Y"
    assert contra == "N"


def test_c2_cue_phrase_conflicting_country():
    text = _norm_text("You must relocate to Toronto within 60 days.")
    evaluable, contra, _ = _c2_row("US, PA, Scranton", text)
    assert evaluable == "Y"
    assert contra == "Y"


def test_c2_no_cue_phrase_not_evaluable():
    """Regression: the original C2 fell back to scanning the WHOLE text for any country
    name, so 'Canada/US passport holders only' (an eligibility clause) in a US posting
    was flagged as a location contradiction. Candidates now come only from an explicit
    cue phrase ('based in', 'relocate to', ...)."""
    text = _norm_text("Open to Canada/US passport holders only.")
    evaluable, contra, _ = _c2_row("US, PA, Scranton", text)
    assert evaluable == "N"
    assert contra == "NA"


def test_c2_blank_field_not_evaluable():
    evaluable, contra, _ = _c2_row("", _norm_text("Based in Berlin."))
    assert evaluable == "N"
    assert contra == "NA"


# ---------------------------------------------------------------------------
# C3 — employment_type vs. arrangement language
# ---------------------------------------------------------------------------

def test_c3_matching_signal():
    text = _norm_text("This is a full-time role, 40 hours a week.")
    evaluable, contra, _ = _c3_row("Full-time", text)
    assert evaluable == "Y"
    assert contra == "N"


def test_c3_conflicting_signal():
    text = _norm_text("This is a part-time role, flexible hours.")
    evaluable, contra, _ = _c3_row("Full-time", text)
    assert evaluable == "Y"
    assert contra == "Y"


def test_c3_short_term_disability_is_not_a_temporary_signal():
    """Regression: bare 'short-term'/'fixed-term' fired on standard US benefits-plan
    boilerplate. 95 of 252 original 'Temporary'-signal contradictions traced to exactly
    this phrase, which has nothing to do with the advertised role's employment type."""
    text = _norm_text(
        "Full-time position. Benefits include short-term disability and "
        "long-term disability coverage, dental, and vision."
    )
    evaluable, contra, _ = _c3_row("Full-time", text)
    assert evaluable == "Y"
    assert contra == "N"


def test_c3_seasonal_about_other_staff_is_not_a_signal():
    """Regression: bare 'seasonal' matched even when describing OTHER employees
    mentioned in the posting, not the advertised role ("...80 full-time staff and 200
    seasonal workers..."). Requiring a role-noun directly after 'seasonal' means
    'seasonal workers' no longer matches (there is no 'workers' in the role-noun list),
    so the genuine 'full-time' signal about the advertised role is read cleanly instead
    of being drowned out by a false ambiguity."""
    text = _norm_text(
        "You will work closely with our 80 full-time staff and 200 seasonal workers."
    )
    evaluable, contra, _ = _c3_row("Full-time", text)
    assert evaluable == "Y"
    assert contra == "N"


def test_c3_genuine_seasonal_position_is_a_signal():
    text = _norm_text("This is a seasonal position running through the holidays.")
    evaluable, contra, _ = _c3_row("Full-time", text)
    assert evaluable == "Y"
    assert contra == "Y"


def test_c3_blank_or_other_field_not_evaluable():
    evaluable, contra, _ = _c3_row("Other", _norm_text("Full-time role."))
    assert evaluable == "N"
    assert contra == "NA"


# ---------------------------------------------------------------------------
# C4 — required_experience vs. "N years" in text
# ---------------------------------------------------------------------------

def test_c4_age_phrase_excluded():
    """Regression: 'must be at least 25 years or older' is an age requirement, not an
    experience requirement."""
    text = _norm_text("Applicants must be at least 25 years or older to apply.")
    assert _years_of_experience_mentions(text) == []


def test_c4_unrelated_years_in_business_excluded():
    """Regression: 'world leader for more than 60 years' describes the company's
    history, not the role's experience requirement."""
    text = _norm_text("We have been a world leader in logistics for more than 60 years.")
    assert _years_of_experience_mentions(text) == []


def test_c4_genuine_experience_requirement_detected():
    text = _norm_text("Requires 5 years of experience in software development.")
    assert _years_of_experience_mentions(text) == [5]


def test_c4_large_gap_flagged_as_contradiction():
    text = _norm_text("Requires 15 years of experience in the field.")
    evaluable, contra, _ = _c4_row("Entry level", text)
    assert evaluable == "Y"
    assert contra == "Y"


def test_c4_blank_field_not_evaluable():
    evaluable, contra, _ = _c4_row("Not Applicable", _norm_text("5 years experience."))
    assert evaluable == "N"
    assert contra == "NA"


# ---------------------------------------------------------------------------
# C5 — required_education vs. qualification language
# ---------------------------------------------------------------------------

def test_c5_large_tier_gap_flagged():
    text = _norm_text("A PhD in a relevant field is required.")
    evaluable, contra, _ = _c5_row("High School or equivalent", text)
    assert evaluable == "Y"
    assert contra == "Y"


def test_c5_consistent_tier_not_flagged():
    text = _norm_text("A Bachelor's degree is required.")
    evaluable, contra, _ = _c5_row("Bachelor's Degree", text)
    assert evaluable == "Y"
    assert contra == "N"


def test_c5_unspecified_field_not_evaluable():
    evaluable, contra, _ = _c5_row("Unspecified", _norm_text("PhD required."))
    assert evaluable == "N"
    assert contra == "NA"


# ---------------------------------------------------------------------------
# C6 — salary_range vs. money figures (see module docstring, Decision 0.3)
# ---------------------------------------------------------------------------

def test_c6_k_suffix_resolved_to_thousands():
    """Regression: '$95k - $105k' was parsed as the literal numbers 95 and 105, so a
    figure that exactly matched the field range ($95,000-$105,000) was reported as 'far
    outside' it."""
    text = _norm_text("Competitive salary - $95k - $105k (DOE).")
    evaluable, contra, _, _ = _c6_row(True, 95000, 105000, text)
    assert evaluable == "Y"
    assert contra == "N"


def test_c6_unrelated_dollar_figure_excluded_by_salary_context_gate():
    """Regression: _SALARY_WORD_RE was defined but never wired into the matching logic,
    so an unrelated figure (e.g. a travel/interview reimbursement) was compared against
    salary_range and flagged as a contradiction -- as in the real posting this is based
    on (full-corpus run, 2026-10-08): 'up to $156,000 USD' (genuine salary) alongside,
    many words later, 'up to $1000 ... for the day of the interview' (an unrelated
    reimbursement) in the same posting. The unrelated figure must sit far enough from
    any salary-context word that the window-based gate in this test is a fair proxy for
    that real separation, not an artificially close substitute."""
    text = _norm_text(
        "Salary: $45,000 per year. "
        "We offer a fast-paced, collaborative environment with plenty of room to grow "
        "and a generous benefits package including dental, vision, and a 401k match. "
        "We also cover up to $1000 in travel cost for the day of the interview."
    )
    evaluable, contra, _, _ = _c6_row(True, 42000, 48000, text)
    assert evaluable == "Y"
    assert contra == "N"


def test_c6_genuine_large_mismatch_flagged():
    text = _norm_text("Salary: $9,000 per year.")
    evaluable, contra, _, _ = _c6_row(True, 90000, 110000, text)
    assert evaluable == "Y"
    assert contra == "Y"


def test_c6_field_absent_not_evaluable_but_supplementary_set():
    text = _norm_text("Salary: $60,000 per year.")
    evaluable, contra, _, supplementary = _c6_row(False, None, None, text)
    assert evaluable == "N"
    assert contra == "NA"
    assert supplementary == "Y"


def test_c6_no_salary_context_figure_not_evaluable():
    text = _norm_text("We offer $250 towards building your own ecommerce store.")
    evaluable, contra, _, supplementary = _c6_row(True, 35000, 45000, text)
    assert evaluable == "N"
    assert contra == "NA"
    assert supplementary == "N"


# ---------------------------------------------------------------------------
# E3 — metadata completeness composite
# ---------------------------------------------------------------------------

def test_e3_completeness_is_equal_weighted_mean():
    df = load_emscad(CSV_PATH)
    e3 = extract_e3(df.head(50))
    present_cols = [c for c in e3.columns if c.endswith("_present")]
    expected = e3[present_cols].mean(axis=1)
    assert (e3["E3_completeness_score"] == expected).all()
    assert e3["E3_completeness_score"].between(0, 1).all()


# ---------------------------------------------------------------------------
# End-to-end smoke test against the real corpus (shape/sanity only)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def df():
    return load_emscad(CSV_PATH)


def test_extract_all_and_coverage_report_shape(df):
    features = extract_all(df)
    assert len(features) == len(df)
    for prefix in ["E1_", "E2_", "E3_", "C1_", "C2_", "C3_", "C4_", "C5_", "C6_"]:
        assert any(c.startswith(prefix) for c in features.columns), f"no {prefix} columns"

    report = coverage_report(features)
    for rule in ["C1", "C2", "C3", "C4", "C5", "C6"]:
        assert 0 <= report[rule]["evaluable"] <= report[rule]["field_present"]
        assert report[rule]["evaluable"] <= len(df)
        assert 0 <= report[rule]["contradictions"] <= report[rule]["evaluable"]
    assert report["aggregate"]["n"] == len(df)
