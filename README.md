# 🚀 GridPulse AI
> **Network-aware grid load optimisation and renewable performance advisor**

---

## 👥 Team

| Field | Value |
|---|---|
| **Team Name** | Antigravity |
| **Track** | AI / Sustainability |
| **Team Lead** | Dhruv Mistry |
| **Members** | Dhruv Mistry |

---

## 🎯 Problem Statement
Renewable generation is highly variable, demand fluctuates throughout the day, and grid operators need to anticipate transmission stress before it becomes operationally difficult. Traditional systems react to the current state; we need a system that looks ahead to prevent curtailment and overloads. 

---

## 💡 Solution
GridPulse AI forecasts grid and renewable conditions, detects asset problems, recommends constrained actions, simulates their consequences, and gives operators an explainable safety-aware decision brief. By utilizing a 60-minute prediction horizon, GridPulse predicts the next grid state rather than only describing the current state.

---

## ✨ Key Features
- **Predict**: XGBoost Regressors (Demand) and Gradient Boosted Trees (Renewable) forecast the 60m horizon.
- **Detect & Explain**: Isolation Forests detect degraded asset states and a diagnostic telemetry engine bounds root causes.
- **Optimize**: Linear programming optimizations bound actions against strict physical constraints.
- **Simulate**: Counterfactual simulations identify conditions under which the current optimization policy can increase curtailment and create overload risk.
- **Alert**: An Operator Brief generates deterministic risk flags (GREEN, YELLOW, RED) based on physical simulation outcomes.
- **Human Decision**: A Streamlit Dashboard acts as a human-in-the-loop validation layer. The AI does not autonomously control the grid.

---

## 🛠️ Tech Stack

| Category | Technologies |
|---|---|
| **Languages** | Python |
| **Frameworks** | Streamlit, Pandas, NumPy |
| **Machine Learning** | Scikit-Learn, XGBoost, SciPy |
| **Data Visualization** | Plotly |

---

## 📁 Repository Structure

```
├── data/                 # Raw grid telemetry and weather data
├── src/                  # End-to-end data pipeline source code
├── tests/                # Data integrity and cross-path consistency test suites
├── outputs/              # Safely deterministically versioned ML model outputs
│   ├── final_validation/ # Final integration reports and demo scripts
├── app.py                # Main Streamlit Dashboard entry point
├── run_pipeline.py       # Sequential execution runner
└── requirements.txt      # Python dependencies
```

---

## ⚡ How to Run

```bash
# 1. Install dependencies
python -m pip install -r requirements.txt

# 2. Run the end-to-end pipeline (Executes PATH 2 through PATH 10)
python run_pipeline.py

# 3. Launch the human-in-the-loop dashboard
python -m streamlit run app.py
```

---

## 🖥️ Demo

| Artifact | Link |
|---|---|
| 📜 Demo Script | [outputs/final_validation/demo_script.md](outputs/final_validation/demo_script.md) |
| 📊 Final Metrics | [outputs/final_validation/final_metrics.json](outputs/final_validation/final_metrics.json) |

---

## ⚠️ Known Limitations

- **Battery**: Continuous battery SoC feasibility cannot be verified because `energy_capacity_mwh` is unavailable.
- **Forecasting**: Forecasts provide predictive guidance and are subject to error.
- **Wind MAPE**: Wind MAPE is unstable because wind generation can approach zero; MAE/RMSE are more operationally meaningful.
- **Root Cause**: Root-cause analysis is evidence-based and not a fully supervised classifier because only a small number of labeled events are available.
- **Simulation**: Baseline-vs-optimized results are counterfactual simulation estimates, not verified historical operational savings.
- **Control**: GridPulse AI does not automatically execute grid-control commands.

---

## 🏅 What We're Most Proud Of
Our counterfactual simulation layer. By discovering that optimizations can occasionally induce *worse* outcomes (due to inevitable forecast errors), we built a system that surfaces **Adverse Counterfactuals** and flags them RED for human review. GridPulse AI embraces the reality of ML error rather than hiding it behind an autonomous optimizer.
