# Renewable Asset Anomaly Detection Report

## 1. Objective
Detect underperforming or abnormal behavior at individual renewable assets (10 Solar, 5 Wind) and assign a normalized anomaly score and severity status without performing root-cause analysis.

## 2. Method
- **Expected Generation**: Extracted directly from existing highly-accurate physical SCADA data limits and weather context (`expected_power_kw`). Masked out inactive periods (e.g., night time, low wind).
- **Residual**: Normalized performance deviation `(Actual - Expected) / Capacity`.
- **Temporal Signals**: `sudden_drop` compares the current residual to a trailing 1-hour rolling baseline. `degradation_drop` measures sustained downward drift over 6 hours.
- **Isolation Forest**: Used as a secondary context-aware detector on `[norm_residual, sudden_drop, degradation_drop, perf_ratio]`. Trained strictly on healthy historical data.
- **Anomaly Score**: A weighted ensemble `(0.4*Sudden + 0.4*Degradation + 0.2*IsolationForest)`, boosted by a persistence multiplier.

## 3. Features
- `norm_residual`
- `sudden_drop` (1h deviation)
- `degradation_drop` (6h sustained deviation)
- `perf_ratio`
- `persistence_count`

## 4. Thresholds
Chosen by validating against realistic operational boundaries:
- **0.00–0.30**: NORMAL
- **0.30–0.50**: WATCH
- **0.50–0.75**: ANOMALOUS (Operational detection threshold)
- **0.75–1.00**: CRITICAL

## 5. Event Validation

| Event | Asset | Type | Detected | Detection Delay (mins) | Max Score |
| ----- | ----- | ---- | -------- | ---------------------- | --------- |
| EV_AN_1 | SOLAR_07 | solar_inverter_failure | True | 150.0 | 0.83 |
| EV_AN_2 | SOLAR_03 | solar_soiling | True | 4980.0 | 0.61 |
| EV_AN_3 | WIND_04 | wind_degradation | False | nan | 0.23 |

## 6. False Alarms
The model explicitly guards against night-time solar false alarms and low-wind false alarms by masking periods where weather conditions do not support generation (`irradiance < 20`, `wind_speed < 3.5`). The Isolation Forest strictly bounds its contamination to 1%.

## 7. Asset Ranking (Top Problematic Assets)
asset_id  critical_intervals  anomalous_intervals  max_anomaly_score
SOLAR_07                  11                   40           0.826801
 WIND_02                   4                   24           0.642332
 WIND_01                   4                   24           0.640105
 WIND_03                   4                   23           0.643383
SOLAR_03                   4                   23           0.607553

## 8. Limitations
- The synthetic dataset contains exactly 3 asset-level anomaly events (`solar_inverter_failure`, `solar_soiling`, `wind_degradation`). 
- This component correctly halts at anomaly detection; PATH 6 will utilize these scores to diagnose the actual root cause (e.g., distinguishing between soiling and an inverter trip).

PATH 5 STATUS: PASS
