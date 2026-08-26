#!/usr/bin/env python3
"""
EMSCAD Data Audit
=================
An Explainable Credibility Scoring Framework for Online Recruitment Posts
O.K. Samarasinghe — COBSCCOMP242P-069

PURPOSE
    Measure, on the real CSV, every dataset claim currently marked unverified in
    sources.md. Replaces estimated figures with measured ones.

    Closes sources.md items:
      #3  consistency rule coverage C1-C6      (currently estimated, printed as fact)
      #4  boolean fields stored as 't'/'f'     (currently inferred)
      #5  duplicate counts                     (currently from a profiler, not measured)
      #7  #EMAIL_# / #PHONE_# / #URL_# tokens  (only #URL_# actually observed so far)
      #9  class composition 17,014 / 866       (corroborated, not confirmed)

USAGE
    python emscad_audit.py                        # auto-finds the CSV in this folder
    python emscad_audit.py path/to/data.csv

OUTPUT
    audit_report.md    — paste straight into methodology.md "Data audit" section
    audit_results.json — machine-readable, for reuse in later stages

REQUIREMENTS
    pandas, numpy        (pip install pandas numpy)

NOTE ON SCOPE
    This script measures DATA AVAILABILITY, not rule firing. For each consistency
    rule it reports:
      - field coverage    : the structured field(s) the rule reads are present
      - evaluable coverage: BOTH operands are present, so the rule could actually run
    Evaluable coverage is the honest upper bound on rule coverage. How often each
    rule actually FIRES is a Stage 4 measurement, once the lexicons are written.
"""

import sys
import os
import re
import json
import glob
import hashlib
from datetime import date

import pandas as pd
import numpy as np

pd.set_option("display.width", 200)

BOOL_COLS = ["telecommuting", "has_company_logo", "has_questions",
             "fraudulent", "in_balanced_dataset"]

TEXT_COLS = ["title", "company_profile", "description", "requirements", "benefits"]

STRUCT_COLS = ["department", "salary_range", "employment_type", "required_experience",
               "required_education", "industry", "function",
               "has_company_logo", "has_questions"]

R = {}          # results dict
LINES = []      # report lines


def say(s=""):
    print(s)
    LINES.append(s)


def head(title):
    say()
    say("=" * 74)
    say(title)
    say("=" * 74)


# ----------------------------------------------------------------------------
# 0. LOAD
# ----------------------------------------------------------------------------

def find_csv():
    if len(sys.argv) > 1:
        return sys.argv[1]
    candidates = glob.glob("*.csv")
    if not candidates:
        sys.exit("No CSV found. Pass the path: python emscad_audit.py <file.csv>")
    # prefer the usual Kaggle filename
    for c in candidates:
        if "job" in c.lower() or "emscad" in c.lower() or "fake" in c.lower():
            return c
    return candidates[0]


path = find_csv()
print(f"Reading: {path}\n")
df = pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[""])
R["file"] = os.path.basename(path)
R["audit_date"] = str(date.today())

head("1.  SHAPE AND COLUMNS")
say(f"File            : {os.path.basename(path)}")
say(f"Rows            : {len(df):,}")
say(f"Columns         : {len(df.columns)}")
say(f"Column names    : {', '.join(df.columns)}")
R["n_rows"] = int(len(df))
R["n_cols"] = int(len(df.columns))
R["columns"] = list(df.columns)

expected = 17880
say()
say(f"Expected 17,880 rows (EMSCAD): {'MATCH' if len(df) == expected else 'MISMATCH — investigate'}")
R["row_count_matches_expected"] = bool(len(df) == expected)


# ----------------------------------------------------------------------------
# 1. BOOLEAN ENCODING  (sources.md #4)
# ----------------------------------------------------------------------------

head("2.  BOOLEAN ENCODING  [sources.md #4]")

enc = {}
for col in BOOL_COLS:
    if col not in df.columns:
        say(f"{col:22s} : COLUMN NOT PRESENT")
        enc[col] = None
        continue
    vals = sorted([str(v) for v in df[col].dropna().unique()])
    show = vals if len(vals) <= 6 else vals[:6] + ["..."]
    say(f"{col:22s} : {show}")
    enc[col] = vals

