#!/usr/bin/env python3
"""
Validate control heuristic outputs against overheat labels.

Usage:
    PYTHONPATH=. python src/scripts/qa/validate_control_actions.py \
        --input src/notebooks/clean/inverter_labeled_1hz.csv \
        --classifier models/advanced/gb_overheat.joblib \
        --regressor models/advanced/gbr_deltaT.joblib

Checks:
- Derate recall on overheat seconds vs threshold (default: 0.90).
- Optional cap on overall derate rate (default: 0.5).
Prints summary stats; exits non-zero on failure.
"""

from __future__ import annotations

import argparse
import sys

import pandas as pd

from src.scripts.control.apply_control_heuristic import run as run_control


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        default="src/notebooks/clean/inverter_labeled_1hz.csv",
        help="Path to labeled dataset (default: %(default)s)",
    )
    parser.add_argument(
        "--classifier",
        default="models/advanced/gb_overheat.joblib",
        help="Path to saved classifier artifact (default: %(default)s)",
    )
    parser.add_argument(
        "--regressor",
        default="models/advanced/gbr_deltaT.joblib",
        help="Path to saved regressor artifact (default: %(default)s)",
    )
    parser.add_argument(
        "--min-derate-recall",
        type=float,
        default=0.90,
        help="Minimum fraction of overheat seconds with a derate applied (default: %(default)s)",
    )
    parser.add_argument(
        "--max-derate-rate",
        type=float,
        default=0.50,
        help="Maximum allowed overall derate rate (default: %(default)s)",
    )
    parser.add_argument(
        "--strong-derate-threshold",
        type=float,
        default=40.0,
        help="Threshold (%%) to count as strong derate in summary (default: %(default)s)",
    )
    return parser.parse_args()


def summarize(actions: pd.DataFrame, args: argparse.Namespace) -> dict:
    derate_flag = actions["suggested_derate_pct"] > 0
    strong_flag = actions["suggested_derate_pct"] >= args.strong_derate_threshold

    n_total = len(actions)
    derate_rate = derate_flag.mean() if n_total else 0.0
    strong_rate = strong_flag.mean() if n_total else 0.0

    summary = {
        "n_total": n_total,
        "derate_rate": derate_rate,
        "strong_rate": strong_rate,
    }

    if "overheat_label" in actions.columns:
        overheat_flag = actions["overheat_label"] == 1
        n_overheat = overheat_flag.sum()
        if n_overheat > 0:
            recall = (derate_flag & overheat_flag).sum() / n_overheat
        else:
            recall = 1.0

        # Precision when derating (how many derates coincide with overheat)
        n_derate = derate_flag.sum()
        if n_derate > 0:
            precision = (derate_flag & overheat_flag).sum() / n_derate
        else:
            precision = 1.0

        summary.update(
            {
                "n_overheat": int(n_overheat),
                "derate_recall_on_overheat": recall,
                "derate_precision": precision,
            }
        )
    else:
        summary["warning"] = "overheat_label missing; recall/precision unavailable"

    return summary


def main() -> int:
    args = parse_args()
    # Ensure control thresholds exist on args for reuse in apply_control_heuristic.run
    defaults = {
        "p1": 0.7,
        "p2": 0.9,
        "dt1": 8.0,
        "dt2": 3.0,
        "temp_ceil": 65.0,
        "mild_derate": 25.0,
        "strong_derate": 45.0,
    }
    for key, val in defaults.items():
        if not hasattr(args, key):
            setattr(args, key, val)

    actions = run_control(args)

    summary = summarize(actions, args)
    failures = []

    if "derate_recall_on_overheat" in summary:
        recall = summary["derate_recall_on_overheat"]
        if recall < args.min_derate_recall:
            failures.append(
                f"derate recall {recall:.3f} < min_derate_recall {args.min_derate_recall}"
            )

    if summary["derate_rate"] > args.max_derate_rate:
        failures.append(
            f"derate_rate {summary['derate_rate']:.3f} > max_derate_rate {args.max_derate_rate}"
        )

    if failures:
        print("[control-qa] FAIL:")
        for msg in failures:
            print(f"  - {msg}")
        # Show summary for debugging
        print(f"Summary: {summary}")
        return 1

    print(
        "[control-qa] PASS: "
        f"derate_rate={summary['derate_rate']:.3f}, "
        f"strong_rate={summary['strong_rate']:.3f}, "
        f"derate_recall={summary.get('derate_recall_on_overheat', 'n/a')}, "
        f"derate_precision={summary.get('derate_precision', 'n/a')}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
