## DS3000 Battery Analyzer Agent Notes

1. **Environment** – Use the `venv` already checked in for Python work and prefer `pnpm` if you need to add Node dependencies.
2. **Testing** – Run `npm test` after every change to JavaScript/TypeScript files; add or update tests when you touch model logic.
3. **Model scope** – Core task is to train a model that correlates temperature, current flow, and optional wheel-speed signals to flag overheating/power-delivery anomalies.
4. **Prediction goal** – Use the trained model to forecast how current draw affects temperature and outline strategies for throttling/adjusting power draw to avoid overheating.
5. **Live-data angle** – If time permits, prototype a loop that accepts streaming sensor data and surfaces warnings or suggested power adjustments; documentation of the approach is acceptable if implementation is rough.
