"""
Stage 3 — Leakage-controlled partitioning
==========================================
An Explainable Credibility Scoring Framework for Online Recruitment Posts
O.K. Samarasinghe — COBSCCOMP242P-069

PURPOSE
    Split the Stage 1 output into train/validation/test partitions such that:
      1. No near-duplicate group (Decision 0.2: MD5-on-normalised-description UNION
         MD5-on-normalised-title) ever has members in more than one partition.
      2. The split is approximately stratified by `fraudulent`, so each partition keeps
         roughly the dataset's ~4.84% fraud rate.
      3. The split is a single FIXED partition (guardrail #4) — Stage 5's three seeds vary
         model initialisation only, never the split itself.

WHY GROUP-AWARE, NOT PLAIN STRATIFIED
    The data audit measured 4,762 records (26.6%) sitting in an exact-normalised-description
    duplicate group, with the fraud class disproportionately duplicated (40.3% vs 25.9% for
    legitimate). A plain stratified split would let near-identical postings land in both
    train and test, so the model would partly be recognising memorised strings rather than
    learning fraud patterns — this is leakage, and it would silently inflate every reported
    metric (decisions.md, 2026-08-07).

WHY DESCRIPTION-HASH ONLY, NOT DESCRIPTION-HASH UNION TITLE-HASH
    Decision 0.2 (2026-09-20) originally called for description-hash UNION title-hash, to
    catch campaigns that vary body text slightly while reusing a near-identical title (the
    "English Teacher Abroad" cluster fragmented across 15 separate MD5 groups under
    description-only hashing). That was implemented and tested on 2026-10-06, and a
    diagnostic on the 15 largest resulting groups showed severe over-merging: generic,
    common job titles ("Software Engineer", "Customer Service Associate", etc.) chained
    hundreds of genuinely unrelated postings from different companies into single groups —
    572 records / 118 distinct titles / 501 distinct descriptions for "Software Engineer"
    alone. This is a worse version of the exact failure mode Decision 0.2 already rejected a
    cheaper method for (the 12-token proxy, rejected for merging 48.9% of the corpus — the
    title-hash union merged 56.68%). Reverted to description-hash only the same night (see
    `decisions.md`, 2026-10-06, 23:59) — Decision 0.2's originally-considered Option A. This
    reproduces the already-measured, already-verified figures from the original August audit
    (4,762 records / 26.6%, largest group 417) instead of a broken number. The known cost —
    "English Teacher Abroad" fragmenting across several groups — is an accepted, disclosed
    limitation. A real fix (title match combined with a minimum description similarity, or
    proper near-duplicate clustering such as MinHash) is future work.

GROUP LABEL AND IMPURITY
    A group's "label" for stratification purposes is the majority class among its members.
    Any group that is NOT label-pure (contains both fraud and legit rows) is reported, not
    silently averaged away — see `grouping_report()["impure_groups"]`. A non-zero count here
    would itself be worth a sentence in the methodology chapter.

ALLOCATION METHOD
    Plain stratified-group K-fold machinery (e.g. sklearn's StratifiedGroupKFold) targets
    equal-sized folds, not an arbitrary 70/15/15 ratio. Instead this module uses a documented
    greedy allocator: within each class, groups are sorted largest-first (a seeded shuffle
    breaks ties) and each whole group is assigned to whichever partition is currently
    furthest below its row-count target for that class. This is deterministic given a fixed
    seed, keeps every group intact, and gets close to the target ratios — the actual achieved
    ratios are always reported, never assumed.

DEFINITION OF DONE (PROJECT_PLAN.md Section 7.5, Stage 3)
    - Group-aware stratified 70/15/15 split implemented
    - Zero group overlap proven across train/validation/test
    - Duplicate counts reported using the resolved (union) grouping method
    - Seed fixed and recorded (SPLIT_SEED = 42)
    - Results written into methodology.md (manual step, after running this script)

THIS MODULE DOES NOT
    - Fit any vectoriser, scaler or encoder (Stage 5's job, and it must fit on the `train`
      rows this module produces — never on val or test; guardrail #3).
    - Touch the test set's labels for anything except conservation checks in the test suite.
"""

