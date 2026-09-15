# Architecture

GridPulse is composed of a decoupled backend data processing pipeline and a reactive frontend presentation layer.

## 1. Data Pipeline (`src/pipeline.py`)

The backend pipeline simulates a data ingestion and inference loop, executing in the following order:
1. **Demand Forecasting**: Predicts future load spikes using historical load data.
2. **Renewable Forecasting**: Predicts solar and wind generation based on weather conditions.
3. **Anomaly Detection**: Compares expected renewable generation against actual performance to detect underperforming assets.
4. **Root Cause Analysis**: Classifies the specific mechanical or environmental cause of detected anomalies.
5. **Grid Risk Simulation**: Combines demand and generation forecasts to predict transmission line utilization and curtailment risks.
6. **Action Optimization**: Formulates an action plan to balance the grid and minimize curtailment.
7. **Counterfactual Validation**: Simulates the proposed action to verify it does not trigger a secondary constraint violation (e.g. overloading a transmission line).

The pipeline writes its results to structured CSV files in the `outputs/` directory, establishing a clean boundary between data processing and visualization.

## 2. Presentation Layer (`src/app.py`)

The frontend is built using **Streamlit** and **Plotly**. It reads the current state from the `outputs/` directory and renders a premium, interactive "Command Center". 

The UI is entirely bespoke, utilizing custom injected CSS to override default Streamlit styling and achieve a clean, corporate dashboard aesthetic with custom HTML components (like the Grid Flow and Status Indicator cards).