R["boolean_encoding"] = enc

flat = set()
for v in enc.values():
    if v:
        flat.update(v)
say()
if flat <= {"t", "f"}:
    say("RESULT: confirmed — booleans are stored as the string literals 't' and 'f'.")
    say("        sources.md #4 can be marked VERIFIED.")
    R["tf_encoding_confirmed"] = True
elif flat <= {"0", "1"}:
    say("RESULT: NOT 't'/'f' — these are stored as '0'/'1'.")
    say("        CORRECT Research_Methodology_Final.docx section 2.1.2 and Stage 1.")
    R["tf_encoding_confirmed"] = False
else:
    say(f"RESULT: unexpected encoding {sorted(flat)} — inspect before proceeding.")
    R["tf_encoding_confirmed"] = False


def to_int(series):
    """Map whatever encoding is present onto 0/1."""
    m = {"t": 1, "f": 0, "T": 1, "F": 0, "1": 1, "0": 0,
         "true": 1, "false": 0, "True": 1, "False": 0}
    return series.map(lambda x: m.get(str(x).strip(), np.nan))


for col in BOOL_COLS:
    if col in df.columns:
        df[col + "_i"] = to_int(df[col])


# ----------------------------------------------------------------------------
# 2. CLASS COMPOSITION  (sources.md #9)
# ----------------------------------------------------------------------------

head("3.  CLASS COMPOSITION  [sources.md #9]")

if "fraudulent_i" in df.columns:
    n_fraud = int(df["fraudulent_i"].sum())
    n_legit = int((df["fraudulent_i"] == 0).sum())
    n_bad = int(df["fraudulent_i"].isna().sum())
    pct = 100 * n_fraud / len(df)
    say(f"Fraudulent      : {n_fraud:,}   ({pct:.2f}%)")
    say(f"Legitimate      : {n_legit:,}   ({100-pct:.2f}%)")
    if n_bad:
        say(f"Unparseable     : {n_bad:,}  <-- INVESTIGATE")
    say()
    say(f"Expected 866 fraudulent: {'MATCH' if n_fraud == 866 else 'MISMATCH — investigate'}")
    say(f"Expected 17,014 legit  : {'MATCH' if n_legit == 17014 else 'MISMATCH — investigate'}")
    R.update(n_fraudulent=n_fraud, n_legitimate=n_legit,
             fraud_pct=round(pct, 3),
             class_counts_match_expected=bool(n_fraud == 866 and n_legit == 17014))
else:
    say("fraudulent column not found — cannot proceed with class checks.")

# leakage-prone column
say()
if "in_balanced_dataset" in df.columns:
    say("in_balanced_dataset : PRESENT — must be dropped from the feature space (Stage 1).")
    R["in_balanced_dataset_present"] = True
else:
    say("in_balanced_dataset : not present in this mirror.")
    R["in_balanced_dataset_present"] = False


# ----------------------------------------------------------------------------
# 3. MISSINGNESS
# ----------------------------------------------------------------------------

head("4.  FIELD MISSINGNESS  (drives the E3 completeness category)")

miss = {}
say(f"{'Field':24s} {'Present':>9s} {'Missing':>9s} {'Missing %':>10s}")
say("-" * 56)
for col in df.columns:
    if col.endswith("_i"):
        continue
    n_missing = int((df[col].isna() | (df[col].fillna("").str.strip() == "")).sum())
    n_present = len(df) - n_missing
    pctm = 100 * n_missing / len(df)
    miss[col] = {"present": n_present, "missing": n_missing, "missing_pct": round(pctm, 2)}
    say(f"{col:24s} {n_present:>9,} {n_missing:>9,} {pctm:>9.1f}%")
R["missingness"] = miss


# ----------------------------------------------------------------------------
# 4. SALARY PLACEHOLDERS
# ----------------------------------------------------------------------------

head("5.  SALARY_RANGE QUALITY")

