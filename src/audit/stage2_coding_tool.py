#!/usr/bin/env python3
"""
Stage 2 -- interactive coding tool for the 200-posting manual audit (O1).
An Explainable Credibility Scoring Framework for Online Recruitment Posts
O.K. Samarasinghe -- COBSCCOMP242P-069

WHAT THIS DOES
    Shows one sampled posting at a time from reports/stage2_manual_audit_worksheet.csv,
    prompts you for the E1-E4 observability and C1-C6 contradiction judgements
    described in docs/STAGE2_CODING_INSTRUCTIONS.md, and saves the worksheet after
    every single row so nothing is ever lost if you stop partway through.

WHAT THIS DOES NOT DO
    It does not make any of the judgement calls for you. Every Y/N/PARTIAL/NA
    answer is typed by you, read from the posting yourself. That is the entire
    point of Stage 2 (see sample_for_manual_audit.py's own header comment, and
    decisions.md): O1 measures whether a HUMAN can observe these evidence
    categories, so the judgement has to come from a human, every time, or the
    "manual audit" claim in the dissertation would not be true.

BLINDING (recommended default)
    The true `fraudulent` label is hidden while you code, by default. Seeing it
    would quietly bias your own reading of each posting (you'd be tempted to code
    toward what you already know the "right" answer probably is), which would
    contaminate the measurement in a way that's hard to detect afterward. If you
    want to see it anyway, pass --show-label. If you decide to use it, log that
    choice in decisions.md -- it genuinely is a decision, not a neutral default.

RESUMING
    Re-running the script with no arguments automatically continues from the
    first row that is not fully coded -- including a row you were partway
    through when you quit. A partially-coded row is asked again in full next
    time (its old partial answers are overwritten), rather than silently
    skipped or resumed field-by-field, to avoid splitting one posting's
    judgement across two different sittings.

USAGE
    python src/audit/stage2_coding_tool.py                  # resume from where you left off
    python src/audit/stage2_coding_tool.py --full-text       # show the full description,
                                                               # not just the 400-char snippet
    python src/audit/stage2_coding_tool.py --jump S045        # jump straight to one posting
    python src/audit/stage2_coding_tool.py --show-label       # NOT recommended, see above
"""
from __future__ import annotations

import argparse
import csv
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORKSHEET = os.path.join(REPO_ROOT, "reports", "stage2_manual_audit_worksheet.csv")
FULL_CSV = os.path.join(REPO_ROOT, "data", "raw", "DataSet.csv")

E_COLUMNS = [
    ("E1_observable_MANUAL", "E1 text/content cues -- enough description/requirements text to judge wording, tone, specificity?"),
    ("E2_observable_MANUAL", "E2 identity/contact cues -- company_profile, specific location, or contact-pressure language present?"),
    ("E3_observable_MANUAL", "E3 completeness -- are the structured fields mostly filled or mostly blank?"),
    ("E4_observable_MANUAL", "E4 consistency-checkable -- could you even attempt to check text against fields here?"),
]
C_RULES = ["C1", "C2", "C3", "C4", "C5", "C6"]
C_LABELS = {
    "C1": "C1 remote/on-site vs telecommuting flag",
    "C2": "C2 location named in text vs structured location field",
    "C3": "C3 employment arrangement in text vs employment_type field",
    "C4": "C4 years-of-experience stated in text vs required_experience field",
    "C5": "C5 education requirement in text vs required_education field",
    "C6": "C6 compensation figure in text vs salary_range field",
}


