import json
import pandas as pd
import numpy as np
from pathlib import Path

STRUCT_COLS = ["department", "salary_range", "employment_type", "required_experience",
               "required_education", "industry", "function",
               "has_company_logo", "has_questions"]

TIER2_FRAUD = Path("data/raw/tier2/tier2_fraud_raw.jsonl")
TIER2_LEGIT = Path("data/raw/tier2/tier2_legit_raw.jsonl")

def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

def raw_missing_rate(records, col):
    n = len(records)
    miss = 0
    for r in records:
        v = r.get(col)
        if v is None:
            miss += 1
        elif isinstance(v, str) and v.strip() == "":
            miss += 1
    return 100.0 * miss / n if n else float("nan")

t2_fraud = load_jsonl(TIER2_FRAUD)
t2_legit = load_jsonl(TIER2_LEGIT)
print(f"Tier2 fraud: {len(t2_fraud)} records, Tier2 legit: {len(t2_legit)} records")
print()

print("=== Raw JSONL field presence (what record_to_request/ScoreRequest would see as None) ===")
print(f"{'field':25s} {'Tier2-fraud %miss':>20s} {'Tier2-legit %miss':>20s}")
for col in STRUCT_COLS:
    mf = raw_missing_rate(t2_fraud, col)
    ml = raw_missing_rate(t2_legit, col)
    print(f"{col:25s} {mf:19.1f}% {ml:19.1f}%")

print()
print("=== EMSCAD train split (data/interim/stage3_split.csv) ===")
emscad = pd.read_csv("data/interim/stage3_split.csv")
print("columns:", list(emscad.columns))
emscad_train = emscad[emscad["split"] == "train"] if "split" in emscad.columns else emscad
print(f"EMSCAD train rows: {len(emscad_train)}")
for col in STRUCT_COLS:
    if col not in emscad_train.columns:
        print(f"{col:25s}  COLUMN NOT PRESENT in stage3_split.csv")
        continue
    s = emscad_train[col]
    if pd.api.types.is_numeric_dtype(s):
        miss = s.isna().mean() * 100
    else:
        miss = (s.isna() | (s.fillna("").astype(str).str.strip() == "")).mean() * 100
    print(f"{col:25s}  {miss:6.1f}% missing  dtype={s.dtype}")

print()
print("Sample fraud record keys:", list(t2_fraud[0].keys()))
print("Sample fraud record (first):")
for k, v in t2_fraud[0].items():
    print(f"   {k!r}: {v!r}"[:160])
print()
print("Sample legit record (first):")
for k, v in t2_legit[0].items():
    print(f"   {k!r}: {v!r}"[:160])
