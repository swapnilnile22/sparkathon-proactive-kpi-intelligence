"""Thin wrapper around the Amazon Bedrock Converse API.

Uses the instance's IAM role for credentials (no static keys). The model ID is
configurable so the same code runs against whichever Claude model is enabled in
the Sparkathon account. `temperature` is intentionally omitted — newer models
(e.g. anthropic.claude-opus-4-8) reject it.
"""
from __future__ import annotations

import os

# Cross-region inference profile ID. Override via the BEDROCK_MODEL_ID env var
# (e.g. "anthropic.claude-opus-4-8" for higher quality). Whichever ID is used
# must have model access enabled in the account, in us-east-1.
DEFAULT_MODEL_ID = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"


def converse_text(prompt: str, max_tokens: int = 2000) -> str:
    """Send a single user prompt to Bedrock and return the model's text reply."""
    import boto3

    model_id = os.environ.get("BEDROCK_MODEL_ID", DEFAULT_MODEL_ID)
    region = os.environ.get("AWS_REGION", "us-east-1")

    client = boto3.client("bedrock-runtime", region_name=region)
    resp = client.converse(
        modelId=model_id,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": max_tokens},
    )
    return resp["output"]["message"]["content"][0]["text"]
