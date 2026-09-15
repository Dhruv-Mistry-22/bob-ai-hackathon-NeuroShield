# PATH 9: Baseline vs Optimized Simulation

> **These are counterfactual simulation results, not verified historical operational savings.**

## 1. Physical Equations and Data Physics Validation
- **Transmission Flow**: The dataset empirically demonstrates `transmission_flow_mw = demand_mw - hydro_generation_mw`. Renewables are mathematically injected *after* this measurement (downstream of the bottleneck). Thus, renewable curtailment does **not** directly relieve transmission flow in this architecture.
- **Optimized Flow**: Because battery discharge and DR offset demand (and battery charging increases it), `optimized_flow = baseline_flow + battery_charge - battery_discharge - DR_activate - dispatch_generation`
- **Optimized Curtailment**: `max(0, baseline_curtailment - battery_charge + battery_discharge + DR_activate + dispatch_generation)`. Charging the battery absorbs renewable surplus. Activating DR or discharging battery injects power into an already oversupplied network, effectively *increasing* curtailment. 
- **Overload Definition**: Strict physical bounds: `overload_mw = max(0, transmission_flow_mw - transmission_capacity_mw)`.

## 2. Overall Results (All Timestamps)
- Historical baseline curtailment: 7068.5 MWh
- Simulated optimized curtailment: 100488.6 MWh
- Estimated curtailment avoided: -93420.0 MWh
- Estimated reduction: -1321.6%
- Baseline overload intervals: 0
- Optimized overload intervals: 23
- Additional renewable energy absorbed: -93420.0 MWh

## 3. High-Risk Timestamps (>85% Util)
- Estimated curtailment avoided: 102.4 MWh
- Curtailment reduction: 3.7%
- Overload intervals avoided: -23

## 4. Curtailment-Event Timestamps
- Total battery charging MWh: 1475.0
- Total battery discharging MWh: 0.0
- Total DR MWh: 0.0
- Total dispatch MWh: 0.0
- Total residual curtailment MWh: 2682.8

## 5. Limitations
- **Battery Energy Constraints**: While strict MW power injection constraints are verified, dynamic battery SOC energy constraints cannot be verified in this simulation because the dataset lacks energy_capacity_mwh.
