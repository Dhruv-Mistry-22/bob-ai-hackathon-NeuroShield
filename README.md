# 🚀 GridPulse AI

> **Network-aware grid load optimisation and renewable performance advisor**

---

## 👥 Team

| Field         | Value                                    |
| ------------- | ---------------------------------------- |
| **Team Name** | NeuroShield                              |
| **Track**     | AI / Sustainability                      |
| **Team Lead** | DhruvKumar Mistry                        |
| **Members**   | Meet Patel, Kakkad Priyansh, Harsh Verma |

---

## 🎯 Problem Statement

> Renewable generation is highly variable, demand fluctuates throughout the day, and grid operators need to anticipate transmission stress before it becomes operationally difficult.

Grid operators face the challenge of balancing fluctuating electricity demand with variable renewable generation while preventing transmission stress, overload risk, and unnecessary renewable curtailment. Traditional systems primarily react to the current grid state, making it difficult to anticipate upcoming demand spikes, renewable performance issues, and grid constraints in advance.

---

## 💡 Solution

> GridPulse AI forecasts future grid and renewable conditions, detects renewable asset anomalies, recommends constrained load-balancing actions, simulates their consequences, and provides an explainable safety-aware operator brief.

The system uses a 60-minute predictive horizon to estimate upcoming demand, renewable generation, and grid risk. It combines machine learning, anomaly detection, constrained optimization, counterfactual simulation, and a human-in-the-loop dashboard so that operators can evaluate recommended actions before making operational decisions.

---

## ✨ Key Features

* **Predict:** XGBoost and gradient-boosted models forecast demand and renewable generation up to 60 minutes ahead.
* **Detect:** Hybrid residual analysis and Isolation Forest anomaly detection identify underperforming solar and wind assets.
* **Explain:** Evidence-based root-cause diagnostics identify likely causes such as inverter failure, soiling, gearbox degradation, weather effects, or grid curtailment.
* **Optimize:** Linear programming generates load-balancing recommendations subject to available resource and grid constraints.
* **Simulate:** Counterfactual baseline-vs-optimized simulation evaluates the consequences of recommended actions, including adverse outcomes caused by forecast uncertainty.
* **Alert:** The Operator Brief produces deterministic GREEN, YELLOW, and RED safety flags based on predicted and simulated grid conditions.
* **Human Decision:** A Streamlit dashboard provides a human-in-the-loop validation layer. GridPulse AI does not autonomously execute grid-control commands.

---

## 🛠️ Tech Stack

| Category             | Technologies                                                   |
| -------------------- | -------------------------------------------------------------- |
| **Languages**        | Python                                                         |
| **Frameworks**       | Streamlit, Pandas, NumPy                                       |
| **IBM Technologies** | IBM Hackathon ecosystem; IBM BoB |
| **Databases**        | Not required — CSV-based telemetry and model outputs           |
| **Other**            | Scikit-Learn, XGBoost, SciPy, Plotly, pytest                   |

---

## 📁 Repository Structure

```text
├── data/                       # Grid telemetry, renewable assets, resources and weather
├── demo/                       # Demo video and dashboard screenshots
Video
├── docs/                       # Project documentation (setup, architecture, etc.)
├── outputs/                    # Deterministic model and analysis outputs
│   ├── demand_model/
│   ├── renewable_model/
│   ├── anomaly_model/
│   ├── root_cause/
│   ├── grid_risk/
│   ├── optimization/
│   ├── simulation/
│   └── operator_brief/
├── presentation/               # Pitch deck and presentation slides
├── scripts/                    # Utility scripts (data generation, manual entry)
├── src/                        # End-to-end modelling and decision pipeline
│   ├── app.py                  # Streamlit human-in-the-loop dashboard
│   ├── run_pipeline.py         # Sequential pipeline execution
│   ├── features.py             # PATH 2 — Feature engineering
│   ├── demand_forecast.py      # PATH 3 — Demand prediction
│   ├── renewable_forecast.py   # PATH 4 — Renewable forecasting
│   ├── asset_anomaly.py        # PATH 5 — Asset anomaly detection
│   ├── root_cause.py           # PATH 6 — Root-cause diagnostics
│   ├── grid_risk.py            # PATH 7 — Grid risk and curtailment prediction
│   ├── optimizer.py            # PATH 8 — Constrained optimization
│   ├── baseline_vs_optimized.py# PATH 9 — Counterfactual simulation
│   └── operator_brief.py       # PATH 10 — Operator decision brief
├── tests/                      # Data integrity and integration tests
├── requirements.txt            # Python dependencies
└── submission.yaml             # Hackathon submission metadata
```

