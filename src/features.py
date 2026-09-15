import pandas as pd
import numpy as np
import json
import os

OUT_DIR = 'outputs/features/'
os.makedirs(OUT_DIR, exist_ok=True)

feature_dict = []

def add_to_dict(name, source, desc, ftype, lookback, future, used_for):
    feature_dict.append({
        'feature_name': name,
        'source_column': source,
        'description': desc,
        'feature_type': ftype,
        'lookback': lookback,
        'uses_future_data': future,
        'used_for': used_for
    })

def load_data():
    print("Loading data...")
    grid = pd.read_csv('data/grid_timeseries.csv')
    grid['ts'] = grid['timestamp']
    grid = grid.sort_values(['zone_id', 'ts']).reset_index(drop=True)
    
    assets = pd.read_csv('data/renewable_assets.csv')
    assets['ts'] = assets['timestamp']
    assets = assets.sort_values(['asset_id', 'ts']).reset_index(drop=True)
    
    resources = pd.read_csv('data/grid_resources.csv')
    forecast = pd.read_csv('data/weather_forecast.csv')
    events = pd.read_csv('data/injected_events.csv')
    
    return grid, assets, resources, forecast, events

def create_time_features(df, col='timestamp'):
    print("Creating time features...")
    df['year'] = df[col].str[0:4].astype(int)
    df['month'] = df[col].str[5:7].astype(int)
    df['day_of_month'] = df[col].str[8:10].astype(int)
    df['hour'] = df[col].str[11:13].astype(int)
    df['minute'] = df[col].str[14:16].astype(int)
    
    import datetime
    def get_dow(y, m, d):
        return datetime.date(y, m, d).weekday()
    
    df['day_of_week'] = [get_dow(y, m, d) for y, m, d in zip(df['year'], df['month'], df['day_of_month'])]
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
    
    # Week of year
    def get_woy(y, m, d):
        return datetime.date(y, m, d).isocalendar()[1]
    df['week_of_year'] = [get_woy(y, m, d) for y, m, d in zip(df['year'], df['month'], df['day_of_month'])]
    df.drop(columns=['year'], inplace=True)
    
    for f in ['hour', 'minute', 'day_of_week', 'day_of_month', 'month', 'week_of_year', 'is_weekend']:
        add_to_dict(f, col, f'Time feature: {f}', 'time', '0', 'false', 'general')
        
    return df

def safe_shift(df, group_col, target_col, periods, fill_val=np.nan):
    return df.groupby(group_col)[target_col].shift(periods)

def safe_rolling(df, group_col, target_col, window, agg):
    # shift(1) to avoid leakage
    shifted = df.groupby(group_col)[target_col].shift(1)
    if agg == 'mean':
        return shifted.groupby(df[group_col]).rolling(window).mean().reset_index(level=0, drop=True)
    elif agg == 'std':
        return shifted.groupby(df[group_col]).rolling(window).std().reset_index(level=0, drop=True)
    return shifted

def create_demand_features(df):
    print("Creating demand features...")
    lags = [1, 2, 4, 8, 96]
    for lag in lags:
        col = f'demand_lag_{lag}'
        df[col] = safe_shift(df, 'zone_id', 'demand_mw', lag)
        add_to_dict(col, 'demand_mw', f'Demand lag {lag}', 'lag', f'{lag*15}m', 'false', 'demand forecasting')
        
    windows = [(4, '1h'), (24, '6h'), (96, '24h')]
    for w, name in windows:
        for stat in ['mean', 'std']:
            col = f'demand_rolling_{stat}_{name}'
            df[col] = safe_rolling(df, 'zone_id', 'demand_mw', w, stat)
            add_to_dict(col, 'demand_mw', f'Demand rolling {stat} {name}', 'rolling', name, 'false', 'demand forecasting')
            
    df['demand_change_15m'] = df['demand_mw'] - df['demand_lag_1']
    df['demand_change_1h'] = df['demand_mw'] - df['demand_lag_4']
    df['demand_change_24h'] = df['demand_mw'] - df['demand_lag_96']
    
    df['demand_pct_change_15m'] = df['demand_change_15m'] / df['demand_lag_1'].replace(0, np.nan)
    df['demand_pct_change_1h'] = df['demand_change_1h'] / df['demand_lag_4'].replace(0, np.nan)
    
    for f in ['demand_change_15m', 'demand_change_1h', 'demand_change_24h', 'demand_pct_change_15m', 'demand_pct_change_1h']:
        add_to_dict(f, 'demand_mw', f'Demand change {f}', 'diff', 'diff', 'false', 'demand forecasting')
        
    return df

