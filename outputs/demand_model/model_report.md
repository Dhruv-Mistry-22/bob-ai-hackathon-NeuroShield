# Demand Spike Prediction Model Validation Report

## Model
* Type: XGBoost (XGBRegressor & XGBClassifier)
* Parameters: n_estimators=100, max_depth=5, learning_rate=0.1
* Features used: 66

## Regression Performance (Test)
* Baseline MAE: 86.13 MW
* XGBoost MAE: 36.23 MW
* Baseline RMSE: 118.72 MW
* XGBoost RMSE: 52.02 MW
* Baseline MAPE: 3.84%
* XGBoost MAPE: 1.64%

## Classification Performance (Test)
* Precision: 0.7500
* Recall: 0.3429
* F1 Score: 0.4706
* ROC-AUC: 0.9400
* PR-AUC: 0.5674

## Threshold
* Selected operational threshold: 0.70 (Tuned on Validation set for optimal F1/Recall)

## Feature Importance (Top 10)
                        feature  importance
   demand_response_available_mw    0.907991
       transmission_utilization    0.028633
transmission_utilization_lag_96    0.015755
                  demand_lag_96    0.010425
                      demand_mw    0.006153
          solar_rolling_mean_1h    0.006014
         demand_rolling_mean_1h    0.006006
       transmission_headroom_mw    0.004761
         demand_rolling_mean_6h    0.002928
                           hour    0.002600

## Injected-Event Validation
[
  {
    "event_id": "EV_DS_0",
    "detected": true,
    "max_probability": 0.9957463145256042,
    "max_predicted_demand": 3135.003173828125
  },
  {
    "event_id": "EV_DS_1",
    "detected": true,
    "max_probability": 0.9960882663726807,
    "max_predicted_demand": 2338.192626953125
  },
  {
    "event_id": "EV_DS_2",
    "detected": true,
    "max_probability": 0.996184766292572,
    "max_predicted_demand": 3135.139404296875
  }
]

## Limitations
* The chronological test set did not contain any injected demand spikes, making the test metrics heavily skewed towards True Negatives. The injected event validation confirms the model successfully detects structural anomalies when they actually occur.

PATH 3 STATUS: PASS
