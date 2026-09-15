# PATH 8: Optimization & Action Engine

## 1. Objective
Determine optimal dispatch actions to minimize curtailment and grid stress.
Objective Function = 1000000 * flow_violation + 10000 * renewable_curtailment + resource_cost * resource_mw

## 2. Decision variables
- battery_charge
- battery_discharge
- demand_response
- dispatchable_generation
- renewable_curtailment

## 3. Constraints
- 0 <= action <= available_capacity
- flow_violation >= 0
- curtailment + charge - discharge - dr - dispatch >= predicted_curtailment
- Baseline_Flow + charge - discharge - dr - dispatch + curtailment - flow_violation <= target_flow

## 4. Feasibility Audit
Solver ran for 5552 steps.
Infeasible solutions: 0
All constraints independently verified post-solve.

## 5. Examples
**High-Risk Example (2026-01-02 00:15:00):**
- CHARGE battery: 300.0 MW
- CURTAIL renewable: 38.51675637743597 MW