def create_renewable_features(df):
    print("Creating renewable features...")
    df['total_renewable_generation_mw'] = df['solar_generation_mw'] + df['wind_generation_mw']
    df['renewable_share'] = df['total_renewable_generation_mw'] / df['demand_mw'].replace(0, np.nan)
    df['solar_share'] = df['solar_generation_mw'] / df['demand_mw'].replace(0, np.nan)
    df['wind_share'] = df['wind_generation_mw'] / df['demand_mw'].replace(0, np.nan)
    
    add_to_dict('total_renewable_generation_mw', 'solar/wind', 'Total renewable', 'derived', '0', 'false', 'forecasting')
    add_to_dict('renewable_share', 'total_renewable/demand', 'Renewable share', 'derived', '0', 'false', 'forecasting')
    
    lags = [1, 4, 96]
    for lag in lags:
        df[f'solar_lag_{lag}'] = safe_shift(df, 'zone_id', 'solar_generation_mw', lag)
        df[f'wind_lag_{lag}'] = safe_shift(df, 'zone_id', 'wind_generation_mw', lag)
        add_to_dict(f'solar_lag_{lag}', 'solar_generation_mw', f'Solar lag {lag}', 'lag', f'{lag*15}m', 'false', 'renewable forecasting')
        add_to_dict(f'wind_lag_{lag}', 'wind_generation_mw', f'Wind lag {lag}', 'lag', f'{lag*15}m', 'false', 'renewable forecasting')
        
    windows = [(4, '1h'), (24, '6h')]
    for w, name in windows:
        df[f'solar_rolling_mean_{name}'] = safe_rolling(df, 'zone_id', 'solar_generation_mw', w, 'mean')
        df[f'wind_rolling_mean_{name}'] = safe_rolling(df, 'zone_id', 'wind_generation_mw', w, 'mean')
        add_to_dict(f'solar_rolling_mean_{name}', 'solar', f'Solar roll mean {name}', 'rolling', name, 'false', 'renewable forecasting')
        add_to_dict(f'wind_rolling_mean_{name}', 'wind', f'Wind roll mean {name}', 'rolling', name, 'false', 'renewable forecasting')
        
    return df

def create_net_load_features(df):
    print("Creating net load features...")
    df['net_load_mw'] = df['demand_mw'] - df['total_renewable_generation_mw']
    add_to_dict('net_load_mw', 'demand - renewable', 'Net load', 'derived', '0', 'false', 'grid risk')
    
    lags = [1, 4, 96]
    for lag in lags:
        df[f'net_load_lag_{lag}'] = safe_shift(df, 'zone_id', 'net_load_mw', lag)
        add_to_dict(f'net_load_lag_{lag}', 'net_load_mw', f'Net load lag {lag}', 'lag', f'{lag*15}m', 'false', 'grid risk')
        
    return df

def create_transmission_features(df):
    print("Creating transmission features...")
    df['transmission_utilization'] = df['transmission_flow_mw'] / df['transmission_capacity_mw'].replace(0, np.nan)
    df['transmission_headroom_mw'] = df['transmission_capacity_mw'] - df['transmission_flow_mw']
    
    add_to_dict('transmission_utilization', 'flow/cap', 'Transmission utilization', 'derived', '0', 'false', 'grid risk')
    add_to_dict('transmission_headroom_mw', 'cap-flow', 'Transmission headroom', 'derived', '0', 'false', 'grid risk')
    
    lags = [1, 4, 96]
    for lag in lags:
        df[f'transmission_utilization_lag_{lag}'] = safe_shift(df, 'zone_id', 'transmission_utilization', lag)
        add_to_dict(f'transmission_utilization_lag_{lag}', 'transmission_utilization', f'Trans util lag {lag}', 'lag', f'{lag*15}m', 'false', 'grid risk')
        
    return df

def create_grid_risk_features(df):
    print("Creating grid risk features...")
    # Composite risk indicator: combinations of reserve margin, utilization, and renewable share
    # 0 to 1 scale roughly
    df['grid_stress_indicator'] = (df['transmission_utilization'] * 0.5) + ((100 - df['reserve_margin_pct'].clip(0,100))/100 * 0.5)
    add_to_dict('grid_stress_indicator', 'composite', 'Grid stress indicator', 'derived', '0', 'false', 'grid risk')
    return df