---

## ⚡ How to Run

> **Copy these exact steps from your `docs/setup-guide.md` if that file is included in the final repository.**

```bash
# 1. Install dependencies
python -m pip install -r requirements.txt

# 2. Run the end-to-end pipeline
python src/run_pipeline.py

# 3. Launch the human-in-the-loop dashboard
python -m streamlit run src/app.py
```

---

## 🖥️ Demo

| Artifact        | Link                                            |
| --------------- | ----------------------------------------------- |
| 📹 Demo Video   | [Video.mp4](demo/Video.mp4)                     |
| 🖼️ Screenshots | [Grid Status](demo/screenshots/1_light_mode_overview.png) <br> [Asset Health](demo/screenshots/2_light_mode_asset_health.png) <br> [Action Validation](demo/screenshots/3_light_mode_validation.png) |
| 📊 Presentation | [GridPulse_AI.pptx](presentation/GridPulse_AI.pptx) |

---

## ⚠️ Known Limitations

> Be honest — judges appreciate transparency over overclaiming.

* **Battery:** Continuous battery state-of-charge feasibility cannot be verified because `energy_capacity_mwh` is unavailable in the provided dataset.
* **Forecasting:** Machine-learning forecasts provide predictive guidance and remain subject to forecast error.
* **Wind MAPE:** Wind MAPE becomes unstable when wind generation approaches zero; MAE and RMSE are more operationally meaningful.
* **Root Cause:** Root-cause analysis is evidence-based rather than a fully supervised classifier because only a small number of labelled events are available.
* **Simulation:** Baseline-vs-optimized results are counterfactual simulation estimates and should not be presented as verified historical operational savings.
* **Optimization Safety:** The counterfactual simulation identified cases where the optimization policy could produce worse outcomes under forecast error, including simulated overload and increased curtailment.
* **Control:** GridPulse AI does not automatically execute grid-control commands. Recommended actions require operator review and approval.
* **Synthetic Data:** The demonstrated results are based on the provided synthetic grid, renewable, weather, resource, and injected-event datasets and require validation against real operational data before deployment.

---

## 🏅 What We're Most Proud Of

Our strongest feature is the **counterfactual simulation and safety layer**.

Instead of assuming that an optimization recommendation is always beneficial, GridPulse AI tests the recommendation against a simulated future state. During validation, the system discovered **adverse counterfactuals** where forecast error could cause an apparently reasonable optimization action to produce worse outcomes.

The simulation identified **23 simulated physical-overload intervals** and a substantial increase in simulated curtailment under the optimized policy compared with the baseline. Rather than hiding these failures, GridPulse AI surfaces them as **RED safety conditions requiring operator approval**.

## This demonstrates an important principle for AI-assisted grid operations: **the system should expose uncertainty and failure modes rather than blindly automate decisions.**

## 🛡️ Human-in-the-Loop Safety

GridPulse AI is designed as a **decision-support system, not an autonomous grid controller**.

Machine-learning models provide forecasts and risk estimates, the optimization layer proposes constrained actions, and the counterfactual simulation evaluates their potential consequences. The final Operator Brief communicates the result through deterministic safety flags so that a human operator can review and approve or reject recommendations before any real-world action.
