import pandas as pd
import numpy as np

def fix_dataset():
    print("Loading data...")
    grid = pd.read_csv('data/grid_timeseries.csv')
    assets = pd.read_csv('data/renewable_assets.csv')
    
    np.random.seed(42)
    
    # 1. Assign realistic capacities to assets
    asset_new_caps = {}
    for aid in assets['asset_id'].unique():
        typ = assets[assets['asset_id'] == aid]['asset_type'].iloc[0]
        if typ == 'solar':
            asset_new_caps[aid] = np.random.uniform(200, 350)
        else:
            asset_new_caps[aid] = np.random.uniform(400, 800)
            
    # 2. Scale asset outputs
    old_caps = assets.groupby('asset_id')['capacity_kw'].first().to_dict()
    scale_factors = assets['asset_id'].map(lambda x: asset_new_caps[x] / old_caps[x])
    
    assets['capacity_kw'] = assets['asset_id'].map(asset_new_caps)
    assets['expected_power_kw'] *= scale_factors
    assets['actual_power_kw'] *= scale_factors
    assets['curtailment_command_kw'] *= scale_factors
    
    # Clean up nighttime and bounds
    night_mask = (assets['expected_power_kw'] < 1.0)
    assets.loc[night_mask, 'expected_power_kw'] = 0.0
    assets.loc[night_mask, 'actual_power_kw'] = 0.0
    assets.loc[night_mask, 'anomaly_ground_truth'] = 0
    
    # Cap actual at capacity
    assets['actual_power_kw'] = np.minimum(assets['actual_power_kw'], assets['capacity_kw'])
    assets['expected_power_kw'] = np.minimum(assets['expected_power_kw'], assets['capacity_kw'])

    # Ensure performance_ratio is correct
    mask_expected = assets['expected_power_kw'] > 0
    assets.loc[mask_expected, 'performance_ratio'] = assets.loc[mask_expected, 'actual_power_kw'] / assets.loc[mask_expected, 'expected_power_kw']
    assets.loc[~mask_expected, 'performance_ratio'] = 1.0

    # 3. Aggregate assets -> grid
    agg = assets.groupby(['timestamp', 'zone_id', 'asset_type']).agg({
        'expected_power_kw': 'sum',
        'actual_power_kw': 'sum'
    }).reset_index()
    
    agg_avail = agg.pivot_table(index=['timestamp', 'zone_id'], columns='asset_type', values='expected_power_kw', fill_value=0) / 1000.0
    agg_disp = agg.pivot_table(index=['timestamp', 'zone_id'], columns='asset_type', values='actual_power_kw', fill_value=0) / 1000.0
    
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
    # (Just slightly adjust solar_generation_mw if we capped it, though it's practically identical)
    ratio = grid['renewable_dispatched_mw'] / (grid['solar_generation_mw'] + grid['wind_generation_mw']).replace(0, 1)
    grid['solar_generation_mw'] *= ratio
    grid['wind_generation_mw'] *= ratio
    
    grid['curtailment_mw'] = grid['renewable_available_mw'] - grid['renewable_dispatched_mw']
    grid['curtailment_mw'] = grid['curtailment_mw'].apply(lambda x: max(0, x))
    
    # Rebalance supply
    delta_ren_disp = old_ren_disp - grid['renewable_dispatched_mw']
    grid['grid_import_mw'] = grid['grid_import_mw'] + delta_ren_disp
    
    curt_mask = grid['curtailment_event_ground_truth'] == 1
    grid['transmission_flow_mw'] = grid['grid_import_mw']
    if curt_mask.sum() > 0:
        grid.loc[curt_mask, 'transmission_flow_mw'] = grid.loc[curt_mask, 'transmission_capacity_mw'] * np.random.uniform(0.95, 0.99, size=curt_mask.sum())
        grid.loc[curt_mask, 'grid_import_mw'] = grid.loc[curt_mask, 'transmission_flow_mw']
        
    # Cap imports to capacity to prevent physical violations
    grid['grid_import_mw'] = np.minimum(grid['grid_import_mw'], grid['transmission_capacity_mw'])
    grid['transmission_flow_mw'] = np.minimum(grid['transmission_flow_mw'], grid['transmission_capacity_mw'])
    
    grid = grid.reset_index()
    
    print("Saving modified datasets...")
    grid.to_csv('data/grid_timeseries.csv', index=False)
    assets.to_csv('data/renewable_assets.csv', index=False)
    
    # Reporting
    print("\nReport:")
    
    cap_ranges = assets.groupby('asset_type')['capacity_kw'].agg(['min', 'max'])
    print("Asset capacity ranges by asset type:")
    print(cap_ranges)
    print()
    
    agg_disp = agg_disp.reset_index()
    check_df = pd.merge(grid[['timestamp', 'zone_id', 'solar_generation_mw', 'wind_generation_mw']], agg_disp, on=['timestamp', 'zone_id'])
    
    check_df['solar_diff'] = np.abs(check_df['solar_generation_mw'] - check_df['solar'])
    check_df['wind_diff'] = np.abs(check_df['wind_generation_mw'] - check_df['wind'])
    
    max_solar_diff = check_df['solar_diff'].max()
    max_wind_diff = check_df['wind_diff'].max()
    
    print(f"Maximum absolute aggregation difference (Solar): {max_solar_diff:.4f} MW")
    print(f"Maximum absolute aggregation difference (Wind): {max_wind_diff:.4f} MW")
    print()
    
    exp_gt_cap = (assets['expected_power_kw'] > assets['capacity_kw'] + 0.01).sum()
    act_gt_cap = (assets['actual_power_kw'] > assets['capacity_kw'] + 0.01).sum()
    neg_pwr = (assets['expected_power_kw'] < -0.01).sum() + (assets['actual_power_kw'] < -0.01).sum()
    
    fp_night = assets[(assets['expected_power_kw'] < 1.0) & (assets['anomaly_ground_truth'] == 1)].shape[0]
    
    dups = grid.duplicated().sum() + assets.duplicated().sum()
    
    violations = exp_gt_cap + act_gt_cap + neg_pwr + fp_night + dups
    if (grid['transmission_flow_mw'] > grid['transmission_capacity_mw'] + 0.1).any(): violations += 1
    
    print(f"expected_power > capacity: {exp_gt_cap}")
    print(f"actual_power > capacity: {act_gt_cap}")
    print(f"negative power: {neg_pwr}")
    print(f"nighttime false-positive anomalies: {fp_night}")
    print(f"duplicate rows: {dups}")
    print(f"physical violations: {violations}")
    print()
    print("Dataset status:")
    print("PASS" if violations == 0 else "FAIL")
    
if __name__ == "__main__":
    fix_dataset()
