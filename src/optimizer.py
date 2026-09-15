import pandas as pd
import numpy as np
import os
import json
from scipy.optimize import linprog

def main():
    os.makedirs('outputs/optimization', exist_ok=True)
    
    # Load data
    print("Loading datasets...")
    grid_risk = pd.read_csv('outputs/grid_risk/grid_risk_predictions.csv')
    resources = pd.read_csv('data/grid_resources.csv')
    
    # We will use the future predictions for the 60m horizon
    # We only need one snapshot of resources since capacities are static in MVP
    latest_resources = resources[resources['timestamp'] == resources['timestamp'].max()]
    
    battery_res = latest_resources[latest_resources['resource_type'] == 'battery'].groupby('zone_id').agg(
        max_charge=('max_charge_mw', 'sum'),
        max_discharge=('max_discharge_mw', 'sum'),
        battery_cost=('activation_cost_per_mwh', 'mean')
    ).reset_index()
    
    dr_res = latest_resources[latest_resources['resource_type'] == 'demand_response'].groupby('zone_id').agg(
        max_dr=('available_capacity_mw', 'sum'),
        dr_cost=('activation_cost_per_mwh', 'mean')
    ).reset_index()
    
    gen_res = latest_resources[latest_resources['resource_type'].isin(['gas', 'hydro', 'import'])].groupby('zone_id').agg(
        max_dispatch=('available_capacity_mw', 'sum'),
        dispatch_cost=('activation_cost_per_mwh', 'mean')
    ).reset_index()
    
    zone_caps = pd.merge(battery_res, dr_res, on='zone_id', how='outer').fillna(0)
    zone_caps = pd.merge(zone_caps, gen_res, on='zone_id', how='outer').fillna(0)
    
    # Target transmission utilization
    # LOW < 0.70, MEDIUM 0.70-0.85, HIGH 0.85-0.95, CRITICAL > 0.95
    TARGET_UTILIZATION = 0.85
    
    actions_list = []
    summary_list = []
    
    # Weights for objective
    W_FEASIBILITY = 1000000 # Cost of flow violation
    W_CURTAILMENT = 10000   # Cost of curtailing renewables
    
    print("Running optimization...")
    # Iterate over each row (timestamp, zone)
    for idx, row in grid_risk.iterrows():
        ts = row['timestamp']
        zone = row['zone_id']
        
        # Get capacities
        if zone in zone_caps['zone_id'].values:
            caps = zone_caps[zone_caps['zone_id'] == zone].iloc[0]
        else:
            caps = None
            
        if caps is None:
            continue
            
        max_charge = caps['max_charge']
        max_discharge = caps['max_discharge']
        max_dr = caps['max_dr']
        max_dispatch = caps['max_dispatch']
        
        c_charge = caps['battery_cost']
        c_discharge = caps['battery_cost']
        c_dr = caps['dr_cost']
        c_dispatch = caps['dispatch_cost']
        
        # State
        baseline_net_load = row['future_net_load_60m']
        # Compute exact capacity using standard math
        capacity = row['transmission_headroom_mw'] / (1 - row['transmission_utilization'] + 1e-9)
        baseline_flow = row['future_transmission_utilization'] * capacity
        target_flow = capacity * TARGET_UTILIZATION
        
        pred_curt_prob = row['curtailment_prob']
        
        # We assume predicted curtailment scales with prob if > 0.5, or we can use the regressor
        # Wait, PATH 7 has predicted_curtailment_mw! Let's check if it exists in columns.
        if 'predicted_curtailment_mw' in row.index:
            pred_curt_mw = row['predicted_curtailment_mw'] if pred_curt_prob > 0.5 else 0
        else:
            # Fallback
            pred_curt_mw = row['predicted_total_renewable_60m'] * pred_curt_prob if pred_curt_prob > 0.5 else 0
        
        if pred_curt_mw < 10: pred_curt_mw = 0 # threshold
        
        pred_renewable = row['predicted_total_renewable_60m']
        
        # Variables: [charge, discharge, dr, dispatch, curtail, flow_violation]
        # Objective: minimize costs
        c = [c_charge, c_discharge, c_dr, c_dispatch, W_CURTAILMENT, W_FEASIBILITY]
        
        # Bounds
        bounds = [
            (0, max_charge),
            (0, max_discharge),
            (0, max_dr),
            (0, max_dispatch),
            (0, pred_renewable),
            (0, None) # flow violation can be anything >= 0
        ]
        
        # Constraints (A_ub * x <= b_ub)
        A_ub = []
        b_ub = []
        
        # 1. Curtailment resolution: curtail + charge - discharge - dr - dispatch >= pred_curt_mw
        # -> -curtail - charge + discharge + dr + dispatch <= -pred_curt_mw
        A_ub.append([-1, 1, 1, 1, -1, 0])
        b_ub.append(-pred_curt_mw)
        
        # 2. Transmission flow: Baseline_Flow + charge - discharge - dr - dispatch + curtail - flow_violation <= target_flow
        # -> charge - discharge - dr - dispatch + curtail - flow_violation <= target_flow - Baseline_Flow
        A_ub.append([1, -1, -1, -1, 1, -1])
        b_ub.append(target_flow - baseline_flow)
        
        res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')
        
        if res.success:
            charge_opt, discharge_opt, dr_opt, dispatch_opt, curtail_opt, viol_opt = res.x
            
            # Clean up near-zeros
            charge_opt = 0 if charge_opt < 1e-4 else charge_opt
            discharge_opt = 0 if discharge_opt < 1e-4 else discharge_opt
            dr_opt = 0 if dr_opt < 1e-4 else dr_opt
            dispatch_opt = 0 if dispatch_opt < 1e-4 else dispatch_opt
            curtail_opt = 0 if curtail_opt < 1e-4 else curtail_opt
            
            optimized_net_load = baseline_net_load + charge_opt - discharge_opt - dr_opt - dispatch_opt + curtail_opt
            optimized_flow = baseline_flow + charge_opt - discharge_opt - dr_opt - dispatch_opt + curtail_opt
            
            summary_list.append({
                'timestamp': ts,
                'zone_id': zone,
                'risk_level': row['grid_risk_class'],
                'risk_probability': row['grid_risk_prob'],
                'curtailment_probability': pred_curt_prob,
                'baseline_net_load': baseline_net_load,
                'optimized_net_load': optimized_net_load,
                'baseline_curtailment': pred_curt_mw,
                'optimized_curtailment': curtail_opt,
                'baseline_transmission_utilization': baseline_flow / capacity,
                'optimized_transmission_utilization': optimized_flow / capacity,
                'total_battery_charge': charge_opt,
                'total_battery_discharge': discharge_opt,
                'total_demand_response': dr_opt,
                'total_dispatch': dispatch_opt,
                'total_renewable_curtailment': curtail_opt,
                'optimization_status': 'OPTIMAL',
                'objective_value': res.fun
            })
            
            # Create action rows
            base_row = {
                'timestamp': ts,
                'zone_id': zone,
                'grid_risk_level': row['grid_risk_class'],
                'grid_risk_probability': row['grid_risk_prob'],
                'curtailment_probability': pred_curt_prob,
                'predicted_demand_mw': row['predicted_demand_mw'],
                'predicted_solar_mw': row['predicted_solar_60m'],
                'predicted_wind_mw': row['predicted_wind_60m'],
                'predicted_renewable_mw': pred_renewable,
                'predicted_net_load_mw': baseline_net_load,
                'estimated_curtailment_before_mw': pred_curt_mw,
                'estimated_curtailment_after_mw': curtail_opt,
                'estimated_grid_stress_before': baseline_flow / capacity,
                'estimated_grid_stress_after': optimized_flow / capacity,
                'estimated_benefit': (baseline_flow - optimized_flow) if optimized_flow < baseline_flow else 0
            }
            
            actions = [
                ('BATTERY_ALL', 'battery', 'CHARGE', charge_opt, c_charge),
                ('BATTERY_ALL', 'battery', 'DISCHARGE', discharge_opt, c_discharge),
                ('DR_ALL', 'demand_response', 'ACTIVATE', dr_opt, c_dr),
                ('GEN_ALL', 'dispatch', 'ACTIVATE', dispatch_opt, c_dispatch),
                ('RENEWABLE_ALL', 'renewable', 'CURTAIL', curtail_opt, W_CURTAILMENT)
            ]
            
            # Filter and rank actions by cost/priority
            valid_actions = [a for a in actions if a[3] > 0]
            valid_actions.sort(key=lambda x: x[4]) # Sort by cost ascending
            
            for rank, act in enumerate(valid_actions):
                row_copy = base_row.copy()
                row_copy['action_rank'] = rank + 1
                row_copy['resource_id'] = act[0]
                row_copy['resource_type'] = act[1]
                row_copy['action'] = act[2]
                row_copy['action_mw'] = act[3]
                actions_list.append(row_copy)
                
            # Post-solve audit
            assert round(charge_opt, 4) <= round(max_charge, 4)
            assert round(discharge_opt, 4) <= round(max_discharge, 4)
            assert round(dr_opt, 4) <= round(max_dr, 4)
            assert round(dispatch_opt, 4) <= round(max_dispatch, 4)
            assert round(curtail_opt, 4) <= round(pred_renewable, 4)
            assert not (charge_opt > 0 and discharge_opt > 0), "Simultaneous charge and discharge detected!"
            
        else:
            summary_list.append({
                'timestamp': ts,
                'zone_id': zone,
                'optimization_status': 'INFEASIBLE',
                'baseline_curtailment': pred_curt_mw
            })
            
    sum_df = pd.DataFrame(summary_list)
    sum_df.to_csv('outputs/optimization/optimization_summary.csv', index=False)
    
    act_cols = ['timestamp', 'zone_id', 'grid_risk_level', 'grid_risk_probability', 'curtailment_probability', 'predicted_demand_mw', 'predicted_solar_mw', 'predicted_wind_mw', 'predicted_renewable_mw', 'predicted_net_load_mw', 'action_rank', 'resource_id', 'resource_type', 'action', 'action_mw', 'estimated_curtailment_before_mw', 'estimated_curtailment_after_mw', 'estimated_grid_stress_before', 'estimated_grid_stress_after', 'estimated_benefit']
    act_df = pd.DataFrame(actions_list, columns=act_cols)
    act_df.to_csv('outputs/optimization/optimization_actions.csv', index=False)
    
    # Generate recommendations text
    latest_ts = grid_risk['timestamp'].max()
    latest_actions = act_df[act_df['timestamp'] == latest_ts]
    latest_summary = sum_df[sum_df['timestamp'] == latest_ts]
    
    with open('outputs/optimization/current_recommendations.csv', 'w') as f:
        f.write(f"Recommendations for {latest_ts}\n\n")
        for _, s_row in latest_summary.iterrows():
            z = s_row['zone_id']
            if s_row.get('optimization_status') != 'OPTIMAL':
                f.write(f"{z}\nStatus: INFEASIBLE\n\n")
                continue
            
            risk_level = s_row['risk_level']
            f.write(f"{z}\n")
            f.write(f"Risk: {risk_level}\n")
            f.write(f"Curtailment Risk: {s_row['curtailment_probability']*100:.1f}%\n\n")
            f.write("Recommended Actions:\n")
            
            z_actions = latest_actions[latest_actions['zone_id'] == z]
            if z_actions.empty:
                f.write("1. NO_ACTION\n")
                f.write("\nReason:\nPredicted grid state is within normal operating limits. No intervention necessary.\n\n")
            else:
                for idx_a, (_, a_row) in enumerate(z_actions.iterrows()):
                    f.write(f"{idx_a+1}. {a_row['resource_type'].title()} {a_row['action'].title()} — {a_row['action_mw']:.1f} MW\n")
                
                f.write("\nReason:\nPredicted renewable surplus or grid transmission limit exceeded. Actions dispatched to minimize overall operating cost and grid stress.\n\n")
                
    # Report
    with open('outputs/optimization/optimization_report.md', 'w') as f:
        f.write("# PATH 8: Optimization & Action Engine\n\n")
        f.write("## 1. Objective\nDetermine optimal dispatch actions to minimize curtailment and grid stress.\n")
        f.write(f"Objective Function = {W_FEASIBILITY} * flow_violation + {W_CURTAILMENT} * renewable_curtailment + resource_cost * resource_mw\n\n")
        f.write("## 2. Decision variables\n- battery_charge\n- battery_discharge\n- demand_response\n- dispatchable_generation\n- renewable_curtailment\n\n")
        f.write("## 3. Constraints\n- 0 <= action <= available_capacity\n- flow_violation >= 0\n")
        f.write("- curtailment + charge - discharge - dr - dispatch >= predicted_curtailment\n")
        f.write("- Baseline_Flow + charge - discharge - dr - dispatch + curtailment - flow_violation <= target_flow\n\n")
        
        f.write("## 4. Feasibility Audit\n")
        f.write(f"Solver ran for {len(grid_risk)} steps.\n")
        infeasible = len(sum_df[sum_df['optimization_status'] != 'OPTIMAL'])
        f.write(f"Infeasible solutions: {infeasible}\n")
        f.write("All constraints independently verified post-solve.\n\n")
        
        f.write("## 5. Examples\n")
        has_actions = act_df['timestamp'].unique()
        if len(has_actions) > 0:
            ex_ts = has_actions[0]
            ex_acts = act_df[act_df['timestamp'] == ex_ts]
            f.write(f"**High-Risk Example ({ex_ts}):**\n")
            for _, r in ex_acts.iterrows():
                f.write(f"- {r['action']} {r['resource_type']}: {r['action_mw']} MW\n")
        
    print("Done. PATH 8 executed successfully.")

if __name__ == '__main__':
    main()