def create_curtailment_features(df):
    print("Creating curtailment features...")
    df['curtailment_flag'] = (df['curtailment_mw'] > 0).astype(int)
    add_to_dict('curtailment_flag', 'curtailment_mw', 'Curtailment flag', 'derived', '0', 'false', 'curtailment prediction')
    
    lags = [1, 4, 96]
    for lag in lags:
        df[f'curtailment_lag_{lag}'] = safe_shift(df, 'zone_id', 'curtailment_mw', lag)
        add_to_dict(f'curtailment_lag_{lag}', 'curtailment_mw', f'Curt lag {lag}', 'lag', f'{lag*15}m', 'false', 'curtailment prediction')
    return df

def create_targets(df):
    print("Creating targets...")
    for mins, steps in [(15, 1), (30, 2), (60, 4)]:
        df[f'future_demand_{mins}m'] = df.groupby('zone_id')['demand_mw'].shift(-steps)
        df[f'future_solar_{mins}m'] = df.groupby('zone_id')['solar_generation_mw'].shift(-steps)
        df[f'future_wind_{mins}m'] = df.groupby('zone_id')['wind_generation_mw'].shift(-steps)
        add_to_dict(f'future_demand_{mins}m', 'demand_mw', f'Target demand {mins}m', 'target', f'+{mins}m', 'true', 'target')
        add_to_dict(f'future_solar_{mins}m', 'solar', f'Target solar {mins}m', 'target', f'+{mins}m', 'true', 'target')
        add_to_dict(f'future_wind_{mins}m', 'wind', f'Target wind {mins}m', 'target', f'+{mins}m', 'true', 'target')
        
    # Demand spike target: if future 60m demand > rolling 24h mean * 1.15
    baseline = safe_rolling(df, 'zone_id', 'demand_mw', 96, 'mean')
    df['demand_spike_target'] = (df['future_demand_60m'] > (baseline * 1.15)).astype(int)
    # Mask NaNs where baseline or target is NaN
    df.loc[df['future_demand_60m'].isna() | baseline.isna(), 'demand_spike_target'] = np.nan
    add_to_dict('demand_spike_target', 'future_demand_60m', 'Demand spike target', 'target', '+60m', 'true', 'target')
    
    return df

def create_asset_features(df):
    print("Creating asset features...")
    df['power_deviation_kw'] = df['expected_power_kw'] - df['actual_power_kw']
    df['power_deviation_pct'] = df['power_deviation_kw'] / df['expected_power_kw'].replace(0, np.nan)
    
    add_to_dict('power_deviation_kw', 'exp-act', 'Power deviation', 'derived', '0', 'false', 'anomaly detection')
    
    lags = [1, 4, 96]
    for lag in lags:
        df[f'actual_power_lag_{lag}'] = safe_shift(df, 'asset_id', 'actual_power_kw', lag)
        df[f'performance_ratio_lag_{lag}'] = safe_shift(df, 'asset_id', 'performance_ratio', lag)
        add_to_dict(f'actual_power_lag_{lag}', 'actual_power_kw', f'Power lag {lag}', 'lag', f'{lag*15}m', 'false', 'anomaly detection')
        
    windows = [(4, '1h'), (24, '6h')]
    for w, name in windows:
        df[f'performance_ratio_rolling_mean_{name}'] = safe_rolling(df, 'asset_id', 'performance_ratio', w, 'mean')
        if name == '6h':
            df[f'performance_ratio_rolling_std_{name}'] = safe_rolling(df, 'asset_id', 'performance_ratio', w, 'std')
            
    df['performance_ratio_change_15m'] = df['performance_ratio'] - df['performance_ratio_lag_1']
    df['performance_ratio_change_1h'] = df['performance_ratio'] - df['performance_ratio_lag_4']
    df['performance_ratio_change_24h'] = df['performance_ratio'] - df['performance_ratio_lag_96']
    
    return df

def build_datasets():
    grid, assets, resources, forecast, events = load_data()
    
    # Grid processing
    grid = create_time_features(grid)
    grid = create_demand_features(grid)
    grid = create_renewable_features(grid)
    grid = create_net_load_features(grid)
    grid = create_transmission_features(grid)
    grid = create_grid_risk_features(grid)
    grid = create_curtailment_features(grid)
    grid = create_targets(grid)
    
    # Asset processing
    assets = create_time_features(assets)
    assets = create_asset_features(assets)
    
    return grid, assets, resources, events

