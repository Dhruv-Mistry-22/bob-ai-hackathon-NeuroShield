# NeuroShield — GridPulse AI Frontend

> **Interactive operator dashboard for grid load optimisation and renewable performance monitoring**

---

## Overview

This branch contains the **frontend layer** for GridPulse AI — a human-in-the-loop Streamlit dashboard that surfaces ML predictions, asset health alerts, optimisation recommendations, and counterfactual simulation results to grid operators.

The frontend is intentionally separated from the backend pipeline so that UI changes can be iterated independently without touching the ML/data engineering branches.

---

## Branch Purpose

| Branch | Responsibility |
|--------|---------------|
| `main` | Project root, README, and final integration |
| `frontend` *(this branch)* | Streamlit dashboard UI, CSS theming, layout components |
| `dashboard_ui` | Original dashboard scaffold (upstream reference) |

---

## Stack

| Layer | Technology |
|-------|-----------|
| UI Framework | Streamlit |
| Charts | Plotly |
| Data | Pandas / NumPy |
| Styling | Custom CSS (control-room dark theme) |

---

## Folder Structure

```
├── app.py                  # Main Streamlit dashboard entry point
├── components/
│   ├── kpi_cards.py        # Reusable KPI card components
│   ├── alert_banners.py    # Safety flag banners (GREEN/YELLOW/RED)
│   └── charts.py           # Plotly chart helpers
├── theme/
│   └── styles.css          # Custom CSS variables and overrides
├── requirements.txt        # Frontend-specific Python dependencies
└── README.md               # This file
```

---

## How to Run

```bash
# Install dependencies
pip install -r requirements.txt

# Launch dashboard (ensure pipeline outputs are present in outputs/)
streamlit run app.py
```

---

## Author

Kakkad Priyansh — frontend branch
