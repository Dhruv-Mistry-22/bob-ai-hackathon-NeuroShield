# Setup Guide

## Requirements
- Python 3.9+

## Installation
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application
GridPulse is split into a data pipeline and a UI dashboard.

**1. Run the Data Pipeline**
Execute the pipeline to generate the necessary data outputs:
```bash
python src/run_pipeline.py
```

**2. Start the UI Dashboard**
Launch the Streamlit interface:
```bash
streamlit run src/app.py
```
Then open `http://localhost:8501` in your browser.
