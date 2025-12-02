## DS3000 Battery Analyzer

Early warning system for inverter overheating and power-delivery anomalies. We ingest inverter telemetry (temperatures, DC bus voltage/current, phase currents, and optional torque/speed) to train models that forecast thermal issues and recommend power-derating actions.

### Repository Layout
- `src/`
  - `data_loading.py` – CSV ingestion utilities (handles BOM, `sep=,`, unit stripping, canonical names).
  - `aggregation.py` – Timestamp parsing + 1 Hz aggregation helpers.
  - `scripts/` – CLI tools:
    - `merge_inverter_data.py` – Builds unified per-second dataset from June 3 logs.
    - `qa_merged_data.py` – Quality checks (row counts, missing data, ranges).
    - `validate_data_loading.py` – Confirms loader/aggregation on current `data/` contents.
  - `clean/` – Generated artifacts (currently `inverter_merged_1hz.csv`).
- `data/` – Raw CSV exports from the inverter logger.
- `tests/` – `unittest` coverage for loader and aggregation utilities (`PYTHONPATH=. python -m unittest discover tests`).
- `DESIGN.md` – Project requirements, milestones, collaboration plan.
- `AGENTS.md` – Working agreements and scope reminders.
- `pyproject.toml` – Editable install definition (use `PYTHONPATH=.` if pip install isn’t available).

### Key Goals
1. **Data Pipeline (Milestone 1)** – Standardize ingestion, produce clean 1 Hz dataset, automate QA (done; document assumptions next).
2. **EDA + Target Definition (Milestone 2)** – Analyze thermal/electrical relationships, set overheating thresholds, label data.
3. **Baseline Modeling (Milestone 3)** – Train logistic/linear baselines with reproducible scripts and metrics.
4. **Advanced Modeling & Control (Milestone 4)** – Boosted trees/temporal models, interpretability, derive control heuristics.
5. **Integration & Reporting (Milestone 5)** – Package CLI/inference workflow, validate end-to-end, deliver final report.

Refer to `DESIGN.md` §5 for detailed tasks, owners, and acceptance criteria per milestone.

### Quick Start
1. Activate the venv and set project root on `PYTHONPATH`:
   ```bash
   source venv/bin/activate
   export PYTHONPATH=.
   ```
2. Regenerate merged dataset:
   ```bash
   python src/scripts/merge_inverter_data.py --output src/clean/inverter_merged_1hz.csv
   ```
3. Run QA:
   ```bash
   python src/scripts/qa_merged_data.py --input src/clean/inverter_merged_1hz.csv
   ```
4. Execute tests:
   ```bash
   python -m unittest discover tests
   ```

### Next Milestone Checklist
- Document cleaning assumptions in `README_cleaning.md` (commands, unit conversions, missing-value handling).
- Launch EDA notebook and label-generation module per `DESIGN.md`.
- Capture open questions (e.g., missing torque data) so later milestones can address them.
