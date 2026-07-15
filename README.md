# Proactive KPI Intelligence — Sparkathon Prototype

An agentic AI system that **forecasts contact-center KPI anomalies up to 7 days ahead**
and **autonomously investigates their root cause** — moving operations managers from
reactive firefighting to proactive intervention.

## What it shows

1. A **KPI health board** of contact-center KPIs (CSAT, Handle Time, Volume,
   First-Contact Resolution) — current value, target, and the 7-day forecast trend.
2. An **early warning**: CSAT is forecast to breach its target ~3 days ahead, flagged
   red while the others stay green.
3. A **real agentic investigation** (Amazon Bedrock / Claude) streamed layer by layer —
   historical context, correlated signals, probable cause, projected financial impact,
   normalization forecast, and prioritised **pre-emptive** actions. Click any point on a
   forecast line to launch it.

## How it works

- **Data store** — a **DynamoDB** table (`dev-sparkathon-sem-rca-forecast`) mirroring the
  production `forecast-lambda` schema: PK `tenant_id`, SK `metric_name#forecast_date`, plus
  `forecast_value`, `model_used`, `readiness_status`, `forecast_generated_at`, and a `ttl`.
  `seed_ddb.py` populates the 7-day forecasts per tenant; the app reads them per tenant
  (`ddb_store.read_forecasts`) and falls back to computing them locally when DDB isn't
  configured.
- **Forecasting** — 7-day forecasts computed with Holt-Winters (`statsmodels`)
  (`forecast_data.py`).
- **Early warning** — each forecast day is compared to the KPI target; a breach raises a
  predicted anomaly (`early_warning.py`).
- **Investigation** — a real **Bedrock Converse** call produces the layered brief
  (`bedrock_client.py` + `investigation.py`); a built-in brief is used automatically if
  Bedrock isn't available.

## Deployment (Sparkathon AWS account)

Hosted on a single **EC2 instance in us-east-1**, private (no public IP), reachable over
**FortiClient VPN** at the instance's private IP. Bedrock and DynamoDB access is via the
instance IAM role. Step-by-step CLI: see **[DEPLOY_AWS.md](DEPLOY_AWS.md)**.

Live app (on Sparkathon VPN): `http://<PRIVATE_IP>:8501`

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open http://localhost:8501. Without AWS credentials the investigation uses the built-in
brief; with credentials + `AWS_REGION`/`BEDROCK_MODEL_ID` set it calls Bedrock.

## Configuration

| Env var | Default | Purpose |
|---|---|---|
| `AWS_REGION` | `us-east-1` | Bedrock + DynamoDB region |
| `BEDROCK_MODEL_ID` | `anthropic.claude-3-haiku-20240307-v1:0` | Claude model — direct us-east-1 on-demand (cross-region `us.` profiles are blocked by the account's region lock) |
| `DDB_TABLE` | *(unset → computed locally)* | DynamoDB table name to read forecasts from |
| `PUBLIC_DEMO` | *(unset)* | Set to `1` for public hosting with no AWS (e.g. Streamlit Cloud): skips the Bedrock call and uses the built-in brief. Leave unset on the AWS host for live Bedrock. |

## Tests

```bash
python -m pytest -v
```
