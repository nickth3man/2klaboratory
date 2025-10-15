#!/usr/bin/env python3
"""
scripts/prepare_builds.py

Requirements (pip):
- pandas
- numpy

Purpose:
- Read all CSVs from builds/csv/
- Parse messy numeric fields (single values or ranges), heights (ft/in or cm ranges), weights.
- Normalize column names to snake_case.
- Produce canonical median table:
    builds/data/builds_canonical.csv
    builds/data/builds_canonical.pkl
  and parsing report:
    builds/data/parsing_report.json

CLI:
    python scripts/prepare_builds.py --input builds/csv --output builds/data [--recompute-percentiles]

Notes:
- Idempotent: overwrites outputs on each run.
- Minimal logging included.
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import math
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


NUMERIC_RE = re.compile(r"[-+]?\d+(?:\.\d+)?")
FT_IN_RE = re.compile(r"(?P<ft>\d+)\s*'\s*(?P<in>\d+)")


def to_snake(name: str) -> str:
    """Convert header to snake_case canonical name."""
    name = name.strip()
    name = name.replace("&", "and")
    name = re.sub(r"[^\w\s]", " ", name)
    name = re.sub(r"\s+", "_", name)
    return name.lower().strip("_")


def parse_number_token(token: str) -> Optional[float]:
    """Try to parse a numeric token robustly."""
    if token is None:
        return None
    t = str(token).strip()
    if t == "":
        return None
    # strip percentage and quotes and stray characters
    t = t.replace("%", "")
    t = t.replace('"', "")
    t = t.replace("”", "")
    t = t.replace("“", "")
    t = t.strip()
    # direct numeric
    try:
        return float(t)
    except Exception:
        # fallback extract first numeric substring
        m = NUMERIC_RE.search(t)
        if m:
            try:
                return float(m.group(0))
            except Exception:
                return None
    return None


def ftin_to_inches(s: str) -> Optional[float]:
    """Parse feet/inches string like 7'1\" or 6'11\" and return inches."""
    if not s:
        return None
    m = FT_IN_RE.search(s)
    if not m:
        return None
    try:
        ft = int(m.group("ft"))
        inch = int(m.group("in"))
        return ft * 12 + inch
    except Exception:
        return None


def parse_range_or_single(
    raw: Any, treat_as_cm_if_large: bool = False
) -> Tuple[Optional[float], Optional[float], Optional[float], List[str]]:
    """
    Parse values like:
      - "85" -> (85,85,85)
      - "85-92" -> (85,92,88.5)
      - "85 to 92" -> same
      - "7'0\"" or "6'11\" to 7'4\"" -> converted to inches when treat_as_cm_if_large relevant
      - numeric values >100 are treated as cm (converted to inches) when treat_as_cm_if_large True

    Returns (min, max, median, warnings)
    """
    warnings: List[str] = []
    if pd.isna(raw):
        return None, None, None, warnings
    s = str(raw).strip()
    if s == "":
        return None, None, None, warnings

    # handle explicit feet/inches or ranges with 'to'
    # normalize separators
    s_clean = s.replace("–", "-").replace("—", "-")
    s_clean = s_clean.replace(" to ", " - ").replace("to", " - ")
    parts = [p.strip() for p in re.split(r"[-–—]", s_clean) if p.strip() != ""]
    # if contains ft/in pattern anywhere, parse each part as ft/in
    ftm = FT_IN_RE.search(s_clean)
    if ftm:
        try:
            if len(parts) >= 2:
                vals = []
                for p in parts[:2]:
                    inches = ftin_to_inches(p)
                    if inches is None:
                        warnings.append(f"unparseable ft/in part: {p}")
                    else:
                        vals.append(float(inches))
                if len(vals) == 1:
                    return vals[0], vals[0], float(vals[0]), warnings
                elif len(vals) == 2:
                    mn, mx = min(vals[0], vals[1]), max(vals[0], vals[1])
                    return mn, mx, float((mn + mx) / 2.0), warnings
            else:
                inches = ftin_to_inches(parts[0])
                if inches is not None:
                    return float(inches), float(inches), float(inches), warnings
        except Exception as e:
            warnings.append(f"ft/in parse error: {e}")
    # If not ft/in, try numeric extraction for each part
    nums: List[float] = []
    for p in parts:
        n = parse_number_token(p)
        if n is None:
            # maybe the part contains "220cm" or "220 cm"
            m = NUMERIC_RE.search(p)
            if m:
                try:
                    n = float(m.group(0))
                except Exception:
                    n = None
        if n is None:
            warnings.append(f"unparseable numeric part: {p}")
        else:
            nums.append(n)
    if len(nums) == 0:
        # try to parse any number in original string
        m = NUMERIC_RE.findall(s_clean)
        if m:
            nums = [float(x) for x in m]
    if len(nums) == 0:
        return None, None, None, warnings

    # If only single numeric token provided
    if len(nums) == 1:
        val = nums[0]
        # If treating as cm when too large, convert
        if treat_as_cm_if_large and val > 100:
            inches = val * 0.3937007874
            return float(inches), float(inches), float(inches), warnings
        # if number looks like inches in plausible range
        return float(val), float(val), float(val), warnings

    # Two or more numeric tokens -> take first two as min/max
    a, b = nums[0], nums[1]
    mn, mx = min(a, b), max(a, b)
    # Convert cm to inches if flagged and values large (assume cm if >100)
    if treat_as_cm_if_large and (mn > 100 or mx > 100):
        mn = mn * 0.3937007874
        mx = mx * 0.3937007874
    # If values are plausible inches (<= 96) and treat_as_cm_if_large False, keep as-is
    med = float((mn + mx) / 2.0)
    return float(mn), float(mx), float(med), warnings


