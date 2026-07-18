"""
LLM client for FeederIQ agents via AWS Bedrock.
Each agent uses this to reason about results and generate human-readable outputs.

Setup:
  1. pip install boto3
  2. Configure AWS credentials: aws configure (or set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION)
  3. Ensure Bedrock model access is enabled in your AWS account

Models:
  - Default: amazon.nova-micro-v1:0 (available immediately, no form needed)
  - Preferred: anthropic.claude-3-sonnet-20240229-v1:0 (requires Anthropic use-case form)
  - Set BEDROCK_MODEL_ID env var to override

If Bedrock is unavailable, agents fall back to template-based outputs (no crash).
"""
import json
import os
import logging

logger = logging.getLogger(__name__)

# Default model - Claude 3.7 Sonnet via cross-region inference profile
BEDROCK_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "us.anthropic.claude-3-7-sonnet-20250219-v1:0")
BEDROCK_REGION = os.environ.get("AWS_DEFAULT_REGION", os.environ.get("AWS_REGION", "us-east-1"))


def get_bedrock_client():
    """Get Bedrock runtime client. Returns None if credentials unavailable."""
    try:
        import boto3
        from botocore.config import Config
        config = Config(
            connect_timeout=5,
            read_timeout=60,
            retries={"max_attempts": 1}
        )
        client = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION, config=config)
        return client
    except Exception as e:
        logger.warning(f"Bedrock client unavailable: {e}")
        return None


def invoke_llm(system_prompt: str, user_message: str, max_tokens: int = 1800) -> str:
    """
    Invoke Bedrock LLM with system prompt and user message.
    Uses Converse API (works with all Bedrock models).
    Returns the LLM response text, or empty string if unavailable.
    """
    client = get_bedrock_client()
    if client is None:
        return ""

    try:
        # Build system message
        system_messages = [{"text": system_prompt}] if system_prompt else []

        response = client.converse(
            modelId=BEDROCK_MODEL_ID,
            messages=[{"role": "user", "content": [{"text": user_message}]}],
            system=system_messages,
            inferenceConfig={"maxTokens": max_tokens, "temperature": 0.3},
        )

        return response["output"]["message"]["content"][0]["text"]

    except Exception as e:
        logger.warning(f"Bedrock invocation failed: {e}")
        return ""


def is_llm_available() -> bool:
    """Check if LLM is configured and accessible."""
    client = get_bedrock_client()
    if client is None:
        return False
    try:
        response = client.converse(
            modelId=BEDROCK_MODEL_ID,
            messages=[{"role": "user", "content": [{"text": "hi"}]}],
            inferenceConfig={"maxTokens": 5},
        )
        return True
    except Exception:
        return False
