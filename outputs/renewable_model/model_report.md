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
| 15m     | 9.22 | 17.66 | 7.93% | 4.02 | 10.81 | 59.73% |
| 30m     | 11.47 | 20.96 | 10.15% | 5.15 | 14.26 | 89.69% |
| 60m     | 15.06 | 27.90 | 15.17% | 6.98 | 18.29 | 152.50% |

*(Note: Solar MAPE only computed for periods where actual generation > 0.1 MW to prevent instability).*

## Baseline Comparison (60m Horizon Test Split)
* Solar Baseline MAE: 64.86
* Solar Model MAE: 15.06
* Wind Baseline MAE: 18.72
* Wind Model MAE: 6.98

## Zone Performance (60m Horizon Test Split MAE)
* Solar ZONE_A: 16.29 MW
* Solar ZONE_B: 13.82 MW
* Wind ZONE_A: 11.32 MW
* Wind ZONE_B: 2.64 MW

## Top Features (60m Models)
### Solar
              feature  importance
  solar_generation_mw    0.731564
                 hour    0.113076
         humidity_pct    0.064468
       fcst_cloud_60m    0.020396
       irradiance_wm2    0.019472
solar_rolling_mean_6h    0.013569
       fcst_irrad_60m    0.005101
          solar_lag_4    0.004745
         solar_lag_96    0.004576
        fcst_temp_60m    0.004259

### Wind
             feature  importance
  wind_generation_mw    0.804899
wind_rolling_mean_1h    0.070581
       fcst_wind_60m    0.055141
wind_rolling_mean_6h    0.014878
       wind_speed_ms    0.013518
          wind_lag_1    0.007275
          wind_lag_4    0.005687
       temperature_c    0.005531
         wind_lag_96    0.004820
                hour    0.004453

## Leakage
* Future leakage: NO (Used only exact shifted target forecasts from t-3h to emulate true prediction-time knowledge).
* Ground-truth leakage: NO.

## Integration
* Successfully merged with PATH 3 demand predictions to calculate `predicted_net_load_60m`. PATH 3 model was NOT retrained.

PATH 4 STATUS: PASS
