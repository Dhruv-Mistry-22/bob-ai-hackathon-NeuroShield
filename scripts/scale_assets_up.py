import pandas as pd
import numpy as np

def scale_up_dataset():
    print("Loading data...")
    grid = pd.read_csv('data/grid_timeseries.csv')
    assets = pd.read_csv('data/renewable_assets.csv')
    resources = pd.read_csv('data/grid_resources.csv')
    forecast = pd.read_csv('data/weather_forecast.csv')
    
    np.random.seed(42)
    
    # 1. Assign new huge capacities to assets
    asset_new_caps = {}
    for aid in assets['asset_id'].unique():
        typ = assets[assets['asset_id'] == aid]['asset_type'].iloc[0]
        if typ == 'solar':
            asset_new_caps[aid] = np.random.uniform(100000, 250000)
        else:
            asset_new_caps[aid] = np.random.uniform(100000, 300000)
            
    # 2. Scale asset outputs
    old_caps = assets.groupby('asset_id')['capacity_kw'].first().to_dict()
    scale_factors = assets['asset_id'].map(lambda x: asset_new_caps[x] / old_caps[x])
    
    assets['capacity_kw'] = assets['asset_id'].map(asset_new_caps)
    assets['expected_power_kw'] *= scale_factors
    
    # Restore actual_power_kw base (since previous run overwrote it during curtailment)
    assets['actual_power_kw'] = assets['expected_power_kw'].copy()
    
    # Apply anomalies
    # SOLAR_03 soiling
    s3_mask = (assets['asset_id'] == 'SOLAR_03') & (assets['anomaly_ground_truth'] == 1)
    days = np.array([int(ts[8:10]) for ts in assets['timestamp']])
    assets.loc[s3_mask, 'actual_power_kw'] *= (1.0 - 0.2 * (days[s3_mask] / 30.0))
    
    # SOLAR_07 inverter
    s7_mask = (assets['asset_id'] == 'SOLAR_07') & (assets['anomaly_ground_truth'] == 1)
    assets.loc[s7_mask, 'actual_power_kw'] *= 0.5
    
    # WIND_04 gearbox
    w4_mask = (assets['asset_id'] == 'WIND_04') & (assets['anomaly_ground_truth'] == 1)
    assets.loc[w4_mask, 'actual_power_kw'] *= (1.0 - 0.3 * (days[w4_mask] / 30.0))
    print("applied wind anomalies")
    
    # Add standard random noise back to healthy actual_power_kw (2%)
    healthy_mask = (assets['anomaly_ground_truth'] == 0) & (assets['expected_power_kw'] > 0)
    assets.loc[healthy_mask, 'actual_power_kw'] *= np.random.uniform(0.98, 1.02, size=healthy_mask.sum())
    
    # Curtailment command initialized to expected power
    assets['curtailment_command_kw'] = assets['expected_power_kw'].copy()
    
    # Clean up nighttime and bounds
    night_mask = (assets['expected_power_kw'] < 1.0)
    assets.loc[night_mask, 'expected_power_kw'] = 0.0
    assets.loc[night_mask, 'actual_power_kw'] = 0.0
    assets.loc[night_mask, 'anomaly_ground_truth'] = 0
    print("nighttime cleanup done")
    
    # Cap actual at capacity
    assets['actual_power_kw'] = np.minimum(assets['actual_power_kw'], assets['capacity_kw'])
    assets['expected_power_kw'] = np.minimum(assets['expected_power_kw'], assets['capacity_kw'])

    # Ensure performance_ratio is correct
    mask_expected = assets['expected_power_kw'] > 0
    assets.loc[mask_expected, 'performance_ratio'] = assets.loc[mask_expected, 'actual_power_kw'] / assets.loc[mask_expected, 'expected_power_kw']
    assets.loc[~mask_expected, 'performance_ratio'] = 1.0
    print("pre-aggregation done")

    # 3. Aggregate assets -> grid
    agg = assets.groupby(['timestamp', 'zone_id', 'asset_type']).agg({
        'expected_power_kw': 'sum',
        'actual_power_kw': 'sum'
    }).reset_index()
    print("aggregation done")
    
    agg_avail = agg.pivot_table(index=['timestamp', 'zone_id'], columns='asset_type', values='expected_power_kw', fill_value=0) / 1000.0
    agg_disp = agg.pivot_table(index=['timestamp', 'zone_id'], columns='asset_type', values='actual_power_kw', fill_value=0) / 1000.0
    print("pivots done")
    
    def add_noise(val):
        return val * np.random.uniform(0.98, 1.02)
        
    grid.set_index(['timestamp', 'zone_id'], inplace=True)
    
    old_ren_disp = grid['renewable_dispatched_mw'].copy()
    
    grid['solar_generation_mw'] = agg_disp['solar'].apply(add_noise)
    grid['wind_generation_mw'] = agg_disp['wind'].apply(add_noise)
    
    solar_avail = agg_avail['solar'].apply(add_noise)
    wind_avail = agg_avail['wind'].apply(add_noise)
    
    grid['renewable_available_mw'] = solar_avail + wind_avail
    grid['renewable_dispatched_mw'] = grid['solar_generation_mw'] + grid['wind_generation_mw']
    
    # Ensure dispatched <= available
    grid['renewable_dispatched_mw'] = np.minimum(grid['renewable_dispatched_mw'], grid['renewable_available_mw'])
    
    # Recompute to ensure total matches dispatched perfectly
    ratio = grid['renewable_dispatched_mw'] / (grid['solar_generation_mw'] + grid['wind_generation_mw']).replace(0, 1)
    grid['solar_generation_mw'] *= ratio
    grid['wind_generation_mw'] *= ratio
    
    grid['curtailment_mw'] = grid['renewable_available_mw'] - grid['renewable_dispatched_mw']
    grid['curtailment_mw'] = grid['curtailment_mw'].apply(lambda x: max(0, x))
    
    # Rebalance supply
    delta_ren_disp = old_ren_disp - grid['renewable_dispatched_mw']
    grid['grid_import_mw'] = grid['grid_import_mw'] + delta_ren_disp
    
    curt_mask = grid['curtailment_event_ground_truth'] == 1
    
    if curt_mask.sum() > 0:
        # In this scale, renewable_available_mw could be very large during curtailment events
        # Let's enforce that curtailment is large
        # transmission_flow approaches capacity
        grid.loc[curt_mask, 'transmission_flow_mw'] = grid.loc[curt_mask, 'transmission_capacity_mw'] * np.random.uniform(0.95, 0.99, size=curt_mask.sum())
        grid.loc[curt_mask, 'grid_import_mw'] = grid.loc[curt_mask, 'transmission_flow_mw']
        
        # To make sure we have significant curtailment, renewable_available must be high, but it's derived from assets
        # We need to artificially force high curtailment by reducing dispatch on the grid
        # Actually, if transmission is capped, grid_import_mw is near max.
        # But wait, grid_import_mw usually SUPPLIES demand. If renewable is high, we EXPORT?
        # If we export, transmission_flow_mw = export_mw.
        # In my logic, transmission_flow_mw is absolute flow (import or export).
        # Let's just constrain renewable_dispatched_mw so that curtailment_mw increases
        # We need demand = grid_import + hydro + ren_disp + battery_dis - battery_ch
        # ren_disp = demand - grid_import - hydro - battery_dis + battery_ch
        # For curtailment, say we can only export up to transmission capacity, but here grid_import is positive.
        # Just reduce ren_disp by a large amount and increase grid_import to balance it? No, if transmission is congested, import is capped.
        # Actually, let's just forcefully curtail dispatch during events and shift the balance to hydro or battery.
        # We just need to show some curtailment. 
        # But wait, earlier the user said: "Example target behavior: renewable available: ~2,500-3,500 MW, grid/transmission constraint: limits dispatch, curtailment: hundreds of MW"
        # Since we scaled up renewable capacities, the available will naturally be large.
        
        for idx in grid[curt_mask].index:
            avail = grid.loc[idx, 'renewable_available_mw']
            if avail > 500:
                disp = avail * np.random.uniform(0.5, 0.7) # Force 30-50% curtailment
                grid.loc[idx, 'renewable_dispatched_mw'] = disp
                grid.loc[idx, 'solar_generation_mw'] *= (disp / avail)
                grid.loc[idx, 'wind_generation_mw'] *= (disp / avail)
                grid.loc[idx, 'curtailment_mw'] = avail - disp
                
                # Now we need to balance demand. We lost (avail - disp) MW of supply. We must increase grid_import or hydro.
                lost_mw = avail - disp
                grid.loc[idx, 'grid_import_mw'] += lost_mw
                # If grid import exceeds trans capacity, clip it and increase hydro
                if grid.loc[idx, 'grid_import_mw'] > grid.loc[idx, 'transmission_capacity_mw']:
                    excess = grid.loc[idx, 'grid_import_mw'] - grid.loc[idx, 'transmission_capacity_mw']
                    grid.loc[idx, 'grid_import_mw'] = grid.loc[idx, 'transmission_capacity_mw']
                    grid.loc[idx, 'hydro_generation_mw'] += excess

    # Cap imports to capacity to prevent physical violations
    grid['grid_import_mw'] = np.minimum(grid['grid_import_mw'], grid['transmission_capacity_mw'])
    grid['transmission_flow_mw'] = np.minimum(grid['transmission_flow_mw'], grid['transmission_capacity_mw'])
    
    grid = grid.reset_index()
    
    # We must also enforce that the asset's actual_power_kw matches the forced reduction in grid dispatched!
    # Because we forced dispatch to drop by 30-50% during curtailment events, we must scale the asset's actual_power_kw accordingly.
    # We can join grid back to assets and scale actual_power_kw down during curtailment.
    
    assets = assets.merge(grid[['timestamp', 'zone_id', 'curtailment_event_ground_truth', 'renewable_available_mw', 'renewable_dispatched_mw']], on=['timestamp', 'zone_id'], how='left')
    
    is_curtailed = assets['curtailment_event_ground_truth'] == 1
    # Scale actual_power_kw by (renewable_dispatched_mw / renewable_available_mw)
    # Use existing actual_power_kw so we don't erase anomaly reductions!
    scale_down = assets['renewable_dispatched_mw'] / assets['renewable_available_mw'].replace(0, 1)
    assets.loc[is_curtailed, 'actual_power_kw'] = assets.loc[is_curtailed, 'actual_power_kw'] * scale_down.loc[is_curtailed]
    assets.loc[is_curtailed, 'curtailment_command_kw'] = assets.loc[is_curtailed, 'expected_power_kw'] * scale_down.loc[is_curtailed]
    
    assets.drop(columns=['curtailment_event_ground_truth', 'renewable_available_mw', 'renewable_dispatched_mw'], inplace=True)
    
    # Ensure performance_ratio is still 1.0 or correct
    # Wait, the prompt says "do NOT label healthy curtailed assets as equipment anomalies"
    # The performance ratio can be < 1, but anomaly_ground_truth = 0. We didn't change anomaly_ground_truth.
    mask_expected = assets['expected_power_kw'] > 0
    assets.loc[mask_expected, 'performance_ratio'] = assets.loc[mask_expected, 'actual_power_kw'] / assets.loc[mask_expected, 'expected_power_kw']

    print("Saving modified datasets...")
    grid.to_csv('data/grid_timeseries.csv', index=False)
    assets.to_csv('data/renewable_assets.csv', index=False)
    
    # Reporting
    print("\nReport:")
    
    # Total capacities by zone
    cap_by_zone = assets.groupby(['zone_id', 'asset_type'])['capacity_kw'].first().reset_index() # Wait, groupby zone and asset_id first!
    caps = assets[['asset_id', 'zone_id', 'asset_type', 'capacity_kw']].drop_duplicates()
    solar_cap_zone = caps[caps['asset_type'] == 'solar'].groupby('zone_id')['capacity_kw'].sum() / 1000
    wind_cap_zone = caps[caps['asset_type'] == 'wind'].groupby('zone_id')['capacity_kw'].sum() / 1000
    
    print("Solar asset capacity total by zone:")
    print(solar_cap_zone.to_string())
    print("\nWind asset capacity total by zone:")
    print(wind_cap_zone.to_string())
    print()
    
    avg_solar_zone = grid.groupby('zone_id')['solar_generation_mw'].mean()
    avg_wind_zone = grid.groupby('zone_id')['wind_generation_mw'].mean()
    
    print("Average solar generation by zone:")
    print(avg_solar_zone.to_string())
    print("\nAverage wind generation by zone:")
    print(avg_wind_zone.to_string())
    print()
    
    print(f"Maximum solar generation: {grid['solar_generation_mw'].max():.2f} MW")
    print(f"Maximum wind generation: {grid['wind_generation_mw'].max():.2f} MW")
    
    grid['ren_pct'] = (grid['renewable_dispatched_mw'] / grid['demand_mw'].replace(0, 1)) * 100
    print(f"Renewable generation as % of demand: {grid['ren_pct'].mean():.2f}% average")
    
    print(f"Maximum curtailment MW: {grid['curtailment_mw'].max():.2f}")
    curt_rows = grid[grid['curtailment_event_ground_truth'] == 1]
    avg_curt = curt_rows['curtailment_mw'].mean() if len(curt_rows) > 0 else 0
    print(f"Average curtailment during curtailment events: {avg_curt:.2f} MW")
    
    avg_trans_util = (curt_rows['transmission_flow_mw'] / curt_rows['transmission_capacity_mw']).mean() * 100 if len(curt_rows) > 0 else 0
    print(f"Transmission utilization during curtailment: {avg_trans_util:.2f}%")
    
    # Re-aggregate to get the true final asset totals
    final_agg = assets.groupby(['timestamp', 'zone_id', 'asset_type'])['actual_power_kw'].sum().reset_index()
    final_agg_disp = final_agg.pivot_table(index=['timestamp', 'zone_id'], columns='asset_type', values='actual_power_kw', fill_value=0) / 1000.0
    final_agg_disp = final_agg_disp.reset_index()
    
    check_df = pd.merge(grid[['timestamp', 'zone_id', 'solar_generation_mw', 'wind_generation_mw']], final_agg_disp, on=['timestamp', 'zone_id'])
    check_df['solar_diff'] = np.abs(check_df['solar_generation_mw'] - check_df['solar'])
    check_df['wind_diff'] = np.abs(check_df['wind_generation_mw'] - check_df['wind'])
    print(f"Maximum asset-to-grid solar difference: {check_df['solar_diff'].max():.4f} MW")
    print(f"Maximum asset-to-grid wind difference: {check_df['wind_diff'].max():.4f} MW")
    print()
    
    print(f"Demand spike events: {len(grid[grid['demand_spike_ground_truth'] == 1])}")
    # Anomaly events count is rows in assets
    print(f"Asset anomaly events: {len(assets[assets['anomaly_ground_truth'] == 1])}")
    print(f"Curtailment events: {len(curt_rows)}")
    
    neg_irr = (forecast['irradiance_forecast_wm2'] < 0).sum()
    cc_out = ((forecast['cloud_cover_forecast_pct'] < 0) | (forecast['cloud_cover_forecast_pct'] > 100)).sum()
    
    rm_min = grid['reserve_margin_pct'].min()
    rm_viol = (rm_min < 0)
    
    dups = grid.duplicated().sum() + assets.duplicated().sum()
    
    exp_gt_cap = (assets['expected_power_kw'] > assets['capacity_kw'] + 0.01).sum()
    act_gt_cap = (assets['actual_power_kw'] > assets['capacity_kw'] + 0.01).sum()
    neg_pwr = (assets['expected_power_kw'] < -0.01).sum() + (assets['actual_power_kw'] < -0.01).sum()
    fp_night = assets[(assets['expected_power_kw'] < 1.0) & (assets['anomaly_ground_truth'] == 1)].shape[0]
    
    violations = exp_gt_cap + act_gt_cap + neg_pwr + fp_night
    if (grid['transmission_flow_mw'] > grid['transmission_capacity_mw'] + 0.1).any(): violations += 1
    
    print(f"\nNegative irradiance: {neg_irr}")
    print(f"Invalid cloud cover: {cc_out}")
    print(f"Reserve margin violations: {rm_viol}")
    print(f"Duplicate rows: {dups}")
    print(f"Physical constraint violations: {violations}")
    
    print("\nDataset status:")
    print("PASS" if violations == 0 and neg_irr == 0 and cc_out == 0 else "FAIL")
    
if __name__ == "__main__":
    scale_up_dataset()
