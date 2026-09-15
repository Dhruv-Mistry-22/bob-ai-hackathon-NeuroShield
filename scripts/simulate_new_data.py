"""
simulate_new_data.py
--------------------
Generates one new 15-minute tick of synthetic grid telemetry and appends
it to all four source CSV files. Called before the pipeline runs to
simulate live incoming data.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

SEED = None  # intentionally random each run for demo realism
rng = np.random.default_rng(seed=SEED)


# ─── helpers ──────────────────────────────────────────────────────────────────

def next_ts(df, ts_col='timestamp'):
    last = pd.to_datetime(df[ts_col].max())
    return last + timedelta(minutes=15)


def perturb(val, pct=0.05, low=None, high=None):
    """Randomly nudge a value by ±pct, clamped to [low, high]."""
    delta = val * pct * rng.uniform(-1, 1)
    result = val + delta
    if low is not None:
        result = max(result, low)
    if high is not None:
        result = min(result, high)
    return float(result)


# ─── 1. grid_timeseries ───────────────────────────────────────────────────────

def simulate_grid_timeseries():
    path = 'data/grid_timeseries.csv'
    df = pd.read_csv(path)
    new_ts = next_ts(df)
    ts_str = new_ts.strftime('%Y-%m-%d %H:%M:%S')
    hour = new_ts.hour

    # Nighttime -> no solar; daytime -> some solar
    is_daytime = 6 <= hour <= 18

    new_rows = []
    for zone_id in df['zone_id'].unique():
        zdf = df[df['zone_id'] == zone_id].sort_values('timestamp')
        last = zdf.iloc[-1]

        temp = perturb(float(last['temperature_c']), 0.03, -5, 45)
        humidity = perturb(float(last['humidity_pct']), 0.02, 20, 100)
        wind_speed = perturb(float(last['wind_speed_ms']), 0.10, 0, 20)
        irradiance = perturb(float(last['irradiance_wm2']), 0.15, 0, 1000) if is_daytime else rng.uniform(0, 10)
        cloud = perturb(float(last['cloud_cover_pct']), 0.05, 0, 100)

        solar_gen = max(0, irradiance * 0.3 * (1 - cloud / 100) * rng.uniform(0.8, 1.2))
        wind_gen = max(0, wind_speed ** 1.5 * rng.uniform(3, 5))
        hydro_gen = perturb(float(last['hydro_generation_mw']), 0.03, 100, 500)

        demand = perturb(float(last['demand_mw']), 0.04, 500, 4000)

        renewable_avail = solar_gen + wind_gen + hydro_gen
        renewable_dispatched = min(renewable_avail, demand * 0.4)
        curtailment = max(0, renewable_avail - renewable_dispatched)

        grid_import = max(0, demand - renewable_dispatched - hydro_gen)
        tx_cap = int(last['transmission_capacity_mw'])
        tx_flow = min(grid_import + renewable_dispatched, tx_cap * rng.uniform(0.7, 0.98))

        soc = perturb(float(last['battery_soc_pct']), 0.02, 10, 90)
        freq = perturb(float(last['grid_frequency_hz']), 0.001, 49.5, 50.5)
        reserve = perturb(float(last['reserve_margin_pct']), 0.05, 5, 40)

        # Occasionally inject a demand spike for demo excitement
        spike = int(rng.random() < 0.08)
        if spike:
            demand *= rng.uniform(1.10, 1.25)

        curt_event = int(curtailment > 5)

        new_rows.append({
            'timestamp': ts_str,
            'zone_id': zone_id,
            'demand_mw': round(demand, 4),
            'temperature_c': round(temp, 4),
            'humidity_pct': round(humidity, 4),
            'wind_speed_ms': round(wind_speed, 4),
            'irradiance_wm2': round(irradiance, 4),
            'cloud_cover_pct': round(cloud, 4),
            'solar_generation_mw': round(solar_gen, 4),
            'wind_generation_mw': round(wind_gen, 4),
            'hydro_generation_mw': round(hydro_gen, 4),
            'grid_import_mw': round(grid_import, 4),
            'battery_charge_mw': 0,
            'battery_discharge_mw': 0,
            'battery_soc_pct': round(soc, 4),
            'demand_response_available_mw': int(last['demand_response_available_mw']),
            'transmission_capacity_mw': tx_cap,
            'transmission_flow_mw': round(tx_flow, 4),
            'renewable_available_mw': round(renewable_avail, 4),
            'renewable_dispatched_mw': round(renewable_dispatched, 4),
            'curtailment_mw': round(curtailment, 4),
            'grid_frequency_hz': round(freq, 4),
            'reserve_margin_pct': round(reserve, 4),
            'holiday_flag': int(last['holiday_flag']),
            'demand_spike_ground_truth': spike,
            'curtailment_event_ground_truth': curt_event,
        })

    df_new = pd.DataFrame(new_rows)
    df_combined = pd.concat([df, df_new], ignore_index=True)
    df_combined.to_csv(path, index=False)
    print(f"  [grid_timeseries]    +{len(new_rows)} rows -> new ts: {ts_str}")
    return ts_str


# ─── 2. renewable_assets ──────────────────────────────────────────────────────

def simulate_renewable_assets(ts_str):
    path = 'data/renewable_assets.csv'
    df = pd.read_csv(path)
    hour = pd.to_datetime(ts_str).hour
    is_daytime = 6 <= hour <= 18

    new_rows = []
    for asset_id in df['asset_id'].unique():
        adf = df[df['asset_id'] == asset_id].sort_values('timestamp')
        last = adf.iloc[-1]

        cap = float(last['capacity_kw'])
        asset_type = last['asset_type']
        zone_id = last['zone_id']

        if asset_type == 'solar':
            irr = rng.uniform(0, 600) if is_daytime else rng.uniform(0, 5)
            expected = cap * (irr / 1000) * 0.18
            actual = expected * perturb(1.0, 0.08, 0.5, 1.1)
        else:  # wind
            ws = perturb(float(last['wind_speed_ms']), 0.12, 0, 20)
            expected = min(cap, cap * (ws / 12) ** 3)
            actual = expected * perturb(1.0, 0.07, 0.5, 1.1)
            irr = 0.0

        actual = max(0, actual)
        expected = max(0.01, expected)
        pr = round(actual / expected, 4) if expected > 0 else 0.0

        # Occasionally degrade an asset for demo excitement
        anomaly = int(rng.random() < 0.06)
        if anomaly:
            actual *= rng.uniform(0.4, 0.7)

        new_rows.append({
            'timestamp': ts_str,
            'asset_id': asset_id,
            'asset_type': asset_type,
            'zone_id': zone_id,
            'capacity_kw': round(cap, 4),
            'expected_power_kw': round(expected, 4),
            'actual_power_kw': round(actual, 4),
            'performance_ratio': pr,
            'irradiance_wm2': round(irr, 4),
            'ambient_temp_c': round(perturb(float(last['ambient_temp_c']), 0.03), 4),
            'asset_temp_c': round(perturb(float(last['asset_temp_c']), 0.03), 4),
            'dc_voltage_v': int(last['dc_voltage_v']),
            'dc_current_a': round(perturb(float(last['dc_current_a']), 0.05, 0), 4),
            'ac_voltage_v': int(last['ac_voltage_v']),
            'ac_current_a': round(perturb(float(last['ac_current_a']), 0.05, 0), 4),
            'power_factor': round(perturb(float(last['power_factor']), 0.01, 0.8, 1.0), 4),
            'wind_speed_ms': round(perturb(float(last['wind_speed_ms']), 0.10, 0, 20), 4),
            'wind_direction_deg': round(rng.uniform(0, 360), 4),
            'fault_code': 'NONE',
            'communication_status': 'OK',
            'maintenance_age_days': int(last['maintenance_age_days']) + 1,
            'curtailment_command_kw': round(expected, 4),
            'anomaly_ground_truth': anomaly,
            'root_cause_ground_truth': float('nan'),
        })

    df_new = pd.DataFrame(new_rows)
    df_combined = pd.concat([df, df_new], ignore_index=True)
    df_combined.to_csv(path, index=False)
    print(f"  [renewable_assets]   +{len(new_rows)} rows -> new ts: {ts_str}")


# ─── 3. grid_resources ────────────────────────────────────────────────────────

def simulate_grid_resources(ts_str):
    path = 'data/grid_resources.csv'
    df = pd.read_csv(path)

    new_rows = []
    for rid in df['resource_id'].unique():
        rdf = df[df['resource_id'] == rid].sort_values('timestamp')
        last = rdf.iloc[-1]

        soc = perturb(float(last['current_soc_pct']), 0.03, float(last['min_soc_pct']) if pd.notna(last['min_soc_pct']) else 10,
                      float(last['max_soc_pct']) if pd.notna(last['max_soc_pct']) else 90) if pd.notna(last['current_soc_pct']) else float('nan')

        new_rows.append({
            'timestamp': ts_str,
            'resource_id': rid,
            'resource_type': last['resource_type'],
            'zone_id': last['zone_id'],
            'available_capacity_mw': int(last['available_capacity_mw']),
            'max_charge_mw': last['max_charge_mw'],
            'max_discharge_mw': last['max_discharge_mw'],
            'current_output_mw': 0,
            'min_output_mw': int(last['min_output_mw']),
            'max_output_mw': int(last['max_output_mw']),
            'ramp_rate_mw_per_min': float(last['ramp_rate_mw_per_min']),
            'current_soc_pct': round(soc, 4) if pd.notna(soc) else float('nan'),
            'min_soc_pct': last['min_soc_pct'],
            'max_soc_pct': last['max_soc_pct'],
            'activation_cost_per_mwh': int(last['activation_cost_per_mwh']),
            'response_time_min': int(last['response_time_min']),
        })

    df_new = pd.DataFrame(new_rows)
    df_combined = pd.concat([df, df_new], ignore_index=True)
    df_combined.to_csv(path, index=False)
    print(f"  [grid_resources]     +{len(new_rows)} rows -> new ts: {ts_str}")


# ─── 4. weather_forecast ──────────────────────────────────────────────────────

def simulate_weather_forecast(ts_str):
    path = 'data/weather_forecast.csv'
    df = pd.read_csv(path)
    new_ts = pd.to_datetime(ts_str)
    target_ts = new_ts + timedelta(hours=4)  # 4-hour ahead forecast window
    forecast_str = new_ts.strftime('%Y-%m-%d %H:%M:%S')
    target_str = target_ts.strftime('%Y-%m-%d %H:%M:%S')
    hour = target_ts.hour
    is_daytime = 6 <= hour <= 18

    new_rows = []
    for zone_id in df['zone_id'].unique():
        zdf = df[df['zone_id'] == zone_id].sort_values('forecast_timestamp')
        last = zdf.iloc[-1]

        new_rows.append({
            'forecast_timestamp': forecast_str,
            'target_timestamp': target_str,
            'zone_id': zone_id,
            'temperature_forecast_c': round(perturb(float(last['temperature_forecast_c']), 0.04), 4),
            'humidity_forecast_pct': round(perturb(float(last['humidity_forecast_pct']), 0.03, 20, 100), 4),
            'irradiance_forecast_wm2': round(max(0, perturb(float(last['irradiance_forecast_wm2']), 0.15)) if is_daytime else rng.uniform(0, 10), 4),
            'cloud_cover_forecast_pct': round(perturb(float(last['cloud_cover_forecast_pct']), 0.05, 0, 100), 4),
            'wind_speed_forecast_ms': round(perturb(float(last['wind_speed_forecast_ms']), 0.10, 0, 20), 4),
        })

    df_new = pd.DataFrame(new_rows)
    df_combined = pd.concat([df, df_new], ignore_index=True)
    df_combined.to_csv(path, index=False)
    print(f"  [weather_forecast]   +{len(new_rows)} rows -> forecast_ts: {forecast_str}")


# ─── main ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("Simulating new 15-minute data tick...")
    ts_str = simulate_grid_timeseries()
    simulate_renewable_assets(ts_str)
    simulate_grid_resources(ts_str)
    simulate_weather_forecast(ts_str)
    print(f"Done. New timestamp: {ts_str}")