def parse_height(raw: Any) -> Tuple[Optional[float], Optional[float], Optional[float], List[str]]:
    """
    Parse height field and return inches: (min_in, max_in, med_in)
    Heuristics:
      - If contains ft/in strings -> parse directly.
      - If numeric tokens > 100 -> treat as cm and convert to inches.
      - Else numeric tokens in 60-90 range -> treat as inches directly.
    """
    warnings: List[str] = []
    if pd.isna(raw):
        return None, None, None, warnings
    s = str(raw).strip()
    if s == "":
        return None, None, None, warnings
    # If hyphenated numeric range but values > 100 treat as cm
    # Use parse_range_or_single with treat_as_cm_if_large True
    mn, mx, med, w = parse_range_or_single(s, treat_as_cm_if_large=True)
    warnings.extend(w)
    # If parse_range_or_single returned values that are absurdly large (>120 inches) then they were likely already inches but wrong;
    # we still accept them but warn.
    if mn is not None and (mn < 20 or mn > 120):
        warnings.append(f"height min suspicious: {mn} inches parsed from '{s}'")
    if mx is not None and (mx < 20 or mx > 120):
        warnings.append(f"height max suspicious: {mx} inches parsed from '{s}'")
    return mn, mx, med, warnings


def parse_weight(raw: Any) -> Tuple[Optional[float], Optional[float], Optional[float], List[str]]:
    """Parse weight field: assume lbs for typical numbers; ranges supported."""
    warnings: List[str] = []
    if pd.isna(raw):
        return None, None, None, warnings
    s = str(raw).strip()
    if s == "":
        return None, None, None, warnings
    mn, mx, med, w = parse_range_or_single(s, treat_as_cm_if_large=False)
    warnings.extend(w)
    # Validate plausible lbs
    if mn is not None and (mn < 90 or mn > 400):
        # Some entries may be in kg (rare). If <90 maybe kg; convert if small (<90) and looks like kg
        if mn < 90:
            # treat as kg -> lbs
            mn_lbs = mn * 2.2046226218
            if mx is not None:
                mx_lbs = mx * 2.2046226218
            else:
                mx_lbs = mn_lbs
            med_lbs = float((mn_lbs + mx_lbs) / 2.0)
            warnings.append(f"interpreted weight {s} as kg converted to lbs")
            return float(mn_lbs), float(mx_lbs), float(med_lbs), warnings
        else:
            warnings.append(f"weight suspicious value: {mn} (raw: {s})")
    return mn, mx, med, warnings


def parse_stat(raw: Any) -> Tuple[Optional[float], Optional[float], Optional[float], List[str]]:
    """Parse an arbitrary stat field into min,max,median (numeric)."""
    return parse_range_or_single(raw, treat_as_cm_if_large=False)


