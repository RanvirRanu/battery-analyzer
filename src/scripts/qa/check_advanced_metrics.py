#!/usr/bin/env python3
"""
Check advanced model metrics against simple thresholds.

Usage:
    PYTHONPATH=. python src/scripts/qa/check_advanced_metrics.py \
        --cls-metrics metrics/gb_overheat_metrics.json \
        --reg-metrics metrics/gbr_deltaT_metrics.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cls-metrics",
        default="metrics/gb_overheat_metrics.json",
        help="Path to classifier metrics JSON (default: %(default)s)",
    )
    parser.add_argument(
        "--reg-metrics",
        default="metrics/gbr_deltaT_metrics.json",
        help="Path to regressor metrics JSON (default: %(default)s)",
    )
    parser.add_argument(
        "--min-auc",
        type=float,
        default=0.98,
        help="Minimum acceptable AUC for the classifier (default: %(default)s)",
    )
    parser.add_argument(
        "--min-f1",
        type=float,
        default=0.90,
        help="Minimum acceptable F1 for the overheat class (default: %(default)s)",
    )
    parser.add_argument(
        "--min-recall",
        type=float,
        default=0.90,
        help="Minimum acceptable recall for the overheat class (default: %(default)s)",
    )
    parser.add_argument(
        "--max-mae",
        type=float,
        default=2.0,
        help="Maximum acceptable MAE (°C) for the regressor (default: %(default)s)",
    )
    parser.add_argument(
        "--max-rmse",
        type=float,
        default=5.0,
        help="Maximum acceptable RMSE (°C) for the regressor (default: %(default)s)",
    )
    return parser.parse_args()


def load_metrics(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    args = parse_args()
    cls_metrics = load_metrics(Path(args.cls_metrics))
    reg_metrics = load_metrics(Path(args.reg_metrics))

    failures = []

    auc = cls_metrics.get("auc")
    if auc is None or auc < args.min_auc:
        failures.append(f"classifier AUC {auc} < {args.min_auc}")

    f1 = cls_metrics.get("f1")
    if f1 is None or f1 < args.min_f1:
        failures.append(f"classifier F1 {f1} < {args.min_f1}")

    recall = cls_metrics.get("recall")
    if recall is None or recall < args.min_recall:
        failures.append(f"classifier recall {recall} < {args.min_recall}")

    mae = reg_metrics.get("mae")
    if mae is None or mae > args.max_mae:
        failures.append(f"regressor MAE {mae} > {args.max_mae}")

    rmse = reg_metrics.get("rmse")
    if rmse is None or rmse > args.max_rmse:
        failures.append(f"regressor RMSE {rmse} > {args.max_rmse}")

    if failures:
        print("[advanced-qa] FAIL:")
        for msg in failures:
            print(f"  - {msg}")
        return 1

    print(
        "[advanced-qa] PASS: "
        f"AUC={auc:.4f} F1={f1:.4f} Recall={recall:.4f} "
        f"MAE={mae:.3f} RMSE={rmse:.3f}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
