## Data Dictionary – DS3000 Battery Analyzer (1 Hz Merged Dataset)

Source file: `src/notebooks/clean/inverter_labeled_1hz.csv` generated via:
1. `PYTHONPATH=. python src/scripts/merge_inverter_data.py`
2. `PYTHONPATH=. python src/labels.py`

### Timestamp & Sample Metadata
| Column | Description | Units/Notes |
| --- | --- | --- |
| `timestamp` | ISO timestamp at 1 Hz | 2025‑06‑03 18:56:10 → 19:59:25 |
| `phase_raw_sample_count` | Number of raw phase-current samples contributing to this second | Count (1–10) |
| `temps_raw_sample_count` | Number of raw temperature samples in this second | Count (1–10) |
| `dc_raw_sample_count` | Raw DC voltage/current samples in this second | Count (1–10) |

### Electrical Features
| Column Pattern | Description | Units |
| --- | --- | --- |
| `inv_dc_bus_voltage_mean/min/max` | DC bus voltage statistics | Volts |
| `inv_dc_bus_current_mean/min/max` | DC bus current statistics | Amps |
| `inv_phase_[abc]_current_mean/min/max` | Inverter phase currents | Amps |

### Thermal Features
| Column Pattern | Description | Units |
| --- | --- | --- |
| `inv_hot_spot_temp_mean/min/max/count` | Inverter hot-spot temperature | °C |
| `inv_coolant_temp_mean/min/max/count` | Coolant temperature at inverter | °C |
| `inv_control_board_temp_*` | Control board temperature | °C |
| `inv_gate_driver_board_temp_*` | Gate driver board temperature | °C |
| `inv_module_[abc]_temp_*` | Module A/B/C temperatures | °C |

### Labels & Targets
| Column | Description | Definition |
| --- | --- | --- |
| `overheat_label` | Binary overheating risk label | 1 if `inv_hot_spot_temp_mean ≥ 65 °C`, else 0 (see `src/labels.py`) |
| `inv_hot_spot_temp_future` | Hot-spot temperature 30 s in the future | `shift(-30)` of `inv_hot_spot_temp_mean`; NaN for final 30 seconds |
| `delta_T_30s` | Future temperature delta | `inv_hot_spot_temp_future − inv_hot_spot_temp_mean` |

### Derived Metrics & Notes
- Idle vs load classification (used in class-balance report) is based on `|inv_dc_bus_current_mean| ≤ 0.1 A`.
- No motor-speed signal exists for June 3 data; torque features remain unavailable.
- Missing data: only a single second lacks module/gate-driver temperature stats; final 30 seconds lack future-delta targets by design.

### Decision Log
- **Overheat threshold**: set to 65 °C (based on inspection of hot-spot trends; captures upper ~3 % of data). Adjust in `LabelConfig` if operations dictate a different limit.
- **Future horizon**: 30 seconds to balance actionable warning window vs. data availability (gives 3 294 labeled points, dropping final 30 seconds).
- **Aggregation statistics**: mean/min/max/count per sensor to retain sub-second variability without keeping raw logs.

For deeper exploratory results and plots, see `src/notebooks/01_eda_template.ipynb` and the `docs/class_balance_and_sensor_report.md`.
