# GridPulse AI Dataset
This dataset represents a synthetic regional electricity grid for MVP development.

## Zones
* ZONE_A: High demand, higher capacity.
* ZONE_B: Medium demand.

## Files
* `grid_timeseries.csv`: Grid-level metrics every 15 minutes.
* `renewable_assets.csv`: Individual solar/wind asset telemetry.
* `grid_resources.csv`: Controllable assets for optimization.
* `weather_forecast.csv`: Weather forecast (4-hours ahead).
* `injected_events.csv`: Ground truth of events for evaluation.

## Injected Events
- Demand Spikes (Extreme weather/load)
- Grid Curtailments (Transmission limits)
- Solar Inverter Faults (High temp)
- Solar Soiling (Gradual performance loss)
- Wind Gearbox Degradation
