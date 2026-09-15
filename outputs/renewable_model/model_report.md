# Renewable Generation Forecast Model Report

## Solar Model
* Features: Lags, rolling means, current weather, and properly aligned forecast weather
* Base features: 17
* Negative predictions: CLIPPED to 0 automatically.

## Wind Model
* Features: Lags, rolling means, current weather, and properly aligned forecast weather
* Base features: 15
* Negative predictions: CLIPPED to 0 automatically.

## Horizon Comparison (Test Split)

| Horizon | Solar MAE | Solar RMSE | Solar MAPE | Wind MAE | Wind RMSE | Wind MAPE |
| ------- | --------: | ---------: | ---------: | -------: | --------: | --------: |
| 15m     | 8.20 | 16.06 | 7.61% | 3.95 | 10.62 | 61.52% |
| 30m     | 10.69 | 20.20 | 10.58% | 5.09 | 13.65 | 95.15% |
| 60m     | 14.18 | 26.85 | 15.28% | 7.57 | 19.22 | 169.55% |

*(Note: Solar MAPE only computed for periods where actual generation > 0.1 MW to prevent instability).*

## Baseline Comparison (60m Horizon Test Split)
* Solar Baseline MAE: 61.44
* Solar Model MAE: 14.18
* Wind Baseline MAE: 19.26
* Wind Model MAE: 7.57

## Zone Performance (60m Horizon Test Split MAE)
* Solar ZONE_A: 15.85 MW
* Solar ZONE_B: 12.51 MW
* Wind ZONE_A: 12.29 MW
* Wind ZONE_B: 2.85 MW

## Top Features (60m Models)
### Solar
              feature  importance
  solar_generation_mw    0.732007
                 hour    0.112571
         humidity_pct    0.073243
       fcst_cloud_60m    0.020658
solar_rolling_mean_6h    0.012144
       irradiance_wm2    0.010301
          solar_lag_4    0.009514
         solar_lag_96    0.004397
               minute    0.004387
        fcst_temp_60m    0.003806

### Wind
             feature  importance
  wind_generation_mw    0.759923
wind_rolling_mean_1h    0.115793
       fcst_wind_60m    0.055756
wind_rolling_mean_6h    0.014565
       wind_speed_ms    0.013186
          wind_lag_1    0.006642
                hour    0.005066
          wind_lag_4    0.004956
         wind_lag_96    0.004804
       temperature_c    0.004526

## Leakage
* Future leakage: NO (Used only exact shifted target forecasts from t-3h to emulate true prediction-time knowledge).
* Ground-truth leakage: NO.

## Integration
* Successfully merged with PATH 3 demand predictions to calculate `predicted_net_load_60m`. PATH 3 model was NOT retrained.

PATH 4 STATUS: PASS
