# PATH 7: Grid Risk and Curtailment Prediction

## 1. Objective
Use real-time grid state + PATH 3 demand forecast + PATH 4 renewable forecast to predict 60-minute ahead grid transmission stress and curtailment events.

## 2. Inputs & Feature Engineering
- **Future Net Load**: `predicted_demand_60m - predicted_total_renewable_60m`
- **Future Penetration**: `predicted_total_renewable_60m / predicted_demand_60m`
- Current zone-level transmission headroom and utilization were passed directly into the model to simulate actual operating context.

## 3. Grid Risk Model
- Formulated as a multi-class prediction (LOW, MEDIUM, HIGH, CRITICAL) using `XGBClassifier` based on transmission quantiles.
- Test Accuracy: 0.886 (Persistence Baseline: 0.799)

## 4. Curtailment Risk Model
- Curtailment events > 10 MW were framed as binary targets.
- ROC-AUC: 0.957
- PR-AUC: 0.748

## 5. Event Validation
| Event | Start | Detected | First Warning | Lead Time (mins) | Max Prob | Max Actual MW |
|-------|-------|----------|---------------|------------------|----------|---------------|
| EV_CT_3 | 2026-01-08 11:00:00 | True | 2026-01-08 10:00:00 | 60.0 | 0.977 | 759.5 |
| EV_CT_4 | 2026-01-25 12:00:00 | True | 2026-01-25 11:00:00 | 60.0 | 0.924 | 355.1 |

## 6. Top Features
**Grid Risk**:
| Feature | Importance |
|---------|------------|
| predicted_demand_mw | 0.2767 |
| predicted_total_renewable_60m | 0.1854 |
| transmission_utilization | 0.1299 |
| predicted_solar_60m | 0.1242 |
| total_resource_capacity_mw | 0.0535 |

**Curtailment Risk**:
| Feature | Importance |
|---------|------------|
| predicted_total_renewable_60m | 0.5729 |
| predicted_solar_60m | 0.0994 |
| predicted_demand_mw | 0.0495 |
| demand_mw | 0.0490 |
| solar_generation_mw | 0.0399 |

## 7. Leakage Validation
* Future leakage: NO
* Ground-truth leakage: NO
* Temporal leakage: NO
* Test-set threshold tuning: NO

PATH 7 STATUS: PASS
