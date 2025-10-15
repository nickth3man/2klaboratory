"""
Compute feature composites and percentiles for canonical builds.

Usage:
    python scripts/compute_features.py --input builds/data/builds_canonical.csv --output builds/data
Flags:
    --force            Overwrite outputs if present.
    --skip-percentiles Skip percentile computation.

Produces (idempotent):
 - builds/data/builds_features.csv
 - builds/data/builds_features.pkl
 - builds/data/feature_definitions.json
 - builds/data/feature_report.json

Notes:
 - Requires: pandas, numpy
 - Percentiles are computed as percentile-rank (0-100) and rounded to 2 decimals.
 - Composite values use a per-row weighted-median with missing-value reweighting.
"""
from __future__ import annotations

import argparse
import json
import logging
import math
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

LOGGER = logging.getLogger("compute_features")
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def weighted_median(values: Sequence[float], weights: Sequence[float]) -> Optional[float]:
    """
    Compute the weighted median of values with corresponding weights.

    - values: sequence of numeric values (may contain NaN)
    - weights: sequence of non-negative weights (same length)
    Returns median or None if no valid values.
    """
    if len(values) == 0:
        return None
    v = np.asarray(values, dtype=float)
    w = np.asarray(weights, dtype=float)

    mask = ~np.isnan(v)
    if not mask.any():
        return None
    v = v[mask]
    w = w[mask].astype(float)

    # Remove non-positive weights
    positive = w > 0
    if not positive.any():
        # equal weights fallback
        return float(np.median(v))
    v = v[positive]
    w = w[positive]

    # normalize weights to sum to 1
    w_sum = float(w.sum())
    if w_sum <= 0 or math.isnan(w_sum):
        return float(np.median(v))
    w = w / w_sum

    # sort by value
    order = np.argsort(v)
    v_sorted = v[order]
    w_sorted = w[order]
    cumsum = np.cumsum(w_sorted)
    # first index where cumsum >= 0.5
    idx = np.searchsorted(cumsum, 0.5, side="left")
    idx = min(idx, len(v_sorted) - 1)
    return float(v_sorted[idx])


def ensure_float_cols(df: pd.DataFrame, cols: Iterable[str]) -> None:
    """Ensure specified columns exist on df and are float dtype (create with NaN if missing)."""
    for c in cols:
        if c not in df.columns:
            df[c] = np.nan
        df[c] = df[c].astype(float)


COMPOSITE_SPECS: Dict[str, Tuple[List[str], List[float]]] = {
    "finishing": (
        ["close_shot", "driving_layup", "driving_dunk", "standing_dunk", "post_control"],
        [0.22, 0.18, 0.25, 0.15, 0.20],
    ),
    "shooting": (
        ["midrange_shot", "threepoint_shot", "free_throw"],
        [0.4, 0.45, 0.15],
    ),
    "playmaking": (
        ["pass_accuracy", "ball_handle", "speed_with_ball"],
        [0.4, 0.35, 0.25],
    ),
    "defense": (
        ["interior_defense", "perimeter_defense", "steal", "block", "defensive_rebound"],
        [0.25, 0.25, 0.15, 0.15, 0.20],
    ),
    "athleticism": (
        ["speed", "agility", "strength", "vertical"],
        [0.25, 0.25, 0.2, 0.3],
    ),
}


def col_med_name(base: str) -> str:
    """Canonical column naming convention: stat_med exists in canonical table."""
    # prepare_builds uses f"{c}_med"
    return f"{base}_med"


def compute_composites(df: pd.DataFrame) -> pd.DataFrame:
    """Add composite columns (0-100 float) to df in-place and return df."""
    # Prepare list of required med columns
    med_columns = {col_med_name(s) for spec in COMPOSITE_SPECS.values() for s in spec[0]}
    ensure_float_cols(df, med_columns)

    # Precompute arrays of med column names & weights per composite
    specs_med: Dict[str, Tuple[List[str], List[float]]] = {}
    for name, (bases, weights) in COMPOSITE_SPECS.items():
        specs_med[name] = ([col_med_name(b) for b in bases], weights)

    # Row-wise compute
    def row_composite(row: pd.Series, cols: List[str], weights: List[float]) -> float:
        vals = [row.get(c, np.nan) for c in cols]
        return weighted_median(vals, weights)  # may return None -> handled below

    for comp, (cols, weights) in specs_med.items():
        LOGGER.info("Computing composite: %s using cols=%s", comp, cols)
        df[comp] = df.apply(lambda r, c=cols, w=weights: row_composite(r, c, w), axis=1)
        # ensure dtype float and range; keep NaN as-is
        df[comp] = pd.to_numeric(df[comp], errors="coerce").astype(float)

    return df


