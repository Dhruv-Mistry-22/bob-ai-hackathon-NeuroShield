"""
manual_entry.py
---------------
Takes a validated dict of manual grid readings and appends one new
15-minute row to all four source CSV files.

Called from app.py after the Streamlit form is validated.
Usage:
    python scripts/manual_entry.py --json '{"zone_id": "ZONE_A", ...}'
"""

import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def next_timestamp(df, ts_col='timestamp'):
    last = pd.to_datetime(df[ts_col].max())
    return last + timedelta(minutes=15)


def append_manual_entry(entry: dict) -> dict:
    """
    entry keys (all required):
        zone_id, demand_mw, temperature_c, humidity_pct,
        wind_speed_ms, irradiance_wm2, cloud_cover_pct,
        battery_soc_pct, grid_frequency_hz, reserve_margin_pct,
        demand_spike (bool), curtailment_event (bool)

    Returns: dict with 'success', 'timestamp', 'errors'
    """
    errors = []

    # ── physics validation ─────────────────────────────────────────────────
    demand_mw       = float(entry['demand_mw'])
    wind_speed      = float(entry['wind_speed_ms'])
    irradiance      = float(entry['irradiance_wm2'])
    cloud_cover     = float(entry['cloud_cover_pct'])
    temperature     = float(entry['temperature_c'])
    humidity        = float(entry['humidity_pct'])
    soc             = float(entry['battery_soc_pct'])
    frequency       = float(entry['grid_frequency_hz'])
    reserve         = float(entry['reserve_margin_pct'])
    zone_id         = str(entry['zone_id'])

    # Derive physical quantities
    solar_gen       = max(0.0, irradiance * 0.3 * (1 - cloud_cover / 100))
    wind_gen        = max(0.0, wind_speed ** 1.5 * 4.0)

    # Load reference data to get transmission capacity and other zone-level params
    ts_df   = pd.read_csv('data/grid_timeseries.csv')
    zone_df = ts_df[ts_df['zone_id'] == zone_id].sort_values('timestamp')

    if zone_df.empty:
        errors.append(f"Zone '{zone_id}' not found in dataset.")
        return {'success': False, 'errors': errors}

    last_row       = zone_df.iloc[-1]
    tx_capacity    = int(last_row['transmission_capacity_mw'])
    hydro_gen      = float(last_row['hydro_generation_mw'])  # carry forward
    dr_avail       = int(last_row['demand_response_available_mw'])

    renewable_avail     = solar_gen + wind_gen + hydro_gen
    renewable_dispatched = min(renewable_avail, demand_mw * 0.4)
    curtailment     = max(0.0, renewable_avail - renewable_dispatched)
    grid_import     = max(0.0, demand_mw - renewable_dispatched - hydro_gen)
    tx_flow         = min(grid_import + renewable_dispatched, tx_capacity * 0.95)

    # ── cross-field validation rules ───────────────────────────────────────
    if demand_mw < 100:
        errors.append(f"Demand ({demand_mw:.0f} MW) is unrealistically low. Minimum 100 MW.")
    if demand_mw > 5000:
        errors.append(f"Demand ({demand_mw:.0f} MW) exceeds maximum 5000 MW.")

    if wind_speed > 25:
        errors.append(f"Wind speed ({wind_speed:.1f} m/s) exceeds physical turbine cut-out speed (25 m/s).")

    if irradiance > 1200:
        errors.append(f"Irradiance ({irradiance:.0f} W/m²) exceeds maximum possible solar irradiance (1200 W/m²).")

    if cloud_cover > 0 and irradiance > 900:
        errors.append(f"Inconsistency: Cloud cover {cloud_cover:.0f}% with irradiance {irradiance:.0f} W/m². "
                      f"High cloud cover implies reduced irradiance.")

    if frequency < 49.0 or frequency > 51.0:
        errors.append(f"Grid frequency ({frequency:.3f} Hz) outside safe operating band (49–51 Hz).")

    if soc < 5 or soc > 100:
        errors.append(f"Battery SOC ({soc:.1f}%) outside physical bounds (5–100%).")

    if temperature < -30 or temperature > 55:
        errors.append(f"Temperature ({temperature:.1f}°C) is outside plausible ambient range (−30 to 55°C).")

    if humidity < 0 or humidity > 100:
        errors.append(f"Humidity ({humidity:.1f}%) must be between 0 and 100%.")

    if reserve < 0 or reserve > 60:
        errors.append(f"Reserve margin ({reserve:.1f}%) outside valid range (0–60%).")

    if tx_flow > tx_capacity:
        errors.append(f"Derived transmission flow ({tx_flow:.0f} MW) exceeds zone capacity ({tx_capacity} MW). "
                      f"Reduce demand or check generation mix.")

    if errors:
        return {'success': False, 'errors': errors}

    # ── compute new timestamp ──────────────────────────────────────────────
    new_ts = next_timestamp(ts_df)
    ts_str = new_ts.strftime('%Y-%m-%d %H:%M:%S')

    # ── 1. Append to grid_timeseries ──────────────────────────────────────
    new_row = {
        'timestamp': ts_str,
        'zone_id': zone_id,
        'demand_mw': round(demand_mw, 4),
        'temperature_c': round(temperature, 4),
        'humidity_pct': round(humidity, 4),
        'wind_speed_ms': round(wind_speed, 4),
        'irradiance_wm2': round(irradiance, 4),
        'cloud_cover_pct': round(cloud_cover, 4),
        'solar_generation_mw': round(solar_gen, 4),
        'wind_generation_mw': round(wind_gen, 4),
        'hydro_generation_mw': round(hydro_gen, 4),
        'grid_import_mw': round(grid_import, 4),
        'battery_charge_mw': 0,
        'battery_discharge_mw': 0,
        'battery_soc_pct': round(soc, 4),
        'demand_response_available_mw': dr_avail,
        'transmission_capacity_mw': tx_capacity,
        'transmission_flow_mw': round(tx_flow, 4),
        'renewable_available_mw': round(renewable_avail, 4),
        'renewable_dispatched_mw': round(renewable_dispatched, 4),
        'curtailment_mw': round(curtailment, 4),
        'grid_frequency_hz': round(frequency, 4),
        'reserve_margin_pct': round(reserve, 4),
        'holiday_flag': 0,
        'demand_spike_ground_truth': int(entry.get('demand_spike', False)),
        'curtailment_event_ground_truth': int(curtailment > 5),
    }
    ts_df_updated = pd.concat([ts_df, pd.DataFrame([new_row])], ignore_index=True)

    # Fill missing zones with simulated values for other zones in the same timestamp
    other_zones = [z for z in ts_df['zone_id'].unique() if z != zone_id]
    rng = np.random.default_rng()
    for oz in other_zones:
        oz_last = ts_df[ts_df['zone_id'] == oz].sort_values('timestamp').iloc[-1]
        oz_row = new_row.copy()
        oz_row['zone_id'] = oz
        oz_row['demand_mw'] = round(float(oz_last['demand_mw']) * rng.uniform(0.97, 1.03), 4)
        oz_row['transmission_capacity_mw'] = int(oz_last['transmission_capacity_mw'])
        oz_row['demand_response_available_mw'] = int(oz_last['demand_response_available_mw'])
        ts_df_updated = pd.concat([ts_df_updated, pd.DataFrame([oz_row])], ignore_index=True)

    ts_df_updated.to_csv('data/grid_timeseries.csv', index=False)

    # ── 2. Append to renewable_assets (carry last values + new ts) ────────
    assets_df = pd.read_csv('data/renewable_assets.csv')
    last_assets = assets_df.sort_values('timestamp').groupby('asset_id', as_index=False).last()
    last_assets['timestamp'] = ts_str
    last_assets['maintenance_age_days'] = last_assets['maintenance_age_days'].astype(int) + 1
    assets_df_updated = pd.concat([assets_df, last_assets], ignore_index=True)
    assets_df_updated.to_csv('data/renewable_assets.csv', index=False)

    # ── 3. Append to grid_resources (carry last values + new ts) ──────────
    res_df = pd.read_csv('data/grid_resources.csv')
    last_res = res_df.sort_values('timestamp').groupby('resource_id', as_index=False).last()
    last_res['timestamp'] = ts_str
    last_res['current_soc_pct'] = last_res['current_soc_pct'].apply(
        lambda x: round(float(x) * rng.uniform(0.98, 1.02), 4) if pd.notna(x) else x
    )
    res_df_updated = pd.concat([res_df, last_res], ignore_index=True)
    res_df_updated.to_csv('data/grid_resources.csv', index=False)

    # ── 4. Append to weather_forecast (carry last + new ts) ───────────────
    wx_df = pd.read_csv('data/weather_forecast.csv')
    last_wx = wx_df.sort_values('forecast_timestamp').groupby('zone_id', as_index=False).last()
    target_ts = (new_ts + timedelta(hours=4)).strftime('%Y-%m-%d %H:%M:%S')
    last_wx['forecast_timestamp'] = ts_str
    last_wx['target_timestamp'] = target_ts
    wx_df_updated = pd.concat([wx_df, last_wx], ignore_index=True)
    wx_df_updated.to_csv('data/weather_forecast.csv', index=False)

    return {
        'success': True,
        'timestamp': ts_str,
        'derived': {
            'solar_generation_mw': round(solar_gen, 2),
            'wind_generation_mw': round(wind_gen, 2),
            'curtailment_mw': round(curtailment, 2),
            'transmission_flow_mw': round(tx_flow, 2),
            'transmission_capacity_mw': tx_capacity,
            'utilization_pct': round(tx_flow / tx_capacity * 100, 1),
        },
        'errors': []
    }


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--json', required=True)
    args = parser.parse_args()
    entry = json.loads(args.json)
    result = append_manual_entry(entry)
    print(json.dumps(result, indent=2))