def discover_input_files(input_dir: Path) -> List[Path]:
    files = sorted([p for p in input_dir.glob("*.csv") if p.is_file()])
    return files


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare canonical builds table from CSVs")
    parser.add_argument("--input", "-i", required=True, help="Input directory (builds/csv)")
    parser.add_argument("--output", "-o", required=True, help="Output directory (builds/data)")
    parser.add_argument(
        "--recompute-percentiles",
        action="store_true",
        help="(placeholder) compute per-position percentiles for stats after canonicalization",
    )
    args = parser.parse_args(argv)

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    files = discover_input_files(input_dir)
    if not files:
        logger.error("No CSV files found in %s", input_dir)
        return 2
    logger.info("Found %d CSV files", len(files))

    # Read all CSVs, keep raw strings
    df_list = []
    for f in files:
        logger.info("Reading %s", f)
        try:
            df = pd.read_csv(f, dtype=str)
            df["source_file"] = str(f.name)
            df_list.append(df)
        except Exception as e:
            logger.error("Failed to read %s: %s", f, e)
    if not df_list:
        logger.error("No dataframes loaded.")
        return 2
    raw = pd.concat(df_list, ignore_index=True, sort=False).fillna("")

    # Normalize column names to snake_case
    orig_cols = list(raw.columns)
    col_map: Dict[str, str] = {}
    for c in orig_cols:
        col_map[c] = to_snake(c)
    raw = raw.rename(columns=col_map)

    # Required canonical columns
    canonical_cols = [
        "build_name",
        "position",
        "height_min_in",
        "height_max_in",
        "height_med_in",
        "weight_min_lb",
        "weight_max_lb",
        "weight_med_lb",
    ]
    # stat columns: everything other than build_name,position,height,weight,source_file
    excluded = {"build_name", "position", "height", "weight", "source_file"}
    stat_columns = [c for c in raw.columns if c not in excluded]
    # But remove any non-stat columns that were created (like source_file already excluded)
    # We'll create med columns for each stat column (originally snake_case names like close_shot)
    stat_med_columns: List[str] = []
    for c in stat_columns:
        if c in ("height", "weight"):
            continue
        stat_med_columns.append(f"{c}_med")

    # Prepare output rows
    rows: List[Dict[str, Any]] = []
    warnings_accum: List[Dict[str, Any]] = []
    total_rows = len(raw)
    logger.info("Processing %d rows", total_rows)
    for idx, r in raw.iterrows():
        row_out: Dict[str, Any] = {}
        # base fields
        row_out["build_name"] = r.get("build_name", "").strip()
        row_out["position"] = r.get("position", "").strip()
        # parse height
        h_raw = r.get("height", "")
        h_min, h_max, h_med, w_h = parse_height(h_raw)
        row_out["height_min_in"] = None if h_min is None else round(float(h_min), 2)
        row_out["height_max_in"] = None if h_max is None else round(float(h_max), 2)
        row_out["height_med_in"] = None if h_med is None else round(float(h_med), 2)
        # parse weight
        wt_raw = r.get("weight", "")
        w_min, w_max, w_med, w_w = parse_weight(wt_raw)
        row_out["weight_min_lb"] = None if w_min is None else round(float(w_min), 2)
        row_out["weight_max_lb"] = None if w_max is None else round(float(w_max), 2)
        row_out["weight_med_lb"] = None if w_med is None else round(float(w_med), 2)
        # parse each stat as median
        for c in stat_columns:
            if c in ("height", "weight"):
                continue
            raw_val = r.get(c, "")
            s_min, s_max, s_med, s_w = parse_stat(raw_val)
            col_med = f"{c}_med"
            row_out[col_med] = None if s_med is None else round(float(s_med), 2)
            # accumulate any warnings
            if s_w:
                warnings_accum.append(
                    {
                        "row_index": int(idx),
                        "build_name": row_out.get("build_name"),
                        "column": c,
                        "raw_value": raw_val,
                        "warnings": s_w,
                    }
                )
        # add height/weight warnings
        if w_h:
            warnings_accum.append({"row_index": int(idx), "build_name": row_out.get("build_name"), "column": "height", "raw_value": h_raw, "warnings": w_h})
        if w_w:
            warnings_accum.append({"row_index": int(idx), "build_name": row_out.get("build_name"), "column": "weight", "raw_value": wt_raw, "warnings": w_w})

        rows.append(row_out)

    canon_df = pd.DataFrame(rows)

    # Re-order columns: canonical cols first, then stat med columns sorted
    stat_med_cols_sorted = sorted([c for c in canon_df.columns if c not in canonical_cols and c not in ("build_name", "position")])
    final_cols = ["build_name", "position"] + canonical_cols[2:]  # height/weight med fields are included below
    # ensure we include exact canonical order
    final_cols = ["build_name", "position", "height_min_in", "height_max_in", "height_med_in", "weight_min_lb", "weight_max_lb", "weight_med_lb"]
    final_cols += stat_med_cols_sorted
    # Some columns might be missing if parsing removed them; intersect
    final_cols = [c for c in final_cols if c in canon_df.columns]
    canon_df = canon_df[final_cols]

    # Save CSV and pickle
    csv_path = output_dir / "builds_canonical.csv"
    pkl_path = output_dir / "builds_canonical.pkl"
    report_path = output_dir / "parsing_report.json"

    canon_df.to_csv(csv_path, index=False)
    canon_df.to_pickle(pkl_path)
    logger.info("Wrote canonical CSV: %s", csv_path)
    logger.info("Wrote canonical PKL: %s", pkl_path)

    # Build parsing report
    warnings_examples = warnings_accum[:200]  # cap examples
    parsing_report: Dict[str, Any] = {
        "source_files": [str(p.name) for p in files],
        "rows_processed": int(total_rows),
        "parsing_warnings_count": len(warnings_accum),
        "parsing_warnings_examples": warnings_examples,
        "stat_columns_median_count": len(stat_med_cols_sorted),
    }
    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump(parsing_report, fh, indent=2)
    logger.info("Wrote parsing report: %s", report_path)

    if args.recompute_percentiles:
        logger.info("--recompute-percentiles requested: placeholder (not implemented)")

    logger.info("Done. Rows processed: %d. Warnings: %d", total_rows, len(warnings_accum))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())