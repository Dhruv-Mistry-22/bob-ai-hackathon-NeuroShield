import pandas as pd
import numpy as np

def run_audit():
    # 1. Load data and check merges
    ts_df = pd.read_csv('data/grid_timeseries.csv')
    opt_df = pd.read_csv('outputs/optimization/optimization_actions.csv')
    sim_df = pd.read_csv('outputs/simulation/baseline_vs_optimized.csv')
    
    print(f"--- 1. ROW COUNT AUDIT ---")
    print(f"Total rows in sim_df: {len(sim_df)}")
    unique_count = len(sim_df.drop_duplicates(subset=['target_timestamp', 'zone_id']))
    print(f"Unique (timestamp, zone_id) in sim_df: {unique_count}")
    
    # Calculate MW -> MWh directly
    baseline_mw_sum = sim_df['baseline_curtailment_mw'].sum()
    opt_mw_sum = sim_df['optimized_curtailment_mw'].sum()
    print(f"Baseline MW Sum * 0.25 = {baseline_mw_sum * 0.25:.2f} MWh")
    print(f"Optimized MW Sum * 0.25 = {opt_mw_sum * 0.25:.2f} MWh")
    print("\n--- 2. EMPIRICAL FLOW EQUATION VALIDATION (5 examples) ---")
    
    # Pick 5 rows with varied actions
    sim_df['total_action'] = sim_df['battery_charge_mw'] + sim_df['battery_discharge_mw'] + sim_df['demand_response_mw']
    sample = sim_df[sim_df['total_action'] > 50].head(5)
    
    # We need hydro from ts_df because we didn't save it in sim_df. Let's merge it back.
    sample = pd.merge(sample, ts_df[['timestamp', 'zone_id', 'hydro_generation_mw']], left_on=['target_timestamp', 'zone_id'], right_on=['timestamp', 'zone_id'])
    
    for _, row in sample.iterrows():
        dem = row['baseline_demand_mw']
        hydro = row['hydro_generation_mw']
        flow = row['baseline_transmission_flow_mw']
        ch = row['battery_charge_mw']
        dch = row['battery_discharge_mw']
        dr = row['demand_response_mw']
        disp = row['dispatch_generation_mw']
        opt_flow = row['optimized_transmission_flow_mw']
        
        print(f"Time: {row['target_timestamp']}, Zone: {row['zone_id']}")
        print(f"  Base Dem: {dem:.1f}, Hydro: {hydro:.1f} -> Dem-Hydro: {dem-hydro:.1f}")
        print(f"  Base Flow: {flow:.1f}")
        print(f"  Actions -> Ch: {ch:.1f}, Dch: {dch:.1f}, DR: {dr:.1f}, Disp: {disp:.1f}")
        print(f"  Calc Opt Flow: {opt_flow:.1f}")
        print()

    print("--- 3. CURTAILMENT EQUATION VALIDATION (5 examples) ---")
    # 1. battery charging
    # 2. battery discharging
    # 3. DR
    # 4. dispatch
    # 5. explicit curtailment
    
    c1 = sim_df[sim_df['battery_charge_mw'] > 100].head(1)
    c2 = sim_df[sim_df['battery_discharge_mw'] > 100].head(1)
    c3 = sim_df[sim_df['demand_response_mw'] > 50].head(1)
    c4 = sim_df[sim_df['dispatch_generation_mw'] > 100].head(1)
    c5 = sim_df[sim_df['renewable_curtailment_action_mw'] > 100].head(1)
    
    for case, row in zip(['Charge', 'Discharge', 'DR', 'Dispatch', 'ExplicitCurt'], [c1, c2, c3, c4, c5]):
        if row.empty: continue
        row = row.iloc[0]
        avail = row['baseline_renewable_mw']
        base_curt = row['baseline_curtailment_mw']
        base_abs = avail - base_curt
        ch = row['battery_charge_mw']
        dch = row['battery_discharge_mw']
        dr = row['demand_response_mw']
        disp = row['dispatch_generation_mw']
        expl_curt = row['renewable_curtailment_action_mw']
        opt_curt = row['optimized_curtailment_mw']
        
        delta = ch - dch - dr - disp
        calc_abs = np.maximum(0, np.minimum(avail, base_abs + delta))
        
        print(f"[{case}]")
        print(f"  RenAvail: {avail:.1f}, BaseCurt: {base_curt:.1f}, BaseAbs: {base_abs:.1f}")
        print(f"  Action -> Ch: {ch:.1f}, Dch: {dch:.1f}, DR: {dr:.1f}, Disp: {disp:.1f}, ExplCurt: {expl_curt:.1f}")
        print(f"  Delta (room change): {delta:.1f}")
        print(f"  OptAbs: {calc_abs:.1f}")
        print(f"  OptCurt: {opt_curt:.1f}")
        print()
        
    print("--- 4. AUDIT 23 OVERLOADS ---")
    overloads = sim_df[sim_df['optimized_overload_mw'] > 0]
    
    # To get predicted risk/flow, we need grid_risk_predictions.csv
    risk_df = pd.read_csv('outputs/grid_risk/grid_risk_predictions.csv')
    risk_df['target_timestamp'] = pd.to_datetime(risk_df['target_timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
    
    overloads = pd.merge(overloads, risk_df[['target_timestamp', 'zone_id', 'future_transmission_utilization', 'timestamp']], on=['target_timestamp', 'zone_id'], how='left')
    
    print(f"Found {len(overloads)} overload intervals.")
    for _, row in overloads.head(5).iterrows():
        cap = row['baseline_transmission_flow_mw'] / row['baseline_transmission_utilization_pct']
        print(f"Decision Time: {row['timestamp']}")
        print(f"Target Time: {row['target_timestamp']}, Zone: {row['zone_id']}")
        print(f"  Predicted Util (PATH 7): {row['future_transmission_utilization']*100:.1f}%")
        print(f"  Actual Base Flow: {row['baseline_transmission_flow_mw']:.1f}, Cap: {cap:.1f} ({row['baseline_transmission_utilization_pct']*100:.1f}%)")
        print(f"  Action -> Ch: {row['battery_charge_mw']:.1f}, Dch: {row['battery_discharge_mw']:.1f}, DR: {row['demand_response_mw']:.1f}")
        print(f"  Opt Flow: {row['optimized_transmission_flow_mw']:.1f} ({row['optimized_transmission_utilization_pct']*100:.1f}%)")
        print(f"  Overload: {row['optimized_overload_mw']:.1f} MW")
        print()
        
if __name__ == '__main__':
    run_audit()
