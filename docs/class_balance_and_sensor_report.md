## Class Balance & Sensor Health Report (Milestone 2)

Data source: `src/notebooks/clean/inverter_labeled_1hz.csv` (1 Hz aggregates from 2025‑06‑03 18:56:10 → 19:59:25).

### 1. Thermal Risk Labels
| Label | Definition | Seconds | Percent |
| --- | --- | --- | --- |
| `0` | Hot-spot temp < 65 °C | 3 226 | 97.05 % |
| `1` | Hot-spot temp ≥ 65 °C | 98 | 2.95 % |

- Labeling logic: `overheat_label = (inv_hot_spot_temp_mean >= 65)` using `src/labels.py`.
- Future delta target (`delta_T_30s`) exists for 3 294 rows (30 future samples unavailable at the end of the window).

### 2. Operating Regimes (Based on DC Bus Current)
- Idle threshold: |`inv_dc_bus_current_mean`| ≤ 0.1 A.
- Idle seconds: 1 698 (51.08 %)
- Load seconds: 1 626 (48.92 %)

Implication: dataset is nearly balanced between idle and load, but overheating events are rare (~3 %). Sampling strategies should account for this imbalance (e.g., class-weighting or focused resampling).

### 3. Sensor Coverage & Missing Data
| Sensor Group | Missing Seconds | Notes |
| --- | --- | --- |
| Gate driver board temps (`*_count/max/mean/min`) | 1 | Single dropout; consider interpolation or dropping that second. |
| Module A/B/C temps (`*_count/max/mean/min`) | 1 each | Aligns with the same missing second as gate driver temps. |
| `inv_hot_spot_temp_future`, `delta_T_30s` | 30 | Expected because the last 30 seconds cannot form a full 30 s horizon. |
| Motor speed | Not present | No aligned torque/speed data for June 3 session. |

No other columns exhibit missing values. Phase currents and DC currents are fully populated.

### 4. Key Takeaways
- Overheating label imbalance (3 % positive) requires careful model evaluation (recall/f1 emphasis).
- Approximately half the dataset represents idle conditions; consider stratifying by load status during model training.
- Temperature sensor dropouts are minimal (1 second); decide whether to forward-fill or drop affected rows before modeling.
- Motor speed signal remains unavailable; coordinate with data collection team if this feature is required for future milestones.