if "salary_range" in df.columns:
    sr = df["salary_range"].fillna("").str.strip()
    n_present = int((sr != "").sum())
    n_zero = int((sr == "0-0").sum())
    parseable = sr.str.match(r"^\s*\d+\s*-\s*\d+\s*$", na=False)
    n_parse = int(parseable.sum())
    n_usable = int((parseable & (sr != "0-0")).sum())
    say(f"Present                     : {n_present:,}  ({100*n_present/len(df):.1f}%)")
    say(f"Literal '0-0' placeholder   : {n_zero:,}")
    say(f"Numeric 'lo-hi' parseable   : {n_parse:,}")
    say(f"USABLE (parseable, not 0-0) : {n_usable:,}  ({100*n_usable/len(df):.1f}%)")
    say()
    say("The usable figure is the real ceiling for consistency rule C6.")
    R["salary"] = {"present": n_present, "zero_zero": n_zero,
                   "parseable": n_parse, "usable": n_usable,
                   "usable_pct": round(100*n_usable/len(df), 2)}


# ----------------------------------------------------------------------------
# 5. ANONYMISATION TOKENS  (sources.md #7 — HIGH IMPACT)
# ----------------------------------------------------------------------------

head("6.  ANONYMISED CONTACT TOKENS  [sources.md #7 — HIGH IMPACT]")

say("E2 (Identity & Contact Cues) depends on these existing. If #EMAIL_# and")
say("#PHONE_# are absent, a large part of E2 collapses and the taxonomy needs revision.")
say()

TOKEN_PATTERNS = {
    "#URL_#":    re.compile(r"#URL_[0-9a-fA-F]+#"),
    "#EMAIL_#":  re.compile(r"#EMAIL_[0-9a-fA-F]+#"),
    "#PHONE_#":  re.compile(r"#PHONE_[0-9a-fA-F]+#"),
}
# also catch any token of the generic form #WORD_hash#
GENERIC = re.compile(r"#([A-Z_]+)_[0-9a-fA-F]{4,}#")

search_cols = [c for c in ["description", "requirements", "benefits", "company_profile"]
               if c in df.columns]
blob = df[search_cols].fillna("").agg(" ".join, axis=1)

tok = {}
say(f"{'Token':12s} {'Postings with >=1':>18s} {'% of rows':>10s} {'Total occurrences':>18s}")
say("-" * 62)
for name, pat in TOKEN_PATTERNS.items():
    counts = blob.str.count(pat)
    n_posts = int((counts > 0).sum())
    total = int(counts.sum())
    tok[name] = {"postings": n_posts, "total": total,
                 "pct_rows": round(100*n_posts/len(df), 2)}
    say(f"{name:12s} {n_posts:>18,} {100*n_posts/len(df):>9.1f}% {total:>18,}")
R["contact_tokens"] = tok

# discover any other token types actually present
found = {}
for txt in blob.head(20000):
    for m in GENERIC.finditer(txt):
        found[m.group(1)] = found.get(m.group(1), 0) + 1
say()
say(f"All placeholder token types discovered: {sorted(found.keys()) if found else 'NONE'}")
R["token_types_found"] = sorted(found.keys())

say()
missing_tok = [k for k, v in tok.items() if v["postings"] == 0]
if missing_tok:
    say(f"WARNING: {', '.join(missing_tok)} NOT FOUND in this dataset.")
    say("         Revise the E2 taxonomy and correct section 2.1.3 of the methodology.")
else:
    say("RESULT: all three token types present — E2 stands as designed.")
    say("        sources.md #7 can be marked VERIFIED.")

# token rate by class — is this actually a fraud signal?
if "fraudulent_i" in df.columns:
    say()
    say("Token presence by class (is this actually discriminative?):")
    say(f"{'Token':12s} {'Fraud %':>10s} {'Legit %':>10s} {'Ratio':>8s}")
    say("-" * 44)
    by_class = {}
    for name, pat in TOKEN_PATTERNS.items():
        has = blob.str.contains(pat)
        f_rate = 100 * has[df["fraudulent_i"] == 1].mean()
        l_rate = 100 * has[df["fraudulent_i"] == 0].mean()
        ratio = (f_rate / l_rate) if l_rate > 0 else float("nan")
        by_class[name] = {"fraud_pct": round(f_rate, 2), "legit_pct": round(l_rate, 2),
                          "ratio": None if np.isnan(ratio) else round(ratio, 2)}
        say(f"{name:12s} {f_rate:>9.1f}% {l_rate:>9.1f}% {ratio:>8.2f}")
    R["token_by_class"] = by_class
    say()
    say("A ratio well above 1.0 means fraudulent postings carry that token more often.")
    say("This is descriptive only — not a modelling result.")