def compute_percentiles(df: pd.DataFrame, skip: bool = False) -> pd.DataFrame:
    """
    Add per-position and global percentiles for each composite.
    Percentiles are 0-100 and rounded to 2 decimals.
    """
    if skip:
        LOGGER.info("Skipping percentile computation as requested.")
        return df

    comps = list(COMPOSITE_SPECS.keys())
    # global percentiles
    for comp in comps:
        col_pos = f"{comp}_pct_pos"
        col_glob = f"{comp}_pct_global"
        # per-position percentile
        df[col_pos] = df.groupby("position", sort=False)[comp].rank(method="average", pct=True) * 100
        df[col_glob] = df[comp].rank(method="average", pct=True) * 100
        df[col_pos] = df[col_pos].round(2)
        df[col_glob] = df[col_glob].round(2)
        # ensure floats
        df[col_pos] = df[col_pos].astype(float)
        df[col_glob] = df[col_glob].astype(float)

    return df


def primary_role(df: pd.DataFrame) -> pd.DataFrame:
    """Add primary_role (string) and primary_role_score (float) columns."""
    comps = list(COMPOSITE_SPECS.keys())
    # ensure composites exist
    for c in comps:
        if c not in df.columns:
            df[c] = np.nan
    comp_vals = df[comps].astype(float)
    df["primary_role_score"] = comp_vals.max(axis=1)
    # In case of ties, choose first by comps order
    def pick_role(row: pd.Series) -> str:
        vals = row[comps].to_dict()
        if pd.isna(row["primary_role_score"]):
            return ""
        for c in comps:
            if not pd.isna(vals.get(c)) and float(vals.get(c)) == float(row["primary_role_score"]):
                return c.capitalize()  # e.g., "Finishing"
        return ""

    df["primary_role"] = df.apply(pick_role, axis=1)
    # enforce dtypes
    df["primary_role_score"] = df["primary_role_score"].astype(float)
    df["primary_role"] = df["primary_role"].astype(str)
    return df


def build_feature_definitions() -> Dict:
    """Return JSON-serializable feature definitions describing formulas and weights."""
    defs = {}
    for name, (bases, weights) in COMPOSITE_SPECS.items():
        defs[name] = {
            "formula": "weighted_median",
            "inputs": [col_med_name(b) for b in bases],
            "weights": weights,
            "notes": "Missing inputs are ignored and remaining weights re-normalized proportionally.",
        }
    defs["_percentile_method"] = {
        "type": "percentile-rank",
        "range": [0, 100],
        "per_position": "groupby position rank(pct=True)*100",
        "global": "rank(pct=True)*100",
        "rounding": "2 decimals",
    }
    return defs


def analyze_and_report(df: pd.DataFrame) -> Dict:
    """Produce feature report: rows_processed, NaN counts per stat, composite distributions, examples."""
    rows_processed = int(len(df))
    # NaN counts for each stat med column used
    stat_bases = sorted({b for spec in COMPOSITE_SPECS.values() for b in spec[0]})
    stat_meds = [col_med_name(b) for b in stat_bases]
    nan_counts = {c: int(df[c].isna().sum()) if c in df.columns else int(len(df)) for c in stat_meds}

    # distributions for each composite
    comps = list(COMPOSITE_SPECS.keys())
    distributions: Dict[str, Dict[str, Optional[float]]] = {}
    for c in comps:
        if c in df.columns:
            col = pd.to_numeric(df[c], errors="coerce")
            if col.dropna().empty:
                distributions[c] = {"min": None, "median": None, "max": None}
            else:
                distributions[c] = {
                    "min": float(col.min()),
                    "median": float(col.median()),
                    "max": float(col.max()),
                }
        else:
            distributions[c] = {"min": None, "median": None, "max": None}

    # examples: builds with missing or out-of-range fields (up to 10)
    examples = []
    outlier_mask = pd.Series(False, index=df.index)

    # detect missing stats among any of the med stats used
    missing_any = df[stat_meds].isna().any(axis=1) if stat_meds else pd.Series(False, index=df.index)
    out_of_range_any = pd.Series(False, index=df.index)
    for c in stat_meds:
        if c in df.columns:
            out_of_range_any = out_of_range_any | ((df[c] < 0) | (df[c] > 100))
    outlier_mask = missing_any | out_of_range_any

    outlier_indices = df.index[outlier_mask].tolist()
    sample_indices = outlier_indices[:10]
    for idx in sample_indices:
        row = df.loc[idx]
        missing_cols = [c for c in stat_meds if c in df.columns and pd.isna(row[c])]
        out_of_range_cols = [c for c in stat_meds if c in df.columns and not pd.isna(row[c]) and (row[c] < 0 or row[c] > 100)]
        example = {
            "index": int(idx),
            "build_name": str(row.get("build_name", "")),
            "position": str(row.get("position", "")),
            "missing_med_columns": missing_cols,
            "out_of_range_columns": out_of_range_cols,
        }
        examples.append(example)

    # number of builds with any missing stat used for composites
    builds_with_missing_stat = int(missing_any.sum()) if isinstance(missing_any, pd.Series) else 0

    report = {
        "rows_processed": rows_processed,
        "nan_counts_per_stat_med": nan_counts,
        "composite_distributions": distributions,
        "builds_with_missing_stat_used_for_composites": builds_with_missing_stat,
        "examples_of_missing_or_unusual_builds": examples,
    }
    return report


