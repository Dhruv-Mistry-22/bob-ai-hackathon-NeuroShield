import os
import pandas as pd
import numpy as np

def validate():
    report = []
    def log(msg):
        print(msg)
        report.append(msg)
        
    try:
        grid = pd.read_csv('data/grid_timeseries.csv')
        assets = pd.read_csv('data/renewable_assets.csv')
        forecast = pd.read_csv('data/weather_forecast.csv')
        resources = pd.read_csv('data/grid_resources.csv')
        events = pd.read_csv('data/injected_events.csv')
        
        log("Grid rows: " + str(len(grid)))
        log("Asset rows: " + str(len(assets)))
        log("Resource rows: " + str(len(resources)))
        log("Weather forecast rows: " + str(len(forecast)))
        log("")
        
        log("Solar assets: " + str(len(assets[assets['asset_type'] == 'solar']['asset_id'].unique())))
        log("Wind assets: " + str(len(assets[assets['asset_type'] == 'wind']['asset_id'].unique())))
        log("Zones: " + str(len(grid['zone_id'].unique())))
        log("")
        
        log("Demand spike events: " + str(len(events[events['event_type'] == 'demand_spike'])))
        log("Asset anomaly events: " + str(len(events[events['event_type'].isin(['solar_inverter_failure', 'solar_soiling', 'wind_degradation'])])))
        log("Curtailment events: " + str(len(events[events['event_type'] == 'grid_curtailment'])))
        log("")
        
        # Missing values & Duplicates
        dups = grid.duplicated().sum() + assets.duplicated().sum() + resources.duplicated().sum()
        log("Missing values: Expected NaNs for non-battery resources")
        log("Duplicate rows: " + str(dups))
        
        # Violations check
        violations = 0
        if (grid['battery_soc_pct'] < 19.99).any() or (grid['battery_soc_pct'] > 95.01).any():
            log("Violation: battery_soc_pct out of bounds")
            violations += 1
        if (grid['curtailment_mw'] < -0.01).any():
            log("Violation: curtailment_mw < 0")
            violations += 1
        if (grid['renewable_dispatched_mw'] > grid['renewable_available_mw'] + 0.1).any():
            log("Violation: dispatched > available")
            violations += 1
        if (grid['transmission_flow_mw'] > grid['transmission_capacity_mw']).any():
            log("Violation: transmission flow > capacity")
            violations += 1
        
        if (assets['actual_power_kw'] > assets['capacity_kw'] + 1).any():
            log("Violation: actual power > capacity")
            violations += 1
        if (assets['expected_power_kw'] > assets['capacity_kw'] + 1).any():
            log("Violation: expected power > capacity")
            violations += 1
        if (assets['performance_ratio'] < 0).any():
            log("Violation: performance ratio < 0")
            violations += 1
        
        simultaneous = ((grid['battery_charge_mw'] > 0) & (grid['battery_discharge_mw'] > 0)).sum()
        if simultaneous > 0:
            log("Violation: simultaneous charge and discharge")
            violations += 1
        
        log("Physical constraint violations: " + str(violations))
        log("")
        
        if violations == 0 and dups == 0:
            log("Dataset status:\nPASS")
        else:
            log("Dataset status:\nFAIL")
            
        with open('data/data_quality_report.txt', 'w') as f:
            f.write('\n'.join(report))
            
    except Exception as e:
        log("Validation failed due to error: " + str(e))
        log("Dataset status:\nFAIL")
        with open('data/data_quality_report.txt', 'w') as f:
            f.write('\n'.join(report))

if __name__ == "__main__":
    validate()
