"""DynamoDB access for the demo's forecast cache (real table, synthetic data).

Mirrors the production forecast-lambda table schema:
  PK  tenant_id                       (S)
  SK  metric_name#forecast_date       (S)   e.g. "CSAT#2026-07-16"
  attrs: forecast_date, forecast_generated_at, forecast_value, metric_name,
         model_used, readiness_status, ttl (TTL, epoch seconds)
`forecast_value` is stored as a Decimal string. Credentials come from the
environment / instance IAM role.
"""
from __future__ import annotations

import os
from datetime import date
from decimal import Decimal

# Demo tenants (synthetic).
TENANTS = [
    "11eee7a2-a715-4010-9f7b-0242ac110003",
    "11eee7a1-52e0-5ad0-97d1-0242ac110004",
]

SK = "metric_name#forecast_date"


def _table():
    import boto3

    name = os.environ["DDB_TABLE"]
    region = os.environ.get("AWS_REGION", "us-east-1")
    return boto3.resource("dynamodb", region_name=region).Table(name)


def read_forecasts(tenant_id: str) -> dict[str, list[tuple[date, float]]]:
    """Return {metric_name: [(forecast_date, forecast_value), ...]} for a tenant."""
    from boto3.dynamodb.conditions import Key

    resp = _table().query(KeyConditionExpression=Key("tenant_id").eq(tenant_id))
    out: dict[str, list[tuple[date, float]]] = {}
    for item in resp.get("Items", []):
        metric = item.get("metric_name")
        try:
            d = date.fromisoformat(item["forecast_date"])
            v = float(item["forecast_value"])
        except (KeyError, ValueError):
            continue
        out.setdefault(metric, []).append((d, v))
    for metric in out:
        out[metric].sort()
    return out


def write_forecasts(
    tenant_id: str,
    metric_name: str,
    points: list[tuple[date, float]],
    generated_at: str,
    ttl_epoch: int,
    model_used: str = "holt_winters",
    readiness_status: str = "ok",
) -> None:
    table = _table()
    with table.batch_writer() as bw:
        for d, v in points:
            bw.put_item(
                Item={
                    "tenant_id": tenant_id,
                    SK: f"{metric_name}#{d.isoformat()}",
                    "forecast_date": d.isoformat(),
                    "forecast_generated_at": generated_at,
                    "forecast_value": Decimal(str(round(float(v), 3))),
                    "metric_name": metric_name,
                    "model_used": model_used,
                    "readiness_status": readiness_status,
                    "ttl": ttl_epoch,
                }
            )
