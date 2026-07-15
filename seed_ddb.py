"""Create (with the production forecast schema) and seed the DynamoDB forecast
table with SYNTHETIC forecasts for the demo tenants.

Schema: PK tenant_id, SK "metric_name#forecast_date", + forecast attributes and
a TTL. If a table with a different key schema already exists under the same name,
it is deleted and recreated. Idempotent enough to run on every EC2 boot.

Env: DDB_TABLE (default dev-sparkathon-sem-rca-forecast), AWS_REGION (us-east-1),
     OWNER (tag value; required by the Sparkathon account policy).
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import config
import ddb_store
import forecast_data as fd

TABLE = os.environ.get("DDB_TABLE", "dev-sparkathon-sem-rca-forecast")
REGION = os.environ.get("AWS_REGION", "us-east-1")
OWNER = os.environ.get("OWNER", "Sparkathon")

# Mirror the real model selection loosely (Prophet-style for demand/CSAT metrics).
_PROPHET = {"CSAT", "VOLUME"}


def _needs_recreate(client) -> bool | None:
    """None = create fresh; True = wrong schema, delete first; False = reuse."""
    try:
        desc = client.describe_table(TableName=TABLE)["Table"]
    except client.exceptions.ResourceNotFoundException:
        return None
    hash_key = next(
        (k["AttributeName"] for k in desc["KeySchema"] if k["KeyType"] == "HASH"), None
    )
    return hash_key != "tenant_id"


def ensure_table(client) -> None:
    state = _needs_recreate(client)
    if state is False:
        return
    if state is True:
        client.delete_table(TableName=TABLE)
        client.get_waiter("table_not_exists").wait(TableName=TABLE)

    client.create_table(
        TableName=TABLE,
        KeySchema=[
            {"AttributeName": "tenant_id", "KeyType": "HASH"},
            {"AttributeName": ddb_store.SK, "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "tenant_id", "AttributeType": "S"},
            {"AttributeName": ddb_store.SK, "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
        Tags=[{"Key": "Owner", "Value": OWNER}],
    )
    client.get_waiter("table_exists").wait(TableName=TABLE)
    try:
        client.update_time_to_live(
            TableName=TABLE,
            TimeToLiveSpecification={"Enabled": True, "AttributeName": "ttl"},
        )
    except Exception:
        pass  # already enabled / not critical


def seed() -> None:
    import boto3

    client = boto3.client("dynamodb", region_name=REGION)
    ensure_table(client)

    now = datetime.now(timezone.utc)
    generated_at = now.isoformat()
    ttl_epoch = int((now + timedelta(days=7)).timestamp())  # survive the judging window

    count = 0
    for tenant in ddb_store.TENANTS:
        for m in config.METRICS:
            points = fd.forecast(m.key, horizon=7)
            ddb_store.write_forecasts(
                tenant_id=tenant,
                metric_name=m.key,
                points=points,
                generated_at=generated_at,
                ttl_epoch=ttl_epoch,
                model_used="prophet" if m.key in _PROPHET else "holt_winters",
                readiness_status="ok",
            )
            count += len(points)
    print(
        f"Seeded {count} forecast rows for {len(ddb_store.TENANTS)} tenants "
        f"into '{TABLE}' ({REGION})."
    )


if __name__ == "__main__":
    seed()