# ----------------------------------------------------------------------------
# 6. DUPLICATES  (sources.md #5)
# ----------------------------------------------------------------------------

head("7.  DUPLICATE AND NEAR-DUPLICATE POSTINGS  [sources.md #5]")


def normalise(s):
    s = str(s or "")
    s = re.sub(r"<[^>]+>", " ", s)                 # strip markup
    s = re.sub(r"#[A-Z_]+_[0-9a-fA-F]+#", " ", s)  # strip anonymisation tokens
    s = s.lower()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


desc = df["description"].fillna("")
n_exact = int(desc.nunique())
norm = desc.map(normalise)
df["_hash"] = norm.map(lambda t: hashlib.md5(t.encode()).hexdigest())
n_norm = int(df["_hash"].nunique())

vc_all = df["_hash"].value_counts()
n_in_dup_groups = int(vc_all[vc_all > 1].sum())  # TRUE count of records sitting in a group >1
n_excess = len(df) - n_norm                       # old (mislabeled) figure: n - n_unique

say(f"Total records                          : {len(df):,}")
say(f"Unique descriptions (exact, raw)       : {n_exact:,}")
say(f"Unique descriptions (normalised)       : {n_norm:,}")
say(f"Records sitting in a duplicate group    : {n_in_dup_groups:,}  ({100*n_in_dup_groups/len(df):.1f}%)")
say(f"  (excess-over-unique figure, for reference only: {n_excess:,} — NOT the group-")
say(f"   membership count; fixed 2026-08-27, see sources.md #5 note)")
say(f"Duplicate groups (size > 1)            : {int((vc_all > 1).sum()):,}")
if "title" in df.columns:
    say(f"Unique titles                          : {df['title'].nunique():,}")

R["duplicates"] = {
    "unique_desc_exact": n_exact,
    "unique_desc_normalised": n_norm,
    "records_in_dup_groups": n_in_dup_groups,
    "records_in_dup_groups_excess_figure_deprecated": n_excess,
    "n_dup_groups": int((vc_all > 1).sum()),
    "unique_titles": int(df["title"].nunique()) if "title" in df.columns else None,
}

say()
say("Normalising finds MORE duplicates than exact matching. The normalised figure")
say("is the one that matters for group-aware partitioning (Stage 3).")

# duplication within the fraud class specifically
if "fraudulent_i" in df.columns:
    fr = df[df["fraudulent_i"] == 1]
    lg = df[df["fraudulent_i"] == 0]
    f_dup_vc = fr["_hash"].value_counts()
    l_dup_vc = lg["_hash"].value_counts()
    f_dup = int(f_dup_vc[f_dup_vc > 1].sum())  # TRUE group-membership count (fixed 2026-08-27,
    l_dup = int(l_dup_vc[l_dup_vc > 1].sum())  # same bug/fix as the top-level figure above)
    say()
    say(f"Duplicated fraudulent records          : {f_dup:,} of {len(fr):,} ({100*f_dup/max(len(fr),1):.1f}%)")
    say(f"Duplicated legitimate records          : {l_dup:,} of {len(lg):,} ({100*l_dup/max(len(lg),1):.1f}%)")
    say()
    say("If the fraud class is more duplicated, a random split inflates fraud-class")
    say("performance specifically — which is exactly the metric this study reports.")
    R["duplicates"]["fraud_dup_records"] = int(f_dup)
    R["duplicates"]["legit_dup_records"] = int(l_dup)
    R["duplicates"]["fraud_dup_pct"] = round(100*f_dup/max(len(fr), 1), 2)
    R["duplicates"]["legit_dup_pct"] = round(100*l_dup/max(len(lg), 1), 2)

    say()
    say("Largest fraudulent duplicate clusters:")
    top = fr["_hash"].value_counts().head(5)
    for h, n in top.items():
        t = fr[fr["_hash"] == h]["title"].iloc[0] if "title" in fr.columns else "(no title)"
        say(f"   {n:>4} copies   {str(t)[:58]}")
    R["duplicates"]["top_fraud_clusters"] = [
        {"copies": int(n),
         "title": str(fr[fr['_hash'] == h]['title'].iloc[0])[:80] if 'title' in fr.columns else None}
        for h, n in top.items()
    ]


