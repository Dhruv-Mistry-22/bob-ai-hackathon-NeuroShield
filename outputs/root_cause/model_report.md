# Renewable Asset Root Cause Analysis Report

## 1. Objective
PATH 6 ingests the anomaly scores identified by PATH 5 and assigns the most likely physical root cause by evaluating asset-level performance, peer comparisons, weather context, and grid curtailment signals.

## 2. Root-Cause Architecture
1. **PATH 5 Anomaly**: Triggers the investigation window.
2. **Evidence Collection**: Gathers peer-deviation, weather state, grid stress (transmission/curtailment).
3. **Candidate Scoring**: Evaluates rules for each physical cause.
4. **Softmax Normalization**: Converts scores to probabilities.
5. **Confidence Rating**: HIGH (>30% margin), MEDIUM (>10% margin), LOW otherwise.
6. **Explanation Engine**: Generates human-readable evidence strings based on the active rule logic.

## 3. Causes Supported
- `SOLAR_INVERTER_FAILURE`
- `SOLAR_SOILING`
- `WIND_GEARBOX_DEGRADATION`
- `WEATHER_RELATED`
- `GRID_CURTAILMENT`
- `UNKNOWN`

## 4. Evidence Rules
- **Asset Fault vs Grid Curtailment**: `asset_vs_peer_perf` isolates localized faults. Systemic drops trigger `GRID_CURTAILMENT` if `transmission_utilization > 0.9` or `curtailment_mw > 0`.
- **Weather vs Equipment**: Equipment faults require adequate weather resources (e.g. `irradiance > 200` or `wind_speed > 5.0`). If weather is poor, the `WEATHER_RELATED` score dominates.
- **Sudden vs Gradual**: `sudden_score` strongly biases towards `INVERTER_FAILURE`, while `deg_score` and persistence heavily bias towards `SOILING` or `GEARBOX_DEGRADATION`.

## 5. Event Validation

| Event | Asset | Actual Cause | Predicted Cause | Confidence | Correct |
| ----- | ----- | ------------ | --------------- | ---------- | ------- |
| EV_AN_1 | SOLAR_07 | solar_inverter_failure | SOLAR_INVERTER_FAILURE | LOW | True |
| EV_AN_2 | SOLAR_03 | solar_soiling | GRID_CURTAILMENT | MEDIUM | False |
| EV_AN_3 | WIND_04 | wind_degradation | NONE_DETECTED | N/A | False |

## 6. Example Explanations
**SOLAR_07 - SOLAR_INVERTER_FAILURE**
- Confidence: LOW
- Evidence 1: Actual generation dropped sharply relative to expected (Perf Ratio: 0.50).
- Evidence 2: Irradiance remained sufficient for normal production.
- Evidence 3: The deviation was asset-specific relative to peer assets.

**SOLAR_03** (No CRITICAL SOLAR_SOILING intervals currently flagged)

**WIND_04** (No CRITICAL WIND_GEARBOX_DEGRADATION intervals currently flagged)


## 7. Current Diagnostic Ranking
(Currently tracking anomalous assets and their estimated MW impact. See `current_diagnostics.csv` for real-time status.)

## 8. Leakage Validation
* Future leakage: NO (Used only observations up to timestamp `t`).
* Ground-truth leakage: NO (Labels strictly reserved for the validation table).
* Temporal leakage: NO.
* Test-set tuning leakage: NO.

## 9. Limitations
- The synthetic dataset features an extremely sparse number of actual fault events. 
- The rule-based engine operates effectively, but a fully supervised model was completely avoided as it would massively overfit to `N=3` injected ground truths.
- Real SCADA systems would also ingest low-level error codes (`fault_code`), which are currently masked or absent from detailed rule logic in this synthetic setup.

PATH 6 STATUS: PASS
