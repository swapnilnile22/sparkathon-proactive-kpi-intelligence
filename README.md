# Proactive KPI Intelligence — Sparkathon Prototype

An agentic AI system that **forecasts contact-center KPI anomalies up to 7 days ahead**
and **autonomously investigates their root cause** — moving operations managers from
reactive firefighting to proactive intervention.

## What it shows

1. A 7-day **forecast board** of contact-center KPIs (CSAT, Handle Time, Volume,
   First-Contact Resolution).
2. An **early warning**: CSAT is forecast to breach its target ~3 days ahead, flagged
   red while the others stay green.
3. A **real agentic investigation** (Amazon Bedrock / Claude) streamed layer by layer —
   historical context, correlated signals, probable cause, projected financial impact,
   normalization forecast, and prioritised **pre-emptive** actions. Click any point on the
   forecast line (or the card button) to launch it.

All data in this prototype is **synthetic** — no real customer, tenant, or user data.

## How it works

- **Data store** — a real **DynamoDB forecast cache** (`dev-sparkathon-sem-rca-forecast`) that
  mirrors the production `forecast-lambda` schema: PK `tenant_id`, SK `metric_name#forecast_date`,
  plus `forecast_value`, `model_used`, `readiness_status`, `forecast_generated_at`, and a `ttl`.
  `seed_ddb.py` populates 7-day synthetic forecasts for two demo tenants; the app reads forecasts
  per tenant (`ddb_store.read_forecasts`). Falls back to computing forecasts locally when DDB
  isn't configured (e.g. local runs).
- **Forecasting** — 7-day forecasts computed with Holt-Winters (`statsmodels`) on that history
  (`forecast_data.py`).
- **Early warning** — each forecast day is compared to the KPI target; a breach raises a
  predicted anomaly (`early_warning.py`).
- **Investigation** — a real **Bedrock Converse** call produces the 7-layer brief
  (`bedrock_client.py` + `investigation.py`); a hand-written brief is used automatically as a
  fallback if Bedrock access isn't available.

## Deployment (Sparkathon AWS account)

Hosted on a single **EC2 instance in us-east-1**, private (no public IP), reachable over
**FortiClient VPN** at the instance's private IP. Bedrock access is via the instance IAM
role. Step-by-step CLI: see **[DEPLOY_AWS.md](DEPLOY_AWS.md)**.

Live app (on Sparkathon VPN): `http://<PRIVATE_IP>:8501`

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open http://localhost:8501. Without AWS credentials the investigation uses the
synthetic fallback; with credentials + `AWS_REGION`/`BEDROCK_MODEL_ID` set it calls Bedrock.

## Configuration

| Env var | Default | Purpose |
|---|---|---|
| `AWS_REGION` | `us-east-1` | Bedrock + DynamoDB region |
| `BEDROCK_MODEL_ID` | `anthropic.claude-3-haiku-20240307-v1:0` | Claude model — direct us-east-1 on-demand (cross-region `us.` profiles are blocked by the account's region lock) |
| `DDB_TABLE` | *(unset → in-memory synthetic)* | DynamoDB table name for KPI actuals/forecasts |

## Tests

```bash
python -m pytest -v
```
