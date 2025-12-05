#!/usr/bin/env python3
"""
Apply the Milestone 4 control heuristic to inverter telemetry.

Usage:
    PYTHONPATH=. python src/scripts/control/apply_control_heuristic.py \
        --input src/notebooks/clean/inverter_labeled_1hz.csv \
        --classifier models/advanced/gb_overheat.joblib \
        --regressor models/advanced/gbr_deltaT.joblib \
        --output predictions/advanced/control_actions.csv

Outputs a CSV with:
- timestamp
- gb_overheat_prob, gb_overheat_pred, gb_delta_T_pred
- suggested_derate_pct (0–50)
- rationale
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from joblib import load

from src.scripts.training.train_boosted_models import add_temporal_features


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
        "--output",
        default=None,
        help="Output CSV path; prints head if omitted.",
    )
    parser.add_argument(
        "--p1",
        type=float,
        default=0.7,
        help="Probability threshold for mild derate (default: %(default)s)",
    )
    parser.add_argument(
        "--p2",
        type=float,
        default=0.9,
        help="Probability threshold for strong derate (default: %(default)s)",
    )
    parser.add_argument(
        "--dt1",
        type=float,
        default=8.0,
        help="ΔT threshold (°C) for mild derate (default: %(default)s)",
    )
    parser.add_argument(
        "--dt2",
        type=float,
        default=3.0,
        help="ΔT threshold (°C) for safe region (default: %(default)s)",
    )
    parser.add_argument(
        "--temp-ceil",
        type=float,
        default=65.0,
        help="Hot-spot temperature ceiling for strong derate (default: %(default)s)",
    )
    parser.add_argument(
        "--mild-derate",
        type=float,
        default=25.0,
        help="Suggested mild derate percent (default: %(default)s)",
    )
    parser.add_argument(
        "--strong-derate",
        type=float,
        default=45.0,
        help="Suggested strong derate percent (default: %(default)s)",
    )
    return parser.parse_args()


def load_artifact(path: Path):
    artifact = load(path)
    return artifact["model"], artifact.get("metadata", {})


def apply_heuristic(
    p_overheat: float,
    delta_t: float,
    hot_temp: float,
    args: argparse.Namespace,
) -> tuple[float, str]:
    """Return (derate_pct, rationale) based on heuristic thresholds."""
    if p_overheat >= args.p2 or hot_temp >= args.temp_ceil:
        return args.strong_derate, "high risk or temp over ceiling"
    if p_overheat >= args.p1 and delta_t >= args.dt1:
        return args.mild_derate, "elevated risk and rising temp"
    if p_overheat < 0.3 and delta_t < args.dt2:
        return 0.0, "low risk and stable temp"
    return args.mild_derate / 2, "moderate risk"


def run(args: argparse.Namespace) -> pd.DataFrame:
    df = pd.read_csv(args.input, parse_dates=["timestamp"])
    df_feat = add_temporal_features(df)

    clf, clf_meta = load_artifact(Path(args.classifier))
    reg, reg_meta = load_artifact(Path(args.regressor))

    clf_features = clf_meta.get("feature_columns")
    reg_features = reg_meta.get("feature_columns")
    if clf_features is None or reg_features is None:
        raise ValueError("Model artifacts missing feature_columns metadata.")

    probs = clf.predict_proba(df_feat[clf_features])[:, 1]
    preds_cls = clf.predict(df_feat[clf_features])
    preds_dt = reg.predict(df_feat[reg_features])

    hot_temp = df_feat["inv_hot_spot_temp_mean"].to_numpy()

    derates = []
    rationales = []
    for p, d, t in zip(probs, preds_dt, hot_temp):
        pct, why = apply_heuristic(p, d, t, args)
        derates.append(pct)
        rationales.append(why)

    out = pd.DataFrame(
        {
            "timestamp": df_feat["timestamp"],
            "gb_overheat_prob": probs,
            "gb_overheat_pred": preds_cls,
            "gb_delta_T_pred": preds_dt,
            "inv_hot_spot_temp_mean": hot_temp,
            "suggested_derate_pct": derates,
            "rationale": rationales,
        }
    )

    if "overheat_label" in df_feat.columns:
        out["overheat_label"] = df_feat["overheat_label"]
    if "delta_T_30s" in df_feat.columns:
        out["delta_T_30s"] = df_feat["delta_T_30s"]

    return out


def main() -> None:
    args = parse_args()
    actions = run(args)
    if args.output:
        out_path = Path(args.output)
        if out_path.parent.is_file():
            out_path.parent.unlink()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        actions.to_csv(out_path, index=False)
        print(f"Wrote control actions to {out_path}")
    else:
        print(actions.head())


if __name__ == "__main__":
    main()
