# Proactive KPI Intelligence — Sparkathon Prototype

An agentic AI system that **forecasts contact-center KPI anomalies up to 7 days ahead**
and **autonomously investigates their root cause** — moving operations managers from
reactive firefighting to proactive intervention.

## Live demo

👉 **<LIVE_STREAMLIT_URL_HERE>** (open to all NiCE users, no login)

## What it shows

1. A 7-day **forecast board** of contact-center KPIs (CSAT, Handle Time, Volume,
   First-Contact Resolution).
2. An **early warning**: CSAT is forecast to breach its target ~3 days ahead, flagged
   red while the others stay green.
3. An **agentic investigation** streamed layer by layer — historical context, correlated
   signals, probable cause, projected financial impact, normalization forecast, and
   prioritised **pre-emptive** actions.

## How it works

- **Forecasting** — 7-day forecasts computed with Holt-Winters (`statsmodels`).
- **Early warning** — each forecast day is compared to the KPI target; a breach raises a
  predicted anomaly (`early_warning.py`).
- **Investigation** — a streaming, layered intelligence brief (`investigation.py`).

All data in this prototype is **synthetic** — no real customer, tenant, or user data.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open http://localhost:8501.

## Tests

```bash
python -m pytest -v
```
