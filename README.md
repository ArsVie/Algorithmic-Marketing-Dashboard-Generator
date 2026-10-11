# Algorithmic Marketing Dashboard Generator

A marketing performance dashboard built with **Python Dash and Plotly**, driven by a synthetic multi-channel campaign dataset (Oct 2022 to Dec 2023).

Live demo: https://algorithmic-marketing-dashboard-generator.onrender.com/ (free hosting tier, so the first load can take a while to wake up).

![Dashboard screenshot](Captura_DashBoard.png)

## What it does

`app.py` loads `dummy_data.csv` (4,113 daily rows across Programmatic, Paid Search, Paid Social and Organic channels) and renders a single-page dashboard:

* **KPI cards with sparklines:** spend, impressions, clicks, conversions and derived ratios (CPM, CTR, CPC, conversion rate), each with a small daily trend chart.
* **Date range filtering:** `DatePickerRange` inputs drive Pandas callbacks that recompute every card, chart and table.
* **Daily or monthly aggregation:** a toggle that re-buckets the time series chart.
* **Heatmap-style tables:** conditional formatting in `dash_table` that shades cells by value (five-step colour scale built in `generate_heatmap_styles`).
* **Custom layout:** hand-written CSS (flexbox and grid), a collapsible sidebar, no drag-and-drop BI tool.
* **Deployable:** exposes `server = app.server`, so it runs under Gunicorn (this is how the live demo is hosted).

## About the data

The dataset was generated offline to look like a real campaign log, with spend shocks, seasonal regimes and smoothed carryover in mind (a jump diffusion style process). **The generator script is not part of this repository**, only its output CSV is. If neither CSV is present, `app.py` falls back to a simple uniform random generator so the app still starts.

## Tech stack

Python 3.9+, Pandas, NumPy, Dash, Plotly, Gunicorn.

## Run locally

```bash
git clone https://github.com/ArsVie/Algorithmic-Marketing-Dashboard-Generator
cd Algorithmic-Marketing-Dashboard-Generator
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Then open http://127.0.0.1:8050.

To serve it the way the demo does: `gunicorn app:server`.

## Limitations

* The data is synthetic, and the code that produced it is not included, so the simulation itself cannot be reproduced from this repo.
* Some rows are not internally consistent as real marketing data would be (for example very low impression counts next to large spend values), so the dashboard is a UI and analytics demo, not a source of marketing insight.
* Single-file app with no automated tests.