def load_worksheet(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    return fieldnames, rows


def save_worksheet(path, fieldnames, rows):
    """Atomic save: write to a temp file, then replace -- never leaves a half-written CSV."""
    tmp = path + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(tmp, path)


def load_full_dataset():
    import pandas as pd
    return pd.read_csv(FULL_CSV, dtype=str, keep_default_na=False, na_values=[""])


def is_row_complete(row):
    """A row counts as done only once every E and C column is filled -- a row
    interrupted partway through (e.g. quit after E1/E2 but before E3) must be
    re-coded in full next time, not silently skipped."""
    if any(not row[col].strip() for col, _ in E_COLUMNS):
        return False
    for rule in C_RULES:
        if not row[f"{rule}_manual_contradiction_MANUAL"].strip():
            return False
    return True


def read_line(prompt):
    """input() that treats an unexpected EOF the same as the user typing Q --
    save and quit cleanly instead of crashing with a traceback."""
    try:
        return input(prompt)
    except EOFError:
        raise KeyboardInterrupt


def prompt_choice(label, choices):
    choice_str = "/".join(choices)
    while True:
        raw = read_line(f"  {label}\n  [{choice_str}] > ").strip().upper()
        if raw in ("Q", "QUIT"):
            raise KeyboardInterrupt
        if raw in choices:
            return raw
        print(f"    (enter one of: {choice_str}, or Q to save and quit)")


def code_one_row(row, full_df, show_label, full_text):
    print("=" * 78)
    print(f"{row['sample_id']}  |  title: {row['title']}")
    if show_label:
        print(f"[DEBUG -- label shown]: fraudulent={row['fraudulent']}")

    if full_text and full_df is not None:
        try:
            import pandas as pd

            def fmt(v):
                return "(blank)" if pd.isna(v) else repr(v)

            r = full_df.iloc[int(row["original_csv_index"])]
            print(f"\nFull description:\n{r['description']}\n")
            print(
                f"location={fmt(r['location'])} | employment_type={fmt(r['employment_type'])} | "
                f"required_experience={fmt(r['required_experience'])}"
            )
            print(
                f"required_education={fmt(r['required_education'])} | "
                f"salary_range={fmt(r['salary_range'])} | telecommuting={fmt(r['telecommuting'])}"
            )
        except Exception as e:
            print(f"(could not load full row, falling back to snippet: {e})")
            print(row["description_snippet"])
    else:
        print(f"\n{row['description_snippet']}")
        print("(400-char snippet -- rerun with --full-text if you need the rest for this posting)")

    print()
    for col, question in E_COLUMNS:
        row[col] = prompt_choice(question, ["Y", "N", "PARTIAL"])

    print()
    for rule in C_RULES:
        present = row[f"{rule}_field_present"].strip().upper()
        if present != "Y":
            row[f"{rule}_manual_contradiction_MANUAL"] = "NA"
            continue
        ref_hint = row[f"{rule}_pattern_evaluable_REFERENCE_ONLY"]
        label = f"{C_LABELS[rule]}  (reference-only pattern hint: {ref_hint!r} -- a crude regex, don't defer to it)"
        row[f"{rule}_manual_contradiction_MANUAL"] = prompt_choice(label, ["Y", "N", "NA"])

    note = read_line("\n  notes (blank for none; flag anything borderline or that made you want to revise the scheme): ").strip()
    row["notes_MANUAL"] = note


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--show-label", action="store_true", help="show the true fraudulent label while coding (NOT recommended -- see module docstring)")
    ap.add_argument("--full-text", action="store_true", help="load the full description from data/raw/DataSet.csv instead of the 400-char snippet (loads a ~59MB file once)")
    ap.add_argument("--jump", metavar="SAMPLE_ID", help="jump directly to one sample_id, e.g. S045, instead of resuming")
    args = ap.parse_args()

    if not os.path.exists(WORKSHEET):
        print(f"Worksheet not found at {WORKSHEET}", file=sys.stderr)
        sys.exit(1)

    fieldnames, rows = load_worksheet(WORKSHEET)
    total = len(rows)

    if args.jump:
        matches = [i for i, r in enumerate(rows) if r["sample_id"] == args.jump]
        if not matches:
            print(f"No row with sample_id={args.jump!r}", file=sys.stderr)
            sys.exit(1)
        start_idx = matches[0]
    else:
        start_idx = next((i for i, r in enumerate(rows) if not is_row_complete(r)), total)

    if start_idx >= total:
        print(f"All {total} rows are already coded. Nothing to do.")
        print("Next step: compute the observability/agreement rates per the instructions")
        print("in docs/STAGE2_CODING_INSTRUCTIONS.md and log them in methodology.md.")
        return

    coded_so_far = sum(1 for r in rows if is_row_complete(r))
    print(f"Stage 2 manual audit -- {coded_so_far}/{total} already fully coded.")
    print(f"Starting at {rows[start_idx]['sample_id']} ({start_idx + 1}/{total}).")
    print("Type Q at any prompt to save progress and quit; rerun with no arguments to resume.")
    print("(A row interrupted partway through will be asked again in full next time --")
    print(" partial answers from an interrupted row are not kept.)\n")

    full_df = load_full_dataset() if args.full_text else None

    for i in range(start_idx, total):
        row = rows[i]
        try:
            code_one_row(row, full_df, args.show_label, args.full_text)
        except KeyboardInterrupt:
            save_worksheet(WORKSHEET, fieldnames, rows)
            done = sum(1 for r in rows if is_row_complete(r))
            print(f"\n\nSaved. {done}/{total} fully coded so far. Resume any time with no arguments.")
            sys.exit(0)

        save_worksheet(WORKSHEET, fieldnames, rows)
        print(f"  -> saved ({i + 1}/{total} done)\n")

    print(f"\nAll {total} postings coded. Worksheet saved to reports/stage2_manual_audit_worksheet.csv.")
    print("Next: compute per-category observability rates and per-rule agreement rates")
    print("(docs/STAGE2_CODING_INSTRUCTIONS.md, 'When you're done'), and log the results")
    print("in methodology.md under 'Taxonomy validation (O1)' -- including at least one")
    print("thing the audit made you revise or drop.")


if __name__ == "__main__":
    main()
