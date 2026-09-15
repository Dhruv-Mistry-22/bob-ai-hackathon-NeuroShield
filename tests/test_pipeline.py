import pandas as pd
import numpy as np
import pytest
import os
import dateutil.parser
from datetime import timedelta

def test_path_outputs_exist():
    assert os.path.exists('outputs/demand_model/demand_predictions.csv')
    assert os.path.exists('outputs/renewable_model/renewable_predictions.csv')
    assert os.path.exists('outputs/anomaly_model/current_asset_status.csv')
    assert os.path.exists('outputs/root_cause/root_cause_predictions.csv')
    assert os.path.exists('outputs/grid_risk/grid_risk_predictions.csv')
    assert os.path.exists('outputs/optimization/optimization_actions.csv')
    assert os.path.exists('outputs/simulation/baseline_vs_optimized.csv')
    assert os.path.exists('outputs/operator_brief/current_operator_context.json')
    assert os.path.exists('outputs/operator_brief/current_operator_brief.md')

def test_cross_path_numerical_consistency():
    import json
    with open('outputs/operator_brief/current_operator_context.json') as f:
        ctx = json.load(f)
        
    ts = ctx['metadata']['decision_time']
    zone = ctx['metadata']['zone']
    
    # Check Demand (PATH 3)
    dem = pd.read_csv('outputs/demand_model/demand_predictions.csv')
    dem_val = dem[(dem['timestamp'] == ts) & (dem['zone_id'] == zone)].iloc[0]['predicted_demand_mw']
    assert abs(ctx['demand_forecast']['predicted_demand_60m'] - dem_val) < 1e-4
    
    # Check Renewable (PATH 4)
    ren = pd.read_csv('outputs/renewable_model/renewable_predictions.csv')
    ren_val = ren[(ren['timestamp'] == ts) & (ren['zone_id'] == zone)].iloc[0]['predicted_total_renewable_60m']
    assert abs(ctx['renewable_forecast']['renewable_60m'] - ren_val) < 1e-4
    
    # Check Optimization (PATH 8)
    opt = pd.read_csv('outputs/optimization/optimization_actions.csv')
    opt_val = opt[(opt['timestamp'] == ts) & (opt['zone_id'] == zone)].iloc[0]['action_mw']
    assert abs(ctx['optimization']['action_mw'] - opt_val) < 1e-4

def test_temporal_alignment():
    with open('outputs/operator_brief/current_operator_context.json') as f:
        import json
        ctx = json.load(f)
    dt_decision = dateutil.parser.parse(ctx['metadata']['decision_time'])
    dt_target = dateutil.parser.parse(ctx['metadata']['forecast_target_time'])
    assert (dt_target - dt_decision) == timedelta(minutes=60)

def test_optimization_bounds():
    opt = pd.read_csv('outputs/optimization/optimization_actions.csv')
    # Simple check, verify actions are non-negative
    assert opt['action_mw'].max() <= 1500 # Sanity check for largest resource in dataset
    assert opt['action_mw'].min() >= 0

def test_simulation_integrity():
    sim = pd.read_csv('outputs/simulation/baseline_vs_optimized.csv')
    assert len(sim.drop_duplicates(subset=['target_timestamp', 'zone_id'])) == len(sim)
    
    # Verify adverse counterfactual exists
    adverse = sim[(sim['optimized_overload_intervals'] > sim['baseline_overload_intervals']) | (sim['optimized_curtailment_mw'] > sim['baseline_curtailment_mw'])]
    assert not adverse.empty, "Adverse counterfactual was not preserved"
    
    # Verify MWh reconciliation (approx)
    base_mwh = sim['baseline_curtailment_mw'].sum() * 0.25
    opt_mwh = sim['optimized_curtailment_mw'].sum() * 0.25
    assert base_mwh > 0
    assert opt_mwh > base_mwh # 7000 vs 100000 approx
