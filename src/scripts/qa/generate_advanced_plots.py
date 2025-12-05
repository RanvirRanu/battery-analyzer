#!/usr/bin/env python3
"""
Generate advanced-model plots for docs:
- Time-series: GB overheat probability vs hot-spot temperature.
- Control regions: probability vs ΔT prediction.

Usage:
    PYTHONPATH=. python src/scripts/qa/generate_advanced_plots.py \
        --input src/notebooks/clean/inverter_labeled_1hz.csv \
        --classifier models/advanced/gb_overheat.joblib \
        --regressor models/advanced/gbr_deltaT.joblib \
        --output-dir docs
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

if "MPLCONFIGDIR" not in os.environ:
    mpl_dir = Path(".matplotlib_cache")
    mpl_dir.mkdir(exist_ok=True)
    os.environ["MPLCONFIGDIR"] = str(mpl_dir.resolve())

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
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
        "--output-dir",
        default="docs",
        help="Directory to save plots (default: %(default)s)",
    )
    parser.add_argument(
        "--tail-window",
        type=int,
        default=600,
        help="Number of most recent samples to plot in the time-series view (default: %(default)s)",
    )
    return parser.parse_args()


def load_artifact(path: Path):
    artifact = load(path)
    return artifact["model"], artifact.get("metadata", {})


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.input, parse_dates=["timestamp"])
    df_feat = add_temporal_features(df)

    clf, clf_meta = load_artifact(Path(args.classifier))
    reg, reg_meta = load_artifact(Path(args.regressor))

    clf_features = clf_meta.get("feature_columns")
    reg_features = reg_meta.get("feature_columns")
    if clf_features is None or reg_features is None:
        raise ValueError("Model artifacts missing feature_columns metadata.")

    preds = pd.DataFrame(
        {
            "timestamp": df_feat["timestamp"],
            "gb_overheat_prob": clf.predict_proba(df_feat[clf_features])[:, 1],
            "gb_overheat_pred": clf.predict(df_feat[clf_features]),
            "gb_delta_T_pred": reg.predict(df_feat[reg_features]),
            "inv_hot_spot_temp_mean": df_feat["inv_hot_spot_temp_mean"],
        }
    )
    preds["delta_T_30s"] = df_feat.get("delta_T_30s")

    # Plot 1: time-series probability vs temperature
    ts = preds.tail(args.tail_window)
    fig, ax1 = plt.subplots(figsize=(12, 4))
    ax1.plot(ts["timestamp"], ts["gb_overheat_prob"], color="tab:red", label="GB overheat prob")
    ax1.axhline(0.7, color="tab:red", linestyle="--", alpha=0.4, label="p=0.7")
    ax1.set_ylabel("Probability", color="tab:red")
    ax1.set_xlabel("Timestamp")
    ax2 = ax1.twinx()
    ax2.plot(ts["timestamp"], ts["inv_hot_spot_temp_mean"], color="tab:blue", alpha=0.7, label="Hot-spot temp")
    ax2.axhline(65, color="tab:blue", linestyle="--", alpha=0.4, label="T=65°C")
    ax2.set_ylabel("Temp (°C)", color="tab:blue")
    ax1.set_title("GB Overheat Probability vs Hot-spot Temperature")
    fig.tight_layout()
    (output_dir / "advanced_prob_vs_temp.png").parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_dir / "advanced_prob_vs_temp.png", dpi=200)
    plt.close(fig)

    # Plot 2: control regions scatter
    fig, ax = plt.subplots(figsize=(6, 5))
    scatter = ax.scatter(
        preds["gb_overheat_prob"],
        preds["gb_delta_T_pred"],
        c=preds["inv_hot_spot_temp_mean"],
        cmap="viridis",
        s=10,
    )
    ax.axvline(0.7, color="red", linestyle="--", label="p_overheat=0.7")
    ax.axhline(8, color="orange", linestyle="--", label="ΔT=8°C")
    ax.set_xlabel("GB overheat probability")
    ax.set_ylabel("GB ΔT prediction (°C)")
    ax.set_title("Control Heuristic Zones")
    cbar = fig.colorbar(scatter, label="Hot-spot temp (°C)")
    cbar.ax.tick_params(labelsize=8)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "advanced_control_regions.png", dpi=200)
    plt.close(fig)

    print(f"[advanced-plots] Wrote plots to {output_dir}")


if __name__ == "__main__":
    main()
