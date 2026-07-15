"""Create (if needed) and seed the DynamoDB KPI table with SYNTHETIC actuals.

Idempotent — safe to run repeatedly (e.g. on every EC2 boot). Writes the same
deterministic synthetic history the app's fallback uses, so DDB-backed and
offline runs show identical numbers.

Env: DDB_TABLE (default dev-sparkathon-sem-rca-forecast), AWS_REGION (default us-east-1),
     OWNER (tag value; required by the Sparkathon account policy).
"""
from __future__ import annotations

import os
from decimal import Decimal

import config
import forecast_data as fd

TABLE = os.environ.get("DDB_TABLE", "dev-sparkathon-sem-rca-forecast")
REGION = os.environ.get("AWS_REGION", "us-east-1")
OWNER = os.environ.get("OWNER", "Sparkathon")


def ensure_table(client) -> None:
    try:
        client.describe_table(TableName=TABLE)
        return
    except client.exceptions.ResourceNotFoundException:
        pass
    client.create_table(
        TableName=TABLE,
        KeySchema=[
            {"AttributeName": "metric", "KeyType": "HASH"},
            {"AttributeName": "sk", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "metric", "AttributeType": "S"},
            {"AttributeName": "sk", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
        Tags=[{"Key": "Owner", "Value": OWNER}],
    )
    client.get_waiter("table_exists").wait(TableName=TABLE)


def seed() -> None:
    import boto3

    client = boto3.client("dynamodb", region_name=REGION)
    ensure_table(client)

    table = boto3.resource("dynamodb", region_name=REGION).Table(TABLE)
    count = 0
    with table.batch_writer() as bw:
        for m in config.METRICS:
            for d, v in fd._synthetic_history(m.key, days=14):
                bw.put_item(
                    Item={
                        "metric": m.key,
                        "sk": f"ACTUAL#{d.isoformat()}",
                        "value": Decimal(str(v)),
                    }
                )
                count += 1
    print(f"Seeded {count} actual rows into '{TABLE}' ({REGION}).")


if __name__ == "__main__":
    seed()
