## DS3000 Battery Analyzer – Design Document

### 1. Project Overview
- **Purpose**: Detect and predict inverter overheating or power-delivery anomalies by correlating temperature readings with current draw, phase currents, and motor speed. Provide both historical analysis (offline model) and a lightweight control concept for live data.
- **Scope**: Use the provided inverter telemetry (temps, DC voltage/current, phase currents, torque & speed) stored under `data/`. Build a training/evaluation pipeline plus a prototype inference routine that could ingest a live stream.

### 2. Requirements & Success Criteria
- **Core model**: Learn a mapping from electrical load indicators (phase currents, DC bus current, speed) to temperature outcomes. Support two modes:
  1. Classification (safe vs. overheating risk) with adjustable thresholds.
  2. Regression predicting future temperature delta under a forecasted current draw.
- **Explainability**: Produce feature importance or SHAP-style rationale for operational insight.
- **Control heuristic**: Document (and optionally implement) a feedback rule that adjusts current draw/power request to keep predicted temperatures under a configurable ceiling.
- **Performance targets**: ≥90% recall for overheating-risk classification on validation splits and ≤2 °C MAE for short-horizon temperature forecasts (targets can be revised after baseline).
- **Operational deliverables**: Cleaned dataset artifacts, reusable training scripts/notebooks, evaluation report, and README instructions for running inference.

### 3. Data Inventory (from `data/`)
| File | Signals | Notes |
| --- | --- | --- |
| `Inverter Temps-data-as-joinbyfield-2025-10-03 17_39_12.csv` | Control board temp, coolant temp, gate driver temp, module temps (A/B/C), hotspot | Primary dependent variables; need unit verification and sensor alignment. |
| `Inverter Voltage and Current-data-as-joinbyfield-2025-10-03 17_38_50.csv` | DC bus voltage/current | Ensure units parsed (values include text like `Volts`, `Amps`). |
| `Inverter Phase Currents-data-as-joinbyfield-2025-10-03 17_38_30.csv` | Three phase currents | Likely in Amps; time stamps align with other logs. |
| `Torque & Motor Speed-data-2025-10-03 18_30_00.csv` | Motor speed (RPM) | Currently zeroed; verify additional torque columns or future logs. |

### 4. System Architecture & Workflow
1. **Data ingestion layer**: Standardize CSV parsing (strip BOM, convert units, harmonize timestamps). Output parquet/clean CSV for downstream work.
2. **Data quality & exploratory analysis**: Visualize correlations, detect missing data, derive target labels (e.g., `temp_hotspot > threshold`).
3. **Feature engineering**:
   - Aggregate rolling statistics (mean, slope) over 1–5 sec windows.
   - Derive combined load indicators (e.g., RMS phase current, power estimates from voltage×current, mechanical power via torque×speed).
   - Encode ambient/contextual variables (coolant temp baseline, control board temp).
4. **Model training**:
   - Baseline algorithms: Linear regression/logistic regression and gradient boosted trees.
   - Hyperparameter search using cross-validation or time-based splits.
   - Track metrics via MLflow/W&B (optional) or simple CSV logs.
5. **Evaluation & validation**:
   - Hold-out validation covering different drive cycles.
   - Stress-test predictions under simulated current spikes.
   - Generate confusion matrices, ROC, MAE charts.
6. **Inference & control prototype**:
   - Batch inference script (`predict.py`) taking CSV input.
   - Optional streaming loop reading from stdin/socket to emulate live data.
   - Control heuristic outputs recommended current derate percentage when overheating risk exceeds threshold.
7. **Deployment/readiness artifacts**:
   - Documented reproducible pipeline commands.
   - Summary report describing findings and control recommendations.

### 5. Milestones & Collaborative Task Breakdown

#### Milestone 1 – Data Audit & Infrastructure (Owner: Data Engineering)
- Parse each CSV, remove `sep=,` lines/BOM, ensure consistent datetime format.
- Build a notebook or script that merges datasets on timestamp.
- Define naming conventions, folder structure (`notebooks/`, `src/`, `models/`), and environment requirements.

#### Milestone 2 – Exploratory Analysis & Target Definition (Owner: Analytics)
- Produce EDA notebook with plots (heatmaps, time-series overlays).
- Establish overheating thresholds (e.g., hotspot > 60 °C) and generate binary labels.
- Quantify class imbalance, detect missing/zeroed sensors (e.g., motor speed zeros) and document mitigation strategies.

#### Milestone 3 – Baseline Modeling (Owner: Modeling Team A)
- Implement baseline regression/classification using scikit-learn.
- Create reusable preprocessing pipelines (scaling, feature selection).
- Log baseline metrics and error analysis; identify key influential signals.

#### Milestone 4 – Advanced Modeling & Control Logic (Owner: Modeling Team B)
- Experiment with tree-based methods (XGBoost/LightGBM) or simple RNN if sequential context needed.
- Introduce feature importance/SHAP analysis for interpretability.
- Design and prototype control heuristic translating predicted risk into current derates; document algorithm and edge cases.

#### Milestone 5 – Integration, Validation, and Reporting (Owner: Integration)
- Package training & inference scripts with CLI arguments.
- Run end-to-end tests using held-out slices; verify `npm test` for any JS components if UI hooks exist.
- Draft final report/presentation summarizing methodology, metrics, control recommendations, and future work.

### 6. Collaboration Guidelines
- **Version control**: Separate feature branches per milestone; open PRs with linked tasks.
- **Artifacts**: Store intermediate datasets in `artifacts/` (git-ignored) and commit configs/scripts only.
- **Meet cadence**: Weekly sync to unblock, ad-hoc async updates through issue tracker.
- **Handoffs**: Each milestone owner delivers documentation + runnable scripts/tests before the next milestone begins.

### 7. Risks & Mitigations
- **Sparse/zero motor speed data**: Plan to simulate wheel-speed scenarios or gather more logs; otherwise down-weight feature.
- **Data drift**: Keep ingestion modular to drop in newer CSVs; document schema.
- **Model generalization**: Use cross-session validation to avoid overfitting to a single timestamp batch.
- **Control safety**: Treat recommendations as advisory; include guardrails to prevent aggressive power cuts.