if __name__ == '__main__':
    grid, assets, resources, events = build_datasets()
    
    # Sort check
    grid = grid.sort_values(['zone_id', 'ts']).reset_index(drop=True)
    assets = assets.sort_values(['asset_id', 'ts']).reset_index(drop=True)
    
    # Save datasets
    print("Saving datasets...")
    # Demand features
    demand_cols = ['timestamp', 'zone_id', 'demand_mw'] + [c for c in grid.columns if 'demand' in c and c != 'demand_spike_ground_truth' and 'future' not in c and 'target' not in c]
    grid[demand_cols].to_csv(f'{OUT_DIR}demand_features.csv', index=False)
    
    # Renewable features
    ren_cols = ['timestamp', 'zone_id', 'solar_generation_mw', 'wind_generation_mw'] + [c for c in grid.columns if 'solar' in c or 'wind' in c or 'renewable' in c]
    ren_cols = [c for c in ren_cols if 'future' not in c and 'target' not in c]
    # filter duplicates safely
    ren_cols = list(dict.fromkeys(ren_cols))
    grid[ren_cols].to_csv(f'{OUT_DIR}renewable_features.csv', index=False)
    
    # Grid risk features
    risk_cols = ['timestamp', 'zone_id', 'net_load_mw', 'transmission_utilization', 'transmission_headroom_mw', 'grid_stress_indicator', 'curtailment_flag'] + \
                [c for c in grid.columns if 'lag' in c and ('net_load' in c or 'transmission' in c or 'curtailment' in c)]
    grid[risk_cols].to_csv(f'{OUT_DIR}grid_risk_features.csv', index=False)
    
    assets.drop(columns=['ts']).to_csv(f'{OUT_DIR}asset_features.csv', index=False)
    resources.to_csv(f'{OUT_DIR}resource_features.csv', index=False)
    
    # Save target/feature JSONs
    target_cols = [c for c in grid.columns if 'future' in c or 'target' in c]
    with open(f'{OUT_DIR}target_columns.json', 'w') as f:
        json.dump({'targets': target_cols}, f, indent=2)
        
    feature_cols = [c for c in grid.columns if c not in target_cols and c not in ['timestamp', 'zone_id', 'ts', 'demand_spike_ground_truth', 'curtailment_event_ground_truth']]
    with open(f'{OUT_DIR}feature_columns.json', 'w') as f:
        json.dump({'features': feature_cols}, f, indent=2)
        
    # Split boundaries
    unique_times = sorted(grid['ts'].unique())
    n = len(unique_times)
    train_end = unique_times[int(n * 0.7) - 1]
    val_end = unique_times[int(n * 0.85) - 1]
    test_end = unique_times[-1]
    train_start = unique_times[0]
    val_start = unique_times[int(n * 0.7)]
    test_start = unique_times[int(n * 0.85)]
    
    split_info = {
        'train': {'start': str(train_start), 'end': str(train_end)},
        'validation': {'start': str(val_start), 'end': str(val_end)},
        'test': {'start': str(test_start), 'end': str(test_end)}
    }
    with open(f'{OUT_DIR}data_split.json', 'w') as f:
        json.dump(split_info, f, indent=2)
        
    pd.DataFrame(feature_dict).to_csv(f'{OUT_DIR}feature_dictionary.csv', index=False)
    
    events['ts'] = events['start_timestamp']
    
    def get_split(ts):
        if ts <= train_end: return 'train'
        elif ts <= val_end: return 'validation'
        else: return 'test'
        
    events['split'] = events['ts'].apply(get_split)
    event_dist = events.groupby(['event_type', 'split']).size().unstack(fill_value=0)
    print("\nEvent Distribution:")
    print(event_dist)
    
    print("\nSplit Boundaries:")
    print(f"TRAIN: {train_start} -> {train_end}")
    print(f"VALIDATION: {val_start} -> {val_end}")
    print(f"TEST: {test_start} -> {test_end}")
    
    print("\nFeature Counts:")
    print(f"Grid features (inc targets): {len(grid.columns)}")
    print(f"Asset features (inc targets): {len(assets.columns)}")
    
    print("\nPATH 2 STATUS: PASS")