def save_outputs(df: pd.DataFrame, out_dir: Path, force: bool = False) -> None:
    """Save CSV, PKL, feature_definitions.json, feature_report.json to out_dir."""
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = out_dir / "builds_features.csv"
    pkl_path = out_dir / "builds_features.pkl"
    defs_path = out_dir / "feature_definitions.json"
    report_path = out_dir / "feature_report.json"

    # idempotency guard: if files exist and not forcing, abort
    existing = [p for p in (csv_path, pkl_path, defs_path, report_path) if p.exists()]
    if existing and not force:
        LOGGER.error(
            "Output files already exist (%s). Use --force to overwrite.", ", ".join(str(p) for p in existing)
        )
        raise FileExistsError("Outputs exist. Use --force to overwrite.")

    # Write CSV and PKL
    LOGGER.info("Writing CSV to %s", csv_path)
    df.to_csv(csv_path, index=False)
    LOGGER.info("Writing PKL to %s", pkl_path)
    df.to_pickle(pkl_path)

    # feature definitions
    defs = build_feature_definitions()
    with defs_path.open("w", encoding="utf-8") as fh:
        json.dump(defs, fh, indent=2)

    # feature report
    report = analyze_and_report(df)
    with report_path.open("w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)

    LOGGER.info("Saved outputs: %s, %s, %s, %s", csv_path, pkl_path, defs_path, report_path)


def load_input(path: Path) -> pd.DataFrame:
    """Load canonical builds table. Prefer .pkl if path ends with .pkl or pkl sibling exists."""
    if path.suffix.lower() == ".pkl":
        LOGGER.info("Loading pickle: %s", path)
        return pd.read_pickle(path)
    # if csv specified but pkl sibling exists, use pkl for speed/reproducibility
    pkl_sibling = path.with_suffix(".pkl")
    if pkl_sibling.exists():
        LOGGER.info("Found sibling pickle %s; loading it", pkl_sibling)
        return pd.read_pickle(pkl_sibling)
    LOGGER.info("Loading CSV: %s", path)
    df = pd.read_csv(path)
    return df


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Compute feature composites and percentiles for builds.")
    parser.add_argument("--input", "-i", required=True, help="Input canonical file (csv or pkl).")
    parser.add_argument("--output", "-o", required=True, help="Output directory (builds/data).")
    parser.add_argument("--force", action="store_true", help="Overwrite outputs if they exist.")
    parser.add_argument(
        "--skip-percentiles",
        action="store_true",
        help="Skip percentile computation (useful for fast iterative runs).",
    )

    args = parser.parse_args(argv)
    input_path = Path(args.input)
    out_dir = Path(args.output)

    if not input_path.exists():
        LOGGER.error("Input file does not exist: %s", input_path)
        return 2

    try:
        df = load_input(input_path)
    except Exception as exc:
        LOGGER.exception("Failed to load input: %s", exc)
        return 3

    # Validate base columns
    if "build_name" not in df.columns or "position" not in df.columns:
        LOGGER.error("Input missing required columns 'build_name' or 'position'.")
        return 4

    # Ensure positions are strings
    df["position"] = df["position"].astype(str)

    # Compute composites
    df = compute_composites(df)

    # Primary role and score
    df = primary_role(df)

    # Percentiles
    df = compute_percentiles(df, skip=args.skip_percentiles)

    # Ensure numeric columns use float dtype
    # composites and primary_role_score already float; enforce for percentiles
    for c in list(COMPOSITE_SPECS.keys()):
        pct_pos = f"{c}_pct_pos"
        pct_glob = f"{c}_pct_global"
        if pct_pos in df.columns:
            df[pct_pos] = pd.to_numeric(df[pct_pos], errors="coerce").astype(float)
        if pct_glob in df.columns:
            df[pct_glob] = pd.to_numeric(df[pct_glob], errors="coerce").astype(float)
        # round composites to 2 decimals for compactness
        if c in df.columns:
            df[c] = df[c].round(2)

    # Save outputs (also writes report)
    try:
        save_outputs(df, out_dir, force=args.force)
    except FileExistsError:
        return 5
    except Exception:
        LOGGER.exception("Failed to write outputs")
        return 6

    LOGGER.info("Completed. Rows processed: %d", len(df))
    LOGGER.info("Required packages: pandas, numpy")
    return 0


if __name__ == "__main__":
    rc = main()
    sys.exit(rc)