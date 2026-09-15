# PATH 7: Grid Risk and Curtailment Prediction

## 1. Objective
Use real-time grid state + PATH 3 demand forecast + PATH 4 renewable forecast to predict 60-minute ahead grid transmission stress and curtailment events.

## 2. Inputs & Feature Engineering
- **Future Net Load**: `predicted_demand_60m - predicted_total_renewable_60m`
- **Future Penetration**: `predicted_total_renewable_60m / predicted_demand_60m`
- Current zone-level transmission headroom and utilization were passed directly into the model to simulate actual operating context.

## 3. Grid Risk Model
- Formulated as a multi-class prediction (LOW, MEDIUM, HIGH, CRITICAL) using `XGBClassifier` based on transmission quantiles.
- Test Accuracy: 0.883 (Persistence Baseline: 0.800)

## 4. Curtailment Risk Model
- Curtailment events > 10 MW were framed as binary targets.
- ROC-AUC: 0.947
- PR-AUC: 0.723

## 5. Event Validation
| Event | Start | Detected | First Warning | Lead Time (mins) | Max Prob | Max Actual MW |
|-------|-------|----------|---------------|------------------|----------|---------------|
| EV_CT_3 | 2026-01-08 11:00:00 | True | 2026-01-08 10:00:00 | 60.0 | 0.974 | 759.5 |
| EV_CT_4 | 2026-01-25 12:00:00 | True | 2026-01-25 11:00:00 | 60.0 | 0.955 | 355.1 |

## 6. Top Features
**Grid Risk**:
| Feature | Importance |
|---------|------------|
| predicted_demand_mw | 0.2989 |
| predicted_total_renewable_60m | 0.1843 |
| transmission_utilization | 0.1312 |
| predicted_solar_60m | 0.1228 |
| transmission_headroom_mw | 0.0458 |

**Curtailment Risk**:
| Feature | Importance |
|---------|------------|
| predicted_total_renewable_60m | 0.5535 |
| predicted_solar_60m | 0.0896 |
| solar_generation_mw | 0.0538 |
| demand_mw | 0.0499 |
| future_renewable_penetration_60m | 0.0466 |

## 7. Leakage Validation
* Future leakage: NO
* Ground-truth leakage: NO
* Temporal leakage: NO
* Test-set threshold tuning: NO

PATH 7 STATUS: PASS
