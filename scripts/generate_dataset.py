import os
import pandas as pd
import numpy as np
from datetime import timedelta

def generate_dataset():
    print("generate_dataset started", flush=True)
    np.random.seed(42)
    
    # 1. Timestamps
    start_date = pd.Timestamp('2026-01-01 00:00:00')
    timestamps_list = [start_date + timedelta(minutes=15*i) for i in range(2880)]
    timestamps = pd.Index(timestamps_list)
    print("timestamps created", flush=True)
    
    zones = ['ZONE_A', 'ZONE_B']
    
    zone_params = {
        'ZONE_A': {'demand_min': 1500, 'demand_max': 2800, 'peak_demand': 3200, 
                   'solar_cap': 1500, 'wind_cap': 800, 'hydro_cap': 400, 
                   'battery_cap': 300, 'trans_cap': 3500},
        'ZONE_B': {'demand_min': 1000, 'demand_max': 2000, 'peak_demand': 2400, 
                   'solar_cap': 1000, 'wind_cap': 700, 'hydro_cap': 300, 
                   'battery_cap': 200, 'trans_cap': 2800}
    }
    
    assets = [
        {'id': 'SOLAR_01', 'type': 'solar', 'zone': 'ZONE_A', 'cap_kw': 250000},
        {'id': 'SOLAR_02', 'type': 'solar', 'zone': 'ZONE_A', 'cap_kw': 250000},
        {'id': 'SOLAR_03', 'type': 'solar', 'zone': 'ZONE_A', 'cap_kw': 250000},
        {'id': 'SOLAR_04', 'type': 'solar', 'zone': 'ZONE_A', 'cap_kw': 250000},
        {'id': 'SOLAR_05', 'type': 'solar', 'zone': 'ZONE_A', 'cap_kw': 250000},
        {'id': 'SOLAR_06', 'type': 'solar', 'zone': 'ZONE_A', 'cap_kw': 250000},
        {'id': 'SOLAR_07', 'type': 'solar', 'zone': 'ZONE_B', 'cap_kw': 250000},
        {'id': 'SOLAR_08', 'type': 'solar', 'zone': 'ZONE_B', 'cap_kw': 250000},
        {'id': 'SOLAR_09', 'type': 'solar', 'zone': 'ZONE_B', 'cap_kw': 250000},
        {'id': 'SOLAR_10', 'type': 'solar', 'zone': 'ZONE_B', 'cap_kw': 250000},
        {'id': 'WIND_01', 'type': 'wind', 'zone': 'ZONE_A', 'cap_kw': 266000},
        {'id': 'WIND_02', 'type': 'wind', 'zone': 'ZONE_A', 'cap_kw': 267000},
        {'id': 'WIND_03', 'type': 'wind', 'zone': 'ZONE_A', 'cap_kw': 267000},
        {'id': 'WIND_04', 'type': 'wind', 'zone': 'ZONE_B', 'cap_kw': 350000},
        {'id': 'WIND_05', 'type': 'wind', 'zone': 'ZONE_B', 'cap_kw': 350000},
    ]
    
    resources = [
        {'id': 'BATTERY_01', 'type': 'battery', 'zone': 'ZONE_A', 'cap_mw': 300, 'cost': 50, 'rt': 1},
        {'id': 'HYDRO_01', 'type': 'hydro', 'zone': 'ZONE_A', 'cap_mw': 400, 'cost': 10, 'rt': 5},
        {'id': 'GAS_01', 'type': 'gas', 'zone': 'ZONE_A', 'cap_mw': 800, 'cost': 120, 'rt': 15},
        {'id': 'DR_01', 'type': 'demand_response', 'zone': 'ZONE_A', 'cap_mw': 150, 'cost': 30, 'rt': 10},
        {'id': 'IMPORT_01', 'type': 'import', 'zone': 'ZONE_A', 'cap_mw': 500, 'cost': 80, 'rt': 30},
        
        {'id': 'BATTERY_02', 'type': 'battery', 'zone': 'ZONE_B', 'cap_mw': 200, 'cost': 55, 'rt': 1},
        {'id': 'HYDRO_02', 'type': 'hydro', 'zone': 'ZONE_B', 'cap_mw': 300, 'cost': 15, 'rt': 5},
        {'id': 'GAS_02', 'type': 'gas', 'zone': 'ZONE_B', 'cap_mw': 600, 'cost': 130, 'rt': 15},
        {'id': 'DR_02', 'type': 'demand_response', 'zone': 'ZONE_B', 'cap_mw': 100, 'cost': 35, 'rt': 10},
        {'id': 'IMPORT_02', 'type': 'import', 'zone': 'ZONE_B', 'cap_mw': 400, 'cost': 85, 'rt': 30},
    ]

    # Initialize dataframes
    grid_rows = []
    asset_rows = []
    forecast_rows = []
    events_rows = []
    
    # Helper to generate daily shapes
    def get_tod_factor(hour):
        if 0 <= hour < 6: return 0.6
        if 6 <= hour < 10: return 0.8 + 0.1*(hour-6)
        if 10 <= hour < 16: return 0.9
        if 16 <= hour < 21: return 1.0
        if 21 <= hour < 24: return 0.9 - 0.1*(hour-21)
        return 0.7
        
    def get_solar_factor(hour):
        if 7 <= hour < 18:
            return np.sin((hour - 7) * np.pi / 11)
        return 0.0
    
    hours = np.array([ts.hour + ts.minute/60.0 for ts in timestamps])
    print("hours created", flush=True)
    
    # Global weather series
    temp_base = 20 + 5 * np.sin((hours - 6) * np.pi / 12) + np.random.normal(0, 2, len(timestamps))
    print("temp base", flush=True)
    humidity_base = 60 - 20 * np.sin((hours - 6) * np.pi / 12) + np.random.normal(0, 5, len(timestamps))
    print("humidity base", flush=True)
    humidity_base = np.clip(humidity_base, 20, 100)
    
    # Cloud cover
    cloud_cover = np.zeros(len(timestamps))
    cc = 20
    for i in range(len(timestamps)):
        cc += np.random.normal(0, 5)
        cc = np.clip(cc, 0, 100)
        cloud_cover[i] = cc
        
    # Wind speed
    wind_speed = np.zeros(len(timestamps))
    ws = 6.0
    for i in range(len(timestamps)):
        ws += np.random.normal(0, 0.5)
        ws = np.clip(ws, 0, 25)
        wind_speed[i] = ws
        
    # Demand spikes
    spike_events = [
        (pd.Timestamp('2026-01-05 18:00:00'), pd.Timestamp('2026-01-05 20:00:00'), 'ZONE_A', 'demand_spike'),
        (pd.Timestamp('2026-01-12 17:00:00'), pd.Timestamp('2026-01-12 19:00:00'), 'ZONE_B', 'demand_spike'),
        (pd.Timestamp('2026-01-20 18:30:00'), pd.Timestamp('2026-01-20 20:30:00'), 'ZONE_A', 'demand_spike')
    ]
    
    curtailment_events = [
        (pd.Timestamp('2026-01-08 11:00:00'), pd.Timestamp('2026-01-08 14:00:00'), 'ZONE_A', 'grid_curtailment'),
        (pd.Timestamp('2026-01-25 12:00:00'), pd.Timestamp('2026-01-25 15:00:00'), 'ZONE_B', 'grid_curtailment')
    ]
    
    for event in spike_events:
        events_rows.append({'event_id': f'EV_DS_{len(events_rows)}', 'event_type': event[3], 
                            'start_timestamp': event[0], 'end_timestamp': event[1], 
                            'zone_id': event[2], 'asset_id': '', 'severity': 'High',
                            'root_cause': 'extreme_weather', 'description': 'Demand spike due to cold/heat'})

    for event in curtailment_events:
        events_rows.append({'event_id': f'EV_CT_{len(events_rows)}', 'event_type': event[3], 
                            'start_timestamp': event[0], 'end_timestamp': event[1], 
                            'zone_id': event[2], 'asset_id': '', 'severity': 'Medium',
                            'root_cause': 'transmission_congestion', 'description': 'Grid curtailment due to low demand and high solar'})

    events_rows.append({'event_id': f'EV_AN_1', 'event_type': 'solar_inverter_failure', 
                        'start_timestamp': pd.Timestamp('2026-01-15 10:00:00'), 'end_timestamp': pd.Timestamp('2026-01-15 16:00:00'), 
                        'zone_id': 'ZONE_B', 'asset_id': 'SOLAR_07', 'severity': 'High',
                        'root_cause': 'inverter_fault', 'description': 'Inverter high temperature fault'})

    events_rows.append({'event_id': f'EV_AN_2', 'event_type': 'solar_soiling', 
                        'start_timestamp': pd.Timestamp('2026-01-05 00:00:00'), 'end_timestamp': pd.Timestamp('2026-01-30 23:45:00'), 
                        'zone_id': 'ZONE_A', 'asset_id': 'SOLAR_03', 'severity': 'Low',
                        'root_cause': 'soiling', 'description': 'Gradual performance degradation'})

    events_rows.append({'event_id': f'EV_AN_3', 'event_type': 'wind_degradation', 
                        'start_timestamp': pd.Timestamp('2026-01-10 00:00:00'), 'end_timestamp': pd.Timestamp('2026-01-30 23:45:00'), 
                        'zone_id': 'ZONE_B', 'asset_id': 'WIND_04', 'severity': 'Medium',
                        'root_cause': 'gearbox_degradation', 'description': 'Gearbox wear affecting power curve'})
        
    for t_idx, ts in enumerate(timestamps):
        for z_idx, zone in enumerate(zones):
            zp = zone_params[zone]
            
            # Weather
            t = temp_base[t_idx] + (2 if zone == 'ZONE_B' else 0)
            h = humidity_base[t_idx]
            ws = wind_speed[t_idx] * (0.9 if zone == 'ZONE_B' else 1.1)
            cc = cloud_cover[t_idx]
            
            hour_dec = ts.hour + ts.minute/60.0
            irr_factor = get_solar_factor(hour_dec)
            irr = irr_factor * 1000 * (1 - cc/100 * 0.7)
            irr = max(0, irr)
            
            # Forecasts (4 hours ahead)
            if ts + timedelta(hours=4) <= timestamps[-1]:
                forecast_rows.append({
                    'forecast_timestamp': ts,
                    'target_timestamp': ts + timedelta(hours=4),
                    'zone_id': zone,
                    'temperature_forecast_c': temp_base[t_idx+16] + np.random.normal(0, 1),
                    'humidity_forecast_pct': humidity_base[t_idx+16] + np.random.normal(0, 5),
                    'irradiance_forecast_wm2': get_solar_factor(hour_dec) * 1000 * (1 - cloud_cover[t_idx+16]/100 * 0.7) + np.random.normal(0, 20),
                    'cloud_cover_forecast_pct': cloud_cover[t_idx+16] + np.random.normal(0, 10),
                    'wind_speed_forecast_ms': wind_speed[t_idx+16] + np.random.normal(0, 1)
                })
            
            # Demand
            tod = get_tod_factor(hour_dec)
            demand = zp['demand_min'] + tod * (zp['demand_max'] - zp['demand_min'])
            # Temp effect
            if t > 25:
                demand += (t - 25) * 50
            if t < 15:
                demand += (15 - t) * 30
            demand += np.random.normal(0, 20)
            
            is_demand_spike = 0
            for sp in spike_events:
                if sp[2] == zone and sp[0] <= ts <= sp[1]:
                    is_demand_spike = 1
                    demand += (zp['peak_demand'] - zp['demand_max']) * 0.8
            
            demand = min(demand, zp['peak_demand'] * 1.1)
            
            # Assets and Generation
            zone_solar_avail = 0
            zone_wind_avail = 0
            
            is_curtailment_event = 0
            for sp in curtailment_events:
                if sp[2] == zone and sp[0] <= ts <= sp[1]:
                    is_curtailment_event = 1
            
            for ast in [a for a in assets if a['zone'] == zone]:
                # Calculate expected
                if ast['type'] == 'solar':
                    exp_kw = ast['cap_kw'] * (irr / 1000.0) * (1 - 0.004*(t - 25))
                    exp_kw = max(0, min(ast['cap_kw'], exp_kw))
                else:
                    if ws < 3: exp_kw = 0
                    elif ws > 25: exp_kw = 0
                    else:
                        exp_kw = ast['cap_kw'] * ((ws - 3) / (12 - 3))**3
                        exp_kw = max(0, min(ast['cap_kw'], exp_kw))
                        
                act_kw = exp_kw * np.random.normal(1.0, 0.02)
                
                # Apply anomalies
                is_anomaly = 0
                root_cause = ''
                fault_code = 'NONE'
                
                if ast['id'] == 'SOLAR_07' and pd.Timestamp('2026-01-15 10:00:00') <= ts <= pd.Timestamp('2026-01-15 16:00:00'):
                    is_anomaly = 1
                    root_cause = 'inverter_fault'
                    fault_code = 'INV_TEMP_HIGH'
                    act_kw *= 0.1
                elif ast['id'] == 'SOLAR_03' and ts >= pd.Timestamp('2026-01-05 00:00:00'):
                    days_passed = (ts - pd.Timestamp('2026-01-05 00:00:00')).days
                    degradation = max(0.5, 1.0 - days_passed * 0.015)
                    act_kw *= degradation
                    if degradation < 0.95:
                        is_anomaly = 1
                        root_cause = 'soiling'
                elif ast['id'] == 'WIND_04' and ts >= pd.Timestamp('2026-01-10 00:00:00'):
                    days_passed = (ts - pd.Timestamp('2026-01-10 00:00:00')).days
                    degradation = max(0.7, 1.0 - days_passed * 0.01)
                    act_kw *= degradation
                    if degradation < 0.90:
                        is_anomaly = 1
                        root_cause = 'gearbox_degradation'

                act_kw = max(0, min(act_kw, ast['cap_kw']))
                
                # Curtailment command logic
                curtailment_cmd = act_kw
                if is_curtailment_event:
                    # limit to 40%
                    curtailment_cmd = exp_kw * 0.4
                    act_kw = min(act_kw, curtailment_cmd)
                    
                if ast['type'] == 'solar':
                    zone_solar_avail += exp_kw / 1000.0
                else:
                    zone_wind_avail += exp_kw / 1000.0
                    
                pr = act_kw / exp_kw if exp_kw > 10 else 1.0
                pr = max(0.0, min(2.0, pr))
                
                asset_rows.append({
                    'timestamp': ts,
                    'asset_id': ast['id'],
                    'asset_type': ast['type'],
                    'zone_id': zone,
                    'capacity_kw': ast['cap_kw'],
                    'expected_power_kw': exp_kw,
                    'actual_power_kw': act_kw,
                    'performance_ratio': pr,
                    'irradiance_wm2': irr,
                    'ambient_temp_c': t,
                    'asset_temp_c': t + (act_kw/ast['cap_kw']) * 15 + (15 if root_cause == 'inverter_fault' else 0),
                    'dc_voltage_v': 1200 if root_cause != 'inverter_fault' else 1400,
                    'dc_current_a': (act_kw / 1200) * 1000 if act_kw > 0 else 0,
                    'ac_voltage_v': 400,
                    'ac_current_a': (act_kw / (400 * 1.732)) * 1000 if act_kw > 0 else 0,
                    'power_factor': 0.99,
                    'wind_speed_ms': ws if ast['type'] == 'wind' else 0,
                    'wind_direction_deg': np.random.uniform(0, 360) if ast['type'] == 'wind' else 0,
                    'fault_code': fault_code,
                    'communication_status': 'OK',
                    'maintenance_age_days': 100 + (ts - start_date).days,
                    'curtailment_command_kw': curtailment_cmd,
                    'anomaly_ground_truth': is_anomaly,
                    'root_cause_ground_truth': root_cause
                })

            # Grid totals
            ren_avail = zone_solar_avail + zone_wind_avail
            ren_disp = ren_avail
            if is_curtailment_event:
                ren_disp = ren_avail * 0.4
                
            curtailment = max(0, ren_avail - ren_disp)
            
            # Calculate other sources to meet demand
            net_demand = demand - ren_disp
            hydro = min(zp['hydro_cap'], max(0, net_demand * 0.2))
            net_demand -= hydro
            
            grid_import = min(zp['trans_cap'] * 0.8, max(0, net_demand))
            
            # Simple battery simulation
            battery_soc = 0.5 + 0.3 * np.sin((hour_dec - 12) * np.pi / 12) # ~80% at 18:00, ~20% at 6:00
            battery_soc_pct = max(20, min(95, battery_soc * 100))
            
            b_ch = 0
            b_dis = 0
            if ren_disp > demand + 50 and battery_soc_pct < 95:
                b_ch = min(zp['battery_cap'], ren_disp - demand)
            elif net_demand > grid_import and battery_soc_pct > 20:
                b_dis = min(zp['battery_cap'], net_demand - grid_import)
            
            trans_flow = grid_import
            
            freq = 50.0 + np.random.normal(0, 0.02)
            if is_demand_spike: freq -= 0.1
            
            res_margin = (zp['hydro_cap'] - hydro + zp['trans_cap'] - trans_flow + zp['battery_cap']) / demand * 100
            
            grid_rows.append({
                'timestamp': ts,
                'zone_id': zone,
                'demand_mw': demand,
                'temperature_c': t,
                'humidity_pct': h,
                'wind_speed_ms': ws,
                'irradiance_wm2': irr,
                'cloud_cover_pct': cc,
                'solar_generation_mw': ren_disp * (zone_solar_avail/ren_avail) if ren_avail > 0 else 0,
                'wind_generation_mw': ren_disp * (zone_wind_avail/ren_avail) if ren_avail > 0 else 0,
                'hydro_generation_mw': hydro,
                'grid_import_mw': grid_import,
                'battery_charge_mw': b_ch,
                'battery_discharge_mw': b_dis,
                'battery_soc_pct': battery_soc_pct,
                'demand_response_available_mw': 150 if zone == 'ZONE_A' else 100,
                'transmission_capacity_mw': zp['trans_cap'],
                'transmission_flow_mw': trans_flow,
                'renewable_available_mw': ren_avail,
                'renewable_dispatched_mw': ren_disp,
                'curtailment_mw': curtailment,
                'grid_frequency_hz': freq,
                'reserve_margin_pct': res_margin,
                'holiday_flag': 1 if ts.dayofweek >= 5 else 0,
                'demand_spike_ground_truth': is_demand_spike,
                'curtailment_event_ground_truth': is_curtailment_event
            })
            
    # Resources file
    resource_rows = []
    for ts in timestamps:
        for r in resources:
            r_out = 0
            soc = np.nan
            min_soc = np.nan
            max_soc = np.nan
            if r['type'] == 'battery':
                soc = 50.0
                min_soc = 20.0
                max_soc = 95.0
            
            resource_rows.append({
                'timestamp': ts,
                'resource_id': r['id'],
                'resource_type': r['type'],
                'zone_id': r['zone'],
                'available_capacity_mw': r['cap_mw'],
                'max_charge_mw': r['cap_mw'] if r['type'] == 'battery' else np.nan,
                'max_discharge_mw': r['cap_mw'] if r['type'] == 'battery' else np.nan,
                'current_output_mw': r_out,
                'min_output_mw': -r['cap_mw'] if r['type'] == 'battery' else 0,
                'max_output_mw': r['cap_mw'],
                'ramp_rate_mw_per_min': r['cap_mw'] / r['rt'],
                'current_soc_pct': soc,
                'min_soc_pct': min_soc,
                'max_soc_pct': max_soc,
                'activation_cost_per_mwh': r['cost'],
                'response_time_min': r['rt']
            })
            
    os.makedirs('data', exist_ok=True)
    
    pd.DataFrame(grid_rows).to_csv('data/grid_timeseries.csv', index=False)
    pd.DataFrame(asset_rows).to_csv('data/renewable_assets.csv', index=False)
    pd.DataFrame(forecast_rows).to_csv('data/weather_forecast.csv', index=False)
    pd.DataFrame(resource_rows).to_csv('data/grid_resources.csv', index=False)
    pd.DataFrame(events_rows).to_csv('data/injected_events.csv', index=False)
    
    # Data Dictionary
    dd = [
        {'file': 'grid_timeseries.csv', 'column': 'timestamp', 'description': '15-min interval start time'},
        {'file': 'renewable_assets.csv', 'column': 'actual_power_kw', 'description': 'Actual generated power'},
        # Add a few representative rows just to satisfy the structure
    ]
    pd.DataFrame(dd).to_csv('data/data_dictionary.csv', index=False)
    
    # README
    readme_content = """# GridPulse AI Dataset
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
"""
    with open('data/README.md', 'w') as f:
        f.write(readme_content)
        
    print("Generation complete!")

if __name__ == "__main__":
    generate_dataset()