# ----------------------------------------------------------------------------
# 7. LOCATION PARSEABILITY
# ----------------------------------------------------------------------------

head("8.  LOCATION PARSEABILITY  (drives rule C2)")

if "location" in df.columns:
    loc = df["location"].fillna("").str.strip()
    present = loc != ""
    parts = loc.str.split(",")
    n_country = int((present & (parts.map(len) >= 1) & (loc.str.split(",").str[0].str.strip() != "")).sum())
    n_city = int((present & (parts.map(len) >= 3) & (loc.str.split(",").str[2].str.strip() != "")).sum())
    say(f"Location present            : {int(present.sum()):,}  ({100*present.mean():.1f}%)")
    say(f"Country component usable    : {n_country:,}  ({100*n_country/len(df):.1f}%)")
    say(f"City component usable       : {n_city:,}  ({100*n_city/len(df):.1f}%)")
    say()
    say("C2 needs a usable location component AND a location named in the description.")
    R["location"] = {"present": int(present.sum()), "country": n_country, "city": n_city,
                     "city_pct": round(100*n_city/len(df), 2)}


# ----------------------------------------------------------------------------
# 8. CONSISTENCY RULE COVERAGE  (sources.md #3 — THE HEADLINE MEASUREMENT)
# ----------------------------------------------------------------------------

head("9.  CONSISTENCY RULE COVERAGE C1-C6  [sources.md #3]")

say("field coverage    = the structured field the rule reads is present")
say("evaluable coverage = BOTH operands present, so the rule could actually run")
say("Evaluable coverage is the honest number for the methodology table.")
say()

d_norm = norm  # normalised DESCRIPTION only

# The text side of rules C3-C6 must search the full posting body, not just the
# description: education requirements normally sit in `requirements`, and
# compensation statements often sit in `benefits`. Using description alone would
# understate coverage and, at Stage 4, would miss real contradictions.
body_cols = [c for c in ["description", "requirements", "benefits"] if c in df.columns]
body = df[body_cols].fillna("").agg(" ".join, axis=1)
b_norm = body.map(normalise)
say(f"Text operand for C3-C6 = {' + '.join(body_cols)} (not description alone).")
say()

REMOTE = re.compile(r"\b(?:work from home|remote|telecommut|home based|home-based|virtual office|anywhere)\b")
ONSITE = re.compile(r"\b(?:on site|onsite|in office|in-office|in person|relocat|commute|our office|headquarters|must be located|based in our)\b")
ARRANGEMENT = re.compile(REMOTE.pattern + "|" + ONSITE.pattern)
PARTTIME = re.compile(r"\b(?:part time|parttime|part-time|contract|temporary|freelance|internship)\b")
YEARS = re.compile(r"\b\d{1,2}\s*\+?\s*(?:or more\s*)?year")
EDU = re.compile(r"\b(?:degree|diploma|bachelor|master|phd|graduate|qualification|certificat)\b")
MONEY = re.compile(r"(?:\$|usd|eur|gbp|salary|per month|per year|per annum|monthly|annually)")


def field_present(col):
    if col not in df.columns:
        return pd.Series(False, index=df.index)
    return df[col].fillna("").str.strip().ne("")


rules = {}
DEFERRED = set()  # rules whose evaluable coverage is not measured yet (report field coverage only)

# C1 — telecommuting vs remote/on-site language.
# STRICT/symmetric definition (2026-08-27 fix, revised same day): bounded vocabulary,
# same category as C3 — NOT deferred like C2. Must detect a contradiction in EITHER
# direction (field says on-site but text says remote, OR field says remote but text
# describes an on-site arrangement), so both REMOTE and ONSITE language count.
c1_field = df["telecommuting_i"].notna() if "telecommuting_i" in df.columns else pd.Series(False, index=df.index)
c1_eval = c1_field & d_norm.str.contains(ARRANGEMENT)
rules["C1"] = ("Remote / on-site", c1_field, c1_eval)

