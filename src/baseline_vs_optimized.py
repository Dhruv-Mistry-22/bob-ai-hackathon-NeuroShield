import pandas as pd
import numpy as np
import os
import json
import traceback
import sys

from datetime import timedelta, datetime
import dateutil.parser

def main():
    try:
        os.makedirs('outputs/simulation', exist_ok=True)
        
        ts_df = pd.read_csv('data/grid_timeseries.csv')
        opt_df = pd.read_csv('outputs/optimization/optimization_actions.csv')
        
        # Avoid pandas vectorized datetime due to environment crash
        def add_60m(ts_str):
            dt = dateutil.parser.parse(ts_str)
            dt += timedelta(minutes=60)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
            
        opt_df['target_timestamp'] = opt_df['timestamp'].apply(add_60m)
        opt_df['action_key'] = opt_df['resource_type'].str.upper() + '_' + opt_df['action'].str.upper()
        
        actions_pivot = opt_df.pivot_table(
            index=['target_timestamp', 'zone_id'],
            columns='action_key',
            values='action_mw',
            aggfunc='sum',
            fill_value=0
        ).reset_index()
        
        expected_keys = ['BATTERY_CHARGE', 'BATTERY_DISCHARGE', 'DEMAND_RESPONSE_ACTIVATE', 'DISPATCH_ACTIVATE', 'RENEWABLE_CURTAIL']
        for k in expected_keys:
            if k not in actions_pivot.columns:
                actions_pivot[k] = 0
                
        sim_df = pd.merge(
            actions_pivot,
            ts_df,
            left_on=['target_timestamp', 'zone_id'],
            right_on=['timestamp', 'zone_id'],
            how='inner'
        )
        
        sim_df = sim_df.rename(columns={'timestamp': 'baseline_timestamp'})
        sim_df['baseline_demand_mw'] = sim_df['demand_mw']
        sim_df['baseline_solar_mw'] = sim_df['solar_generation_mw']
        sim_df['baseline_wind_mw'] = sim_df['wind_generation_mw']
        sim_df['baseline_renewable_mw'] = sim_df['renewable_available_mw']
        sim_df['baseline_curtailment_mw'] = sim_df['curtailment_mw']
        sim_df['baseline_transmission_flow_mw'] = sim_df['transmission_flow_mw']
        sim_df['baseline_transmission_capacity_mw'] = sim_df['transmission_capacity_mw']
        sim_df['baseline_transmission_utilization_pct'] = sim_df['transmission_flow_mw'] / sim_df['transmission_capacity_mw']
        sim_df['baseline_overload_mw'] = np.maximum(0, sim_df['transmission_flow_mw'] - sim_df['transmission_capacity_mw'])
        sim_df['baseline_renewable_absorbed_mw'] = sim_df['renewable_available_mw'] - sim_df['curtailment_mw']
        
        sim_df['battery_charge_mw'] = sim_df['BATTERY_CHARGE']
        sim_df['battery_discharge_mw'] = sim_df['BATTERY_DISCHARGE']
        sim_df['demand_response_mw'] = sim_df['DEMAND_RESPONSE_ACTIVATE']
        sim_df['dispatch_generation_mw'] = sim_df['DISPATCH_ACTIVATE']
        sim_df['renewable_curtailment_action_mw'] = sim_df['RENEWABLE_CURTAIL']
        
        sim_df['optimized_transmission_flow_mw'] = sim_df['baseline_transmission_flow_mw'] + sim_df['battery_charge_mw'] - sim_df['battery_discharge_mw'] - sim_df['demand_response_mw'] - sim_df['dispatch_generation_mw']
        
        delta = sim_df['battery_charge_mw'] - sim_df['battery_discharge_mw'] - sim_df['demand_response_mw'] - sim_df['dispatch_generation_mw']
        
        sim_df['optimized_renewable_absorbed_mw'] = np.minimum(
            sim_df['baseline_renewable_mw'],
            sim_df['baseline_renewable_absorbed_mw'] + delta
        )
        sim_df['optimized_renewable_absorbed_mw'] = np.maximum(0, sim_df['optimized_renewable_absorbed_mw'])
        
        sim_df['optimized_curtailment_mw'] = sim_df['baseline_renewable_mw'] - sim_df['optimized_renewable_absorbed_mw']
        sim_df['optimized_curtailment_mw'] = np.maximum(sim_df['optimized_curtailment_mw'], sim_df['renewable_curtailment_action_mw'])
        
        sim_df['optimized_transmission_utilization_pct'] = sim_df['optimized_transmission_flow_mw'] / sim_df['baseline_transmission_capacity_mw']
        sim_df['optimized_overload_mw'] = np.maximum(0, sim_df['optimized_transmission_flow_mw'] - sim_df['baseline_transmission_capacity_mw'])
        
        sim_df['optimized_renewable_absorbed_mw'] = sim_df['baseline_renewable_mw'] - sim_df['optimized_curtailment_mw']
        
        sim_df['curtailment_avoided_mw'] = sim_df['baseline_curtailment_mw'] - sim_df['optimized_curtailment_mw']
        sim_df['flow_reduction_mw'] = sim_df['baseline_transmission_flow_mw'] - sim_df['optimized_transmission_flow_mw']
        sim_df['additional_renewable_absorbed_mw'] = sim_df['optimized_renewable_absorbed_mw'] - sim_df['baseline_renewable_absorbed_mw']
        
        sim_df['baseline_overload_intervals'] = (sim_df['baseline_overload_mw'] > 0).astype(int)
        sim_df['optimized_overload_intervals'] = (sim_df['optimized_overload_mw'] > 0).astype(int)
        
        out_cols = [
            'target_timestamp', 'zone_id', 
            'baseline_demand_mw', 'baseline_renewable_mw', 'baseline_curtailment_mw', 'baseline_transmission_flow_mw', 'baseline_transmission_utilization_pct', 'baseline_overload_mw',
            'battery_charge_mw', 'battery_discharge_mw', 'demand_response_mw', 'dispatch_generation_mw', 'renewable_curtailment_action_mw',
            'optimized_curtailment_mw', 'optimized_transmission_flow_mw', 'optimized_transmission_utilization_pct', 'optimized_overload_mw',
            'curtailment_avoided_mw', 'additional_renewable_absorbed_mw', 'flow_reduction_mw',
            'baseline_overload_intervals', 'optimized_overload_intervals', 'curtailment_event_ground_truth'
        ]
        sim_df[out_cols].to_csv('outputs/simulation/baseline_vs_optimized.csv', index=False)
        
        def calc_metrics(df, subset_name):
            return {
                'subset': subset_name,
                'total_baseline_curtailment_mwh': float(df['baseline_curtailment_mw'].sum() * 0.25),
                'total_optimized_curtailment_mwh': float(df['optimized_curtailment_mw'].sum() * 0.25),
                'total_curtailment_avoided_mwh': float(df['curtailment_avoided_mw'].sum() * 0.25),
                'curtailment_reduction_pct': float((df['curtailment_avoided_mw'].sum() / df['baseline_curtailment_mw'].sum() * 100) if df['baseline_curtailment_mw'].sum() > 0 else 0),
                
                'baseline_overload_intervals': int(df['baseline_overload_intervals'].sum()),
                'optimized_overload_intervals': int(df['optimized_overload_intervals'].sum()),
                'overload_intervals_reduction_pct': float(((df['baseline_overload_intervals'].sum() - df['optimized_overload_intervals'].sum()) / df['baseline_overload_intervals'].sum() * 100) if df['baseline_overload_intervals'].sum() > 0 else 0),
                
                'baseline_avg_utilization': float(df['baseline_transmission_utilization_pct'].mean()),
                'optimized_avg_utilization': float(df['optimized_transmission_utilization_pct'].mean()),
                
                'baseline_peak_utilization': float(df['baseline_transmission_utilization_pct'].max()),
                'optimized_peak_utilization': float(df['optimized_transmission_utilization_pct'].max()),
                
                'additional_renewable_absorbed_mwh': float(df['additional_renewable_absorbed_mw'].sum() * 0.25),
                
                'total_battery_charge_mwh': float(df['battery_charge_mw'].sum() * 0.25),
                'total_battery_discharge_mwh': float(df['battery_discharge_mw'].sum() * 0.25),
                'total_dr_mwh': float(df['demand_response_mw'].sum() * 0.25),
                'total_dispatch_mwh': float(df['dispatch_generation_mw'].sum() * 0.25)
            }
            
        metrics = []
        metrics.append(calc_metrics(sim_df, 'All Timestamps'))
        high_risk = sim_df[sim_df['baseline_transmission_utilization_pct'] > 0.85]
        metrics.append(calc_metrics(high_risk, 'High-Risk Timestamps (>85% Util)'))
        event_ts = sim_df[sim_df['curtailment_event_ground_truth'] == 1]
        metrics.append(calc_metrics(event_ts, 'Curtailment Event Timestamps'))
        
        summary_df = pd.DataFrame(metrics)
        summary_df.to_csv('outputs/simulation/simulation_summary.csv', index=False)
        with open('outputs/simulation/simulation_metrics.json', 'w') as f:
            json.dump(metrics, f, indent=4)
            
        events = pd.read_csv('data/injected_events.csv')
        event_res = []
        for _, ev in events.iterrows():
            ev_start = ev['start_timestamp']
            ev_end = ev['end_timestamp']
            mask = (sim_df['target_timestamp'] >= ev_start) & (sim_df['target_timestamp'] <= ev_end)
            ev_df = sim_df[mask]
            
            if len(ev_df) > 0:
                base_curt = ev_df['baseline_curtailment_mw'].sum() * 0.25
                opt_curt = ev_df['optimized_curtailment_mw'].sum() * 0.25
                event_res.append({
                    'event_id': ev['event_id'],
                    'event_type': ev['event_type'],
                    'start_time': ev['start_timestamp'],
                    'end_time': ev['end_timestamp'],
                    'baseline_curtailment_mwh': base_curt,
                    'optimized_curtailment_mwh': opt_curt,
                    'curtailment_reduction_mwh': base_curt - opt_curt,
                    'curtailment_reduction_pct': ((base_curt - opt_curt) / base_curt * 100) if base_curt > 0 else 0,
                    'baseline_peak_utilization_pct': ev_df['baseline_transmission_utilization_pct'].max(),
                    'optimized_peak_utilization_pct': ev_df['optimized_transmission_utilization_pct'].max(),
                    'baseline_overload_intervals': ev_df['baseline_overload_intervals'].sum(),
                    'optimized_overload_intervals': ev_df['optimized_overload_intervals'].sum()
                })
        pd.DataFrame(event_res).to_csv('outputs/simulation/event_simulation_results.csv', index=False)
        
        with open('outputs/simulation/simulation_report.md', 'w') as f:
            f.write("# PATH 9: Baseline vs Optimized Simulation\n\n")
            f.write("> **These are counterfactual simulation results, not verified historical operational savings.**\n\n")
            f.write("## 1. Physical Equations and Data Physics Validation\n")
            f.write("- **Transmission Flow**: The dataset empirically demonstrates `transmission_flow_mw = demand_mw - hydro_generation_mw`. Renewables are mathematically injected *after* this measurement (downstream of the bottleneck). Thus, renewable curtailment does **not** directly relieve transmission flow in this architecture.\n")
            f.write("- **Optimized Flow**: Because battery discharge and DR offset demand (and battery charging increases it), `optimized_flow = baseline_flow + battery_charge - battery_discharge - DR_activate - dispatch_generation`\n")
            f.write("- **Optimized Curtailment**: `max(0, baseline_curtailment - battery_charge + battery_discharge + DR_activate + dispatch_generation)`. Charging the battery absorbs renewable surplus. Activating DR or discharging battery injects power into an already oversupplied network, effectively *increasing* curtailment. \n")
            f.write("- **Overload Definition**: Strict physical bounds: `overload_mw = max(0, transmission_flow_mw - transmission_capacity_mw)`.\n\n")
            
            f.write("## 2. Overall Results (All Timestamps)\n")
            all_res = summary_df.iloc[0]
            f.write(f"- Historical baseline curtailment: {all_res['total_baseline_curtailment_mwh']:.1f} MWh\n")
            f.write(f"- Simulated optimized curtailment: {all_res['total_optimized_curtailment_mwh']:.1f} MWh\n")
            f.write(f"- Estimated curtailment avoided: {all_res['total_curtailment_avoided_mwh']:.1f} MWh\n")
            f.write(f"- Estimated reduction: {all_res['curtailment_reduction_pct']:.1f}%\n")
            f.write(f"- Baseline overload intervals: {all_res['baseline_overload_intervals']}\n")
            f.write(f"- Optimized overload intervals: {all_res['optimized_overload_intervals']}\n")
            f.write(f"- Additional renewable energy absorbed: {all_res['additional_renewable_absorbed_mwh']:.1f} MWh\n\n")
    
            f.write("## 3. High-Risk Timestamps (>85% Util)\n")
            hi_res = summary_df.iloc[1]
            f.write(f"- Estimated curtailment avoided: {hi_res['total_curtailment_avoided_mwh']:.1f} MWh\n")
            f.write(f"- Curtailment reduction: {hi_res['curtailment_reduction_pct']:.1f}%\n")
            f.write(f"- Overload intervals avoided: {hi_res['baseline_overload_intervals'] - hi_res['optimized_overload_intervals']}\n\n")
    
            f.write("## 4. Curtailment-Event Timestamps\n")
            ev_res = summary_df.iloc[2]
            f.write(f"- Total battery charging MWh: {ev_res['total_battery_charge_mwh']:.1f}\n")
            f.write(f"- Total battery discharging MWh: {ev_res['total_battery_discharge_mwh']:.1f}\n")
            f.write(f"- Total DR MWh: {ev_res['total_dr_mwh']:.1f}\n")
            f.write(f"- Total dispatch MWh: {ev_res['total_dispatch_mwh']:.1f}\n")
            f.write(f"- Total residual curtailment MWh: {ev_res['total_optimized_curtailment_mwh']:.1f}\n\n")
            f.write("## 5. Limitations\n")
            f.write("- **Battery Energy Constraints**: While strict MW power injection constraints are verified, dynamic battery SOC energy constraints cannot be verified in this simulation because the dataset lacks energy_capacity_mwh.\n")
    
        res_util = summary_df[['subset', 'total_battery_charge_mwh', 'total_battery_discharge_mwh', 'total_dr_mwh', 'total_dispatch_mwh']]
        res_util.to_csv('outputs/simulation/resource_utilization.csv', index=False)
        print("Success")
    except Exception as e:
        print("Error details:", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
