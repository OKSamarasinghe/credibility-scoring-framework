import sys
sys.path.insert(0, ".")

import pandas as pd
import numpy as np
from src.api import pipeline as api_pipeline
from src.api.stage8b_select import TIER2_FRAUD, TIER2_LEGIT, _load_jsonl, record_to_request

FIELDS = [
    "has_company_logo", "has_questions", "department", "salary_range",
    "employment_type", "required_experience", "required_education",
    "industry", "function", "company_profile", "location", "telecommuting",
]

def pct_missing(df, col):
    if col not in df.columns:
        return None
    s = df[col]
    if s.dtype == object:
        missing = s.isna() | (s.astype(str).str.strip() == "") | (s.astype(str) == "nan")
    else:
        missing = s.isna()
    return 100.0 * missing.sum() / len(df)

def build_tier2(path):
    rows = []
    for row in _load_jsonl(path):
        req = record_to_request(row)
        df_row = api_pipeline.build_posting_row(req)
        rows.append(df_row)
    return pd.concat(rows, ignore_index=True)

print("Loading EMSCAD train split ...")
emscad = pd.read_csv("data/interim/stage3_split.csv")
emscad_train = emscad[emscad["split"] == "train"]
print(f"  EMSCAD train: {len(emscad_train)} rows, columns sample: {list(emscad_train.columns)[:15]}")

print("Building Tier2 fraud via ScoreRequest pipeline ...")
t2_fraud = build_tier2(TIER2_FRAUD)
print(f"  Tier2 fraud: {len(t2_fraud)} rows")

print("Building Tier2 legit via ScoreRequest pipeline ...")
t2_legit = build_tier2(TIER2_LEGIT)
print(f"  Tier2 legit: {len(t2_legit)} rows")

print()
print(f"{'field':25s} {'EMSCAD-train %miss':>20s} {'Tier2-fraud %miss':>20s} {'Tier2-legit %miss':>20s}")
for f in FIELDS:
    e = pct_missing(emscad_train, f)
    tf = pct_missing(t2_fraud, f)
    tl = pct_missing(t2_legit, f)
    def fmt(x):
        return "n/a" if x is None else f"{x:.1f}%"
    print(f"{f:25s} {fmt(e):>20s} {fmt(tf):>20s} {fmt(tl):>20s}")

print()
print("EMSCAD train dtypes (first 20 cols):")
print(emscad_train.dtypes.head(20))
print()
print("Tier2-fraud sample row (first record):")
print(t2_fraud.iloc[0].to_dict())