import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from src.ingestion.load_emscad import load_emscad

# ----------------------------------------------------------------------------
# Fixed parameters — DECIDED. Log in decisions.md if changed.
# ----------------------------------------------------------------------------
SPLIT_SEED = 42
TRAIN_FRAC = 0.70
VAL_FRAC = 0.15
TEST_FRAC = 0.15

# ----------------------------------------------------------------------------
# Text normalisation — duplicated from sample_for_manual_audit.py (same known
# compromise logged there: keep in sync manually until a canonical module exists).
# ----------------------------------------------------------------------------


def normalise(s):
    s = str(s or "")
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"#[A-Z_]+_[0-9a-fA-F]+#", " ", s)
    s = s.lower()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _md5(s: str) -> str:
    return hashlib.md5(s.encode()).hexdigest()


# ----------------------------------------------------------------------------
# Grouping — union-find over description-hash groups and title-hash groups
# ----------------------------------------------------------------------------


class _UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1


def compute_groups(df: pd.DataFrame) -> pd.Series:
    """
    Returns a Series of integer group ids, one per row, aligned to df.index.
    Two rows are in the same group iff they share a normalised-description hash.

    NOTE: an earlier version of this function also unioned on normalised-title hash
    (Decision 0.2's original design). That was tested on 2026-10-06 and found to
    severely over-merge via transitive chaining on generic, common job titles — see the
    module docstring and decisions.md, 2026-10-06, 23:59. Description-hash-only grouping
    is the reverted, verified method. Union-find is kept (rather than a plain groupby)
    because it generalises cleanly if a safer second grouping key is added later.
    """
    n = len(df)
    uf = _UnionFind(n)

    desc_hash = df["description"].fillna("").map(normalise).map(_md5)

    groups = {}
    for pos, h in enumerate(desc_hash):
        groups.setdefault(h, []).append(pos)
    for members in groups.values():
        if len(members) < 2:
            continue
        first = members[0]
        for other in members[1:]:
            uf.union(first, other)

    roots = [uf.find(pos) for pos in range(n)]
    relabel = {}
    group_ids = []
    for r in roots:
        if r not in relabel:
            relabel[r] = len(relabel)
        group_ids.append(relabel[r])

    return pd.Series(group_ids, index=df.index, name="group_id")


def grouping_report(df: pd.DataFrame, group_id: pd.Series) -> dict:
    """Measured statistics under the resolved (description UNION title) grouping —
    comparable to, but not identical to, the description-only figures in sources.md #5."""
    sizes = group_id.value_counts()
    multi = sizes[sizes > 1]
    records_in_group = int(multi.sum())

    impure = 0
    for gid in multi.index:
        labels = df.loc[group_id == gid, "fraudulent"].unique()
        if len(labels) > 1:
            impure += 1

    return {
        "n_rows": int(len(df)),
        "n_groups": int(sizes.shape[0]),
        "n_groups_size_gt1": int(multi.shape[0]),
        "records_in_duplicate_group": records_in_group,
        "records_in_duplicate_group_pct": round(100 * records_in_group / len(df), 2),
        "impure_groups": int(impure),
        "largest_group_size": int(sizes.max()),
    }


# ----------------------------------------------------------------------------
# Greedy group-aware stratified allocation
# ----------------------------------------------------------------------------


