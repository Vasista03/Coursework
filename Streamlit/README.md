# Sales Performance Dashboard (Streamlit)

This project ships with a fully working Streamlit data app that lets you explore a demo
sales dataset, slice it with sidebar filters, and review visual insights.

## Prerequisites
- Python 3.9 or newer
- pip

## Create a virtual environment
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

On macOS or Linux:
```bash
python -m venv .venv
source .venv/bin/activate
```

## Install dependencies
```bash
pip install -r requirements.txt
```

## Run the development server
```bash
streamlit run app.py
```

Streamlit will open a browser tab at http://localhost:8501 with the dashboard.

## What you get
- A sidebar with multi-select filters for region, category, and segment plus a date range.
- KPI tiles that summarise total sales, profit, average margin, and order value.
- Plotly charts for daily sales, sales by category, and profit contribution by segment.
- A searchable data table and a download button for the filtered results.

## Data source
Sample sales transactions live in `data/sales_sample.csv`. Replace it with your own data or
hook up a database/REST API as needed.

## Configuration
- Theme settings live in `.streamlit/config.toml`.
- Add secrets to `.streamlit/secrets.toml` (create the file when needed and never commit secrets).

## Next steps
- Swap in real data and extend the visualisations.
- Add authentication, scheduling, or notifications if you deploy the app.
- Consider writing regression tests for business logic or data transforms.
