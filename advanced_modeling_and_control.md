# Advanced Modeling & Control – Milestone 4

Source: `src/notebooks/clean/inverter_labeled_1hz.csv` with temporal features from `add_temporal_features`. Models trained via Gradient Boosting (tree-based) using chronological 80/20 split.

## Metrics
- Overheat classifier (GradientBoostingClassifier)
  - Test AUC: **0.9995**
  - Test F1 (overheat class): **0.9688**
  - Train/Test samples: 2 633 / 659
- ΔT regressor (GradientBoostingRegressor)
  - Test MAE: **1.307 °C**
  - Test RMSE: **3.869 °C**
  - Train/Test samples: 2 633 / 659

## Top Features (importance)
- Classifier: `inv_hot_spot_temp_mean_prev`, `inv_coolant_temp_mean`, `inv_module_c_temp_mean`, `inv_module_a_temp_mean`, `inv_module_b_temp_mean`, `inv_dc_bus_current_mean`, `inv_control_board_temp_mean`, `inv_phase_b_current_mean`, `inv_phase_c_current_mean`, `delta_T_30s_prev`.
- Regressor: `delta_T_30s_prev`, `inv_control_board_temp_mean`, `inv_hot_spot_temp_mean`, `inv_gate_driver_board_temp_mean`, `inv_module_c_temp_max`, `inv_hot_spot_temp_min`, `inv_dc_bus_voltage_mean`, `inv_coolant_temp_min`, `inv_module_c_temp_mean`, `inv_gate_driver_board_temp_max`.

## Control Heuristics (torque derate)
- Let `p_overheat` be classifier probability and `ΔT_pred` the regressor’s 30 s forecast.
- Suggested thresholds:
  - If `p_overheat > 0.7` **and** `ΔT_pred > 8 °C`: derate torque ~20–30% for ~30 s; optionally cap DC current.
  - If `p_overheat > 0.9` **or** hot-spot temp > 65 °C: stronger derate (40–50%) plus warning.
  - If `p_overheat < 0.3` **and** `ΔT_pred < 3 °C`: no derate.
- Plots in `src/notebooks/03_advanced_modeling.ipynb` illustrate time-series alignment and probability–ΔT control regions.

## Usage
- Train + generate summary: `make advanced` (runs `train_boosted_models.py`, writes models/metrics and this doc).
- Inference: `PYTHONPATH=. python src/scripts/inference/predict_boosted.py --input src/notebooks/clean/inverter_labeled_1hz.csv --output predictions/advanced/advanced_predictions.csv`.
- Control heuristic CLI: `PYTHONPATH=. python src/scripts/control/apply_control_heuristic.py --input src/notebooks/clean/inverter_labeled_1hz.csv --output predictions/advanced/control_actions.csv`.
- Notebook: `src/notebooks/03_advanced_modeling.ipynb` reproduces training, metrics, and visuals; rerun after data/model updates.
- QA + plots: `make advanced_qa` checks AUC/F1/Recall/MAE/RMSE thresholds, validates control derate recall/rate, and refreshes `docs/advanced_prob_vs_temp.png` + `docs/advanced_control_regions.png`.
