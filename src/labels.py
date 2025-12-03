"""Label generation utilities for Milestone 2."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd


@dataclass
class LabelConfig:
    merged_path: Path = Path("src/notebooks/clean/inverter_merged_1hz.csv")
    output_path: Path = Path("src/notebooks/clean/inverter_labeled_1hz.csv")
    overheat_threshold: float = 65.0  # Celsius
    delta_horizon_seconds: int = 30   # 30-second look-ahead at 1 Hz


def apply_labels(df: pd.DataFrame, config: LabelConfig) -> pd.DataFrame:
    """Return a copy of df with label columns added."""
    result = df.copy()
    result["overheat_label"] = (result["inv_hot_spot_temp_mean"] >= config.overheat_threshold).astype(int)

    future_col = "inv_hot_spot_temp_future"
    result[future_col] = result["inv_hot_spot_temp_mean"].shift(-config.delta_horizon_seconds)
    result["delta_T_30s"] = result[future_col] - result["inv_hot_spot_temp_mean"]

    return result


def load_and_label(config: Optional[LabelConfig] = None) -> pd.DataFrame:
    cfg = config or LabelConfig()
    df = pd.read_csv(cfg.merged_path, parse_dates=["timestamp"])
    labeled = apply_labels(df, cfg)
    labeled.to_csv(cfg.output_path, index=False)
    return labeled


if __name__ == "__main__":
    load_and_label()
