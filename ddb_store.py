"""DynamoDB access for the demo's KPI store (real table, synthetic data).

Table schema (single table): PK `metric` (S), SK `sk` (S).
- Actuals:   sk = "ACTUAL#<YYYY-MM-DD>"
- Forecasts: sk = "FORECAST#<YYYY-MM-DD>"
`value` is stored as a Decimal string to avoid float precision issues.
Credentials come from the environment / instance IAM role.
"""
from __future__ import annotations

import os
from datetime import date
from decimal import Decimal


def _table():
    import boto3

    name = os.environ["DDB_TABLE"]
    region = os.environ.get("AWS_REGION", "us-east-1")
    return boto3.resource("dynamodb", region_name=region).Table(name)


def read_actuals(metric_key: str, days: int = 14) -> list[tuple[date, float]]:
    from boto3.dynamodb.conditions import Key

    resp = _table().query(
        KeyConditionExpression=Key("metric").eq(metric_key)
        & Key("sk").begins_with("ACTUAL#"),
        ScanIndexForward=True,
    )
    rows = [
        (date.fromisoformat(item["sk"].split("#", 1)[1]), float(item["value"]))
        for item in resp.get("Items", [])
    ]
    return rows[-days:]


def write_forecast(metric_key: str, points: list[tuple[date, float]]) -> None:
    table = _table()
    with table.batch_writer() as bw:
        for d, v in points:
            bw.put_item(
                Item={
                    "metric": metric_key,
                    "sk": f"FORECAST#{d.isoformat()}",
                    "value": Decimal(str(round(float(v), 3))),
                }
            )