# C2 — location vs locations named in description
# NOT symmetric with the other five rules, and deliberately so (logged decision, 2026-08-27).
# The rule's actual premise is "a place name from the text differs from the structured
# field" — genuine location extraction, which is Stage 4 work. A quick regex proxy here
# would silently become a second, weaker implementation of the rule, and the two would be
# guaranteed to disagree at Stage 4. Field coverage is reported as an explicit UPPER BOUND;
# evaluable coverage is deferred until the real Stage 4 matcher exists.
if "location" in df.columns:
    c2_field = df["location"].fillna("").str.strip().ne("")
    has_city = df["location"].fillna("").str.split(",").map(lambda p: len(p) >= 3 and p[2].strip() != "")
    c2_field = c2_field & has_city  # the only field-side condition this audit can measure
else:
    c2_field = pd.Series(False, index=df.index)
c2_eval = pd.Series(False, index=df.index)  # placeholder; not reported (see DEFERRED)
rules["C2"] = ("Location mismatch", c2_field, c2_eval)
DEFERRED.add("C2")

# C3 — employment_type vs working-arrangement language
# STRICT/symmetric definition (2026-08-27 fix): body must actually contain arrangement
# language (part-time/contract/temporary/etc.), not merely be non-empty.
c3_field = field_present("employment_type")
c3_eval = c3_field & b_norm.str.contains(PARTTIME)
rules["C3"] = ("Employment type", c3_field, c3_eval)

# C4 — required_experience vs "N years" in text
c4_field = field_present("required_experience")
c4_eval = c4_field & b_norm.str.contains(YEARS)
rules["C4"] = ("Experience level", c4_field, c4_eval)

# C5 — required_education vs qualification statements in text
c5_field = field_present("required_education")
c5_eval = c5_field & b_norm.str.contains(EDU)
rules["C5"] = ("Education", c5_field, c5_eval)

# C6 — salary_range vs compensation figures in text
if "salary_range" in df.columns:
    sr = df["salary_range"].fillna("").str.strip()
    c6_field = sr.str.match(r"^\s*\d+\s*-\s*\d+\s*$", na=False) & sr.ne("0-0")
    c6_eval = c6_field & body.str.lower().str.contains(MONEY)
else:
    c6_field = c6_eval = pd.Series(False, index=df.index)
rules["C6"] = ("Salary", c6_field, c6_eval)

ESTIMATED = {"C1": 100, "C2": 98, "C3": 81, "C4": 61, "C5": 55, "C6": 16}

say("CAVEAT: all evaluable-coverage figures below are provisional — they use this audit")
say("script's own placeholder patterns (REMOTE/PARTTIME/YEARS/EDU/MONEY), not the final")
say("Stage 4 lexicons. Re-measure once those lexicons are frozen. C2 has no evaluable")
say("figure at all yet: its field coverage is an explicit UPPER BOUND, not a measurement —")
say("see the code comment on C2 for why a quick proxy was deliberately not used.")
say()
say(f"{'ID':4s} {'Rule':20s} {'Field cov':>10s} {'Evaluable':>14s} {'Was est.':>9s} {'Delta':>7s}")
say("-" * 74)
cov = {}
for rid, (label, fcol, ecol) in rules.items():
    fpct = 100 * fcol.mean()
    est = ESTIMATED[rid]
    if rid in DEFERRED:
        cov[rid] = {"rule": label,
                    "field_coverage_pct": round(fpct, 1),
                    "field_coverage_is_upper_bound": True,
                    "evaluable_coverage_pct": None,
                    "evaluable_status": "DEFERRED to Stage 4 (see code comment)",
                    "previous_estimate_pct": est}
        say(f"{rid:4s} {label:20s} {fpct:>9.1f}% {'DEFERRED':>14s} {est:>8d}% {'n/a':>7s}")
    else:
        epct = 100 * ecol.mean()
        delta = epct - est
        cov[rid] = {"rule": label,
                    "field_coverage_pct": round(fpct, 1),
                    "evaluable_coverage_pct": round(epct, 1),
                    "evaluable_is_provisional": True,
                    "previous_estimate_pct": est,
                    "delta_vs_estimate": round(delta, 1)}
        say(f"{rid:4s} {label:20s} {fpct:>9.1f}% {epct:>13.1f}% {est:>8d}% {delta:>+6.1f}")