def group_aware_stratified_split(
    df: pd.DataFrame,
    group_id: pd.Series,
    seed: int = SPLIT_SEED,
    train_frac: float = TRAIN_FRAC,
    val_frac: float = VAL_FRAC,
    test_frac: float = TEST_FRAC,
) -> pd.Series:
    """
    Returns a Series of {"train","val","test"} aligned to df.index. Whole groups are
    assigned atomically — see module docstring for the allocation method and why it's
    needed instead of a plain stratified split or an equal-fold group splitter.
    """
    assert abs(train_frac + val_frac + test_frac - 1.0) < 1e-9

    rng = np.random.default_rng(seed)

    group_label = (
        df.assign(group_id=group_id)
        .groupby("group_id")["fraudulent"]
        .agg(lambda s: int(s.sum() >= (len(s) / 2)))
    )
    group_size = group_id.value_counts()

    partitions = {"train": [], "val": [], "test": []}
    targets_frac = {"train": train_frac, "val": val_frac, "test": test_frac}

    for cls in (0, 1):
        cls_groups = group_label[group_label == cls].index.to_numpy()
        order = rng.permutation(len(cls_groups))
        cls_groups = cls_groups[order]
        cls_sizes = group_size.loc[cls_groups].to_numpy()
        sort_idx = np.argsort(-cls_sizes, kind="stable")
        cls_groups = cls_groups[sort_idx]
        cls_sizes = cls_sizes[sort_idx]

        cls_total = int(cls_sizes.sum())
        targets = {k: cls_total * f for k, f in targets_frac.items()}
        filled = {"train": 0, "val": 0, "test": 0}

        for gid, size in zip(cls_groups, cls_sizes):
            deficits = {k: targets[k] - filled[k] for k in filled}
            bucket = max(deficits, key=deficits.get)
            partitions[bucket].append(gid)
            filled[bucket] += size

    group_to_split = {}
    for split_name, gids in partitions.items():
        for gid in gids:
            group_to_split[gid] = split_name

    return group_id.map(group_to_split).rename("split")


def verify_split(df: pd.DataFrame, group_id: pd.Series, split: pd.Series) -> dict:
    """Hard proof, not an assumption: every group lands in exactly one partition, every
    row is assigned, and the fraud count is conserved across the three partitions."""
    group_splits = (
        pd.DataFrame({"group_id": group_id, "split": split})
        .groupby("group_id")["split"]
        .nunique()
    )
    n_crossing_groups = int((group_splits > 1).sum())

    counts = {}
    fraud_counts = {}
    for name in ("train", "val", "test"):
        mask = split == name
        counts[name] = int(mask.sum())
        fraud_counts[name] = int(df.loc[mask, "fraudulent"].sum())

    return {
        "zero_group_overlap": n_crossing_groups == 0,
        "n_crossing_groups": n_crossing_groups,
        "row_counts": counts,
        "row_fractions": {k: round(v / len(df), 4) for k, v in counts.items()},
        "fraud_counts": fraud_counts,
        "fraud_pct": {
            k: (round(100 * fraud_counts[k] / counts[k], 2) if counts[k] else None)
            for k in counts
        },
        "fraud_total_conserved": sum(fraud_counts.values()) == int(df["fraudulent"].sum()),
        "all_rows_assigned": int(split.notna().sum()) == len(df),
    }


def run(csv_path: str):
    df = load_emscad(csv_path)
    group_id = compute_groups(df)
    g_report = grouping_report(df, group_id)
    split = group_aware_stratified_split(df, group_id)
    v_report = verify_split(df, group_id, split)

    out = df.copy()
    out["group_id"] = group_id
    out["split"] = split

    summary = {
        "seed": SPLIT_SEED,
        "target_fractions": {"train": TRAIN_FRAC, "val": VAL_FRAC, "test": TEST_FRAC},
        "grouping": g_report,
        "verification": v_report,
    }
    return out, summary


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "data/raw/DataSet.csv"
    out_df, summary = run(path)

    Path("data/interim").mkdir(parents=True, exist_ok=True)
    out_df.to_csv("data/interim/stage3_split.csv", index=False)

    Path("reports").mkdir(exist_ok=True)
    with open("reports/stage3_split_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(json.dumps(summary, indent=2))
    print(
        "\nWritten: data/interim/stage3_split.csv (gitignored), "
        "reports/stage3_split_summary.json"
    )
