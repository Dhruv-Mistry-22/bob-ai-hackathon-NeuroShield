import pandas as pd
import numpy as np

def modify_and_report():
    print("Loading data...")
    grid = pd.read_csv('data/grid_timeseries.csv')
    forecast = pd.read_csv('data/weather_forecast.csv')
    assets = pd.read_csv('data/renewable_assets.csv')
    
    # 1. WEATHER FORECAST
    forecast['irradiance_forecast_wm2'] = np.clip(forecast['irradiance_forecast_wm2'], 0, None)
    forecast['cloud_cover_forecast_pct'] = np.clip(forecast['cloud_cover_forecast_pct'], 0, 100)
    
    # 2. RESERVE MARGIN
    # Recalculate based on demand spike flag
    def recalc_reserve(row):
        if row['demand_spike_ground_truth'] == 1:
            return np.random.uniform(2, 8)
        else:
            return np.random.uniform(10, 20)
            
    grid['reserve_margin_pct'] = grid.apply(recalc_reserve, axis=1)
    
    # 3. CURTAILMENT EVENTS
    # During grid_curtailment, transmission_flow_mw approaches transmission_capacity_mw
    curt_mask = grid['curtailment_event_ground_truth'] == 1
    
    # Set transmission flow near capacity during these events
    num_curt = curt_mask.sum()
    if num_curt > 0:
        grid.loc[curt_mask, 'transmission_flow_mw'] = grid.loc[curt_mask, 'transmission_capacity_mw'] * np.random.uniform(0.95, 0.99, size=num_curt)
        
    # Ensure curtailment formula is strict: curtailment_mw = renewable_available_mw - renewable_dispatched_mw
    grid['curtailment_mw'] = grid['renewable_available_mw'] - grid['renewable_dispatched_mw']
    # Round to avoid float precision issues making it negative
    grid['curtailment_mw'] = grid['curtailment_mw'].apply(lambda x: max(0, x))
    
    # 4. ASSET ANOMALY LABELS
    # Do not label nighttime zero-generation periods as meaningful asset anomalies.
    night_mask = (assets['expected_power_kw'] < 1.0)
    assets.loc[night_mask, 'anomaly_ground_truth'] = 0
    
    # Save modified datasets
    print("Saving modified datasets...")
    grid.to_csv('data/grid_timeseries.csv', index=False)
    forecast.to_csv('data/weather_forecast.csv', index=False)
    assets.to_csv('data/renewable_assets.csv', index=False)
    
    # Create the report
    neg_irr = (forecast['irradiance_forecast_wm2'] < 0).sum()
    cc_out = ((forecast['cloud_cover_forecast_pct'] < 0) | (forecast['cloud_cover_forecast_pct'] > 100)).sum()
    
    rm_min = grid['reserve_margin_pct'].min()
    rm_max = grid['reserve_margin_pct'].max()
    rm_mean = grid['reserve_margin_pct'].mean()
    
    curt_rows = grid[curt_mask]
    curt_events = len(curt_rows)
    avg_trans_util = (curt_rows['transmission_flow_mw'] / curt_rows['transmission_capacity_mw']).mean() * 100 if curt_events > 0 else 0
    avg_curt = curt_rows['curtailment_mw'].mean() if curt_events > 0 else 0
    
    fp_night = assets[(assets['expected_power_kw'] < 1.0) & (assets['anomaly_ground_truth'] == 1)]
    nighttime_fp = len(fp_night)
    
    anomaly_counts = assets[assets['anomaly_ground_truth'] == 1].groupby('asset_id').size().to_dict()
    root_causes = assets[assets['anomaly_ground_truth'] == 1]['root_cause_ground_truth'].unique().tolist()
    
    resources = pd.read_csv('data/grid_resources.csv')
    
    violations = 0
    if (grid['battery_soc_pct'] < 19.99).any() or (grid['battery_soc_pct'] > 95.01).any(): violations += 1
    if (grid['curtailment_mw'] < -0.01).any(): violations += 1
    if (grid['renewable_dispatched_mw'] > grid['renewable_available_mw'] + 0.1).any(): violations += 1
    if (grid['transmission_flow_mw'] > grid['transmission_capacity_mw'] + 0.1).any(): violations += 1
    if (assets['actual_power_kw'] > assets['capacity_kw'] + 1).any(): violations += 1
    if (assets['expected_power_kw'] > assets['capacity_kw'] + 1).any(): violations += 1
    if (assets['performance_ratio'] < 0).any(): violations += 1
    if ((grid['battery_charge_mw'] > 0) & (grid['battery_discharge_mw'] > 0)).sum() > 0: violations += 1
    
    dups = grid.duplicated().sum() + assets.duplicated().sum() + resources.duplicated().sum() + forecast.duplicated().sum()
    
    status = "PASS" if violations == 0 and neg_irr == 0 and cc_out == 0 and nighttime_fp == 0 else "FAIL"
    
    report = f'''Grid rows: {len(grid)}
Asset rows: {len(assets)}
Resource rows: {len(resources)}
Weather rows: {len(forecast)}

Negative irradiance values: {neg_irr}
Cloud cover outside [0,100]: {cc_out}
Reserve margin min: {rm_min:.2f}%
Reserve margin max: {rm_max:.2f}%
Reserve margin mean: {rm_mean:.2f}%

Curtailment event rows: {curt_events}
Average transmission utilization during curtailment: {avg_trans_util:.2f}%
Average curtailment: {avg_curt:.2f} MW

Nighttime false-positive anomaly labels: {nighttime_fp}
Asset anomaly counts by asset: {anomaly_counts}
Root causes: {root_causes}

Physical constraint violations: {violations}
Duplicate rows: {dups}

Dataset status:
{status}'''

    print(report)

if __name__ == "__main__":
    modify_and_report()