R["rule_coverage"] = cov

# description-only comparison, so the effect of including requirements/benefits is visible
desc_only = {
    "C4": round(100 * (c4_field & d_norm.str.contains(YEARS)).mean(), 1),
    "C5": round(100 * (c5_field & d_norm.str.contains(EDU)).mean(), 1),
    "C6": round(100 * (c6_field & desc.str.lower().str.contains(MONEY)).mean(), 1),
}
R["rule_coverage_description_only"] = desc_only
say()
say("For comparison, evaluable coverage using DESCRIPTION ALONE:")
for k, v in desc_only.items():
    say(f"   {k}: {v:.1f}%   (vs {cov[k]['evaluable_coverage_pct']:.1f}% using the full body)")

say()
say("ACTION: replace the Field Coverage column in Research_Methodology_Final.docx")
say("        section 3.1 with the EVALUABLE figures above. C1,C3-C6 are provisional")
say("        (placeholder patterns). C2 has no evaluable figure — field coverage only,")
say("        an upper bound. Do NOT mark sources.md #3 fully verified yet.")

# how many postings can be checked by at least one rule
any_eval = np.logical_or.reduce([e.values for _, _, e in rules.values()])
n_any = int(any_eval.sum())
say()
say(f"Postings evaluable by at least one rule : {n_any:,}  ({100*n_any/len(df):.1f}%)")
n_rules_per_post = sum(e.astype(int) for _, _, e in rules.values())
say(f"Mean rules evaluable per posting        : {n_rules_per_post.mean():.2f} of 6")
R["rule_coverage_summary"] = {
    "postings_with_any_evaluable_rule": n_any,
    "pct_with_any_evaluable_rule": round(100*n_any/len(df), 2),
    "mean_evaluable_rules_per_posting": round(float(n_rules_per_post.mean()), 2),
}


# ----------------------------------------------------------------------------
# 9. WRITE OUTPUTS
# ----------------------------------------------------------------------------

head("10.  SUMMARY — WHAT TO UPDATE")

say("sources.md:")
say(f"  #4 boolean t/f encoding      -> {'VERIFIED' if R.get('tf_encoding_confirmed') else 'CORRECTION NEEDED'}")
say(f"  #9 class composition         -> {'VERIFIED' if R.get('class_counts_match_expected') else 'CORRECTION NEEDED'}")
say(f"  #7 contact tokens            -> {'VERIFIED' if not missing_tok else 'CORRECTION NEEDED'}")
say( "  #5 duplicate counts          -> VERIFIED (measured figures above; group-membership")
say( "                                   count corrected 2026-08-27, was mislabeled)")
say( "  #3 rule coverage             -> PARTIALLY VERIFIED. C1,C3-C6 evaluable coverage")
say( "                                   measured but PROVISIONAL (placeholder patterns,")
say( "                                   not final Stage 4 lexicons). C2 evaluable coverage")
say( "                                   NOT measured — field coverage only, reported as")
say( "                                   an upper bound. Do not mark #3 fully verified.")
say()
say("Research_Methodology_Final.docx:")
say("  section 3.1  -> replace Field Coverage column with measured evaluable coverage")
say("  section 2.1.2 -> confirm or correct the duplicate and encoding statements")
say()
say("methodology.md:")
say("  'Data audit' results block -> paste from audit_report.md")

with open("audit_report.md", "w") as f:
    f.write("# EMSCAD Data Audit — measured results\n\n")
    f.write(f"_Run: {R['audit_date']} · File: {R['file']}_\n\n")
    f.write("```\n")
    f.write("\n".join(LINES))
    f.write("\n```\n")

with open("audit_results.json", "w") as f:
    json.dump(R, f, indent=2, default=str)

print("\n\nWritten: audit_report.md, audit_results.json")
