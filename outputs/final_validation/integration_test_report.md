# Integration Test Report

## Status: PASS

### Raw Data Integrity
- Evaluated physical rows, schema definitions, missing columns, and null constraints in `test_data_integrity.py`. All raw features pass structural criteria.

### Pipeline Execution
- The full 8-module pipeline executed synchronously via `run_pipeline.py`.
- No module failed. Total runtime was less than 60 seconds (recorded in `runtime_report.json`).

### Cross-Path Consistency
- **Temporal Check**: Verified `decision_time` vs `forecast_target_time` is exactly +60 minutes without data drift.
- **Numerical Assertion**: Output from PATH 3, PATH 4, PATH 7, PATH 8 and PATH 9 correctly surfaced to Operator Brief (PATH 10) context payload within float tolerance (<1e-4).

### Optimization Safety Tests
- Battery action limits physically bounded and valid. Dispatch actions do not exceed limits. Solvers report optimal.

### Simulation Integrity Tests
- PATH 9 accurately re-simulates and identifies physical overload events that the baseline avoided, thus generating the adverse counterfactual without silencing the finding. 
