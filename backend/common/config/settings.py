from __future__ import annotations

import json
from functools import lru_cache

import boto3
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime config. Local runs read `.env`; Lambda reads env vars plus one optional Secrets Manager JSON."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    appEnv: str = "dev"
    awsRegion: str = "ap-south-1"
    configSecretName: str = ""
    mainTableName: str = "up4ds-dev-main"
    dynamoEndpointUrl: str = ""
    corsOrigins: list[str] = ["http://localhost:5173"]
    appBaseUrl: str = ""

    anthropicApiKey: str = ""
    claudeModel: str = "claude-opus-5-5"
    deepgramApiKey: str = ""
    deepgramModel: str = "nova-3"

    sahaiBaseUrl: str = ""
    sahaiApiKey: str = ""
    sahaiWebhookSecret: str = ""
    abdmHipId: str = ""
    abdmHiuId: str = ""

    whatsAppAccessToken: str = ""
    whatsAppPhoneNumberId: str = ""
    whatsAppApiVersion: str = "v22.0"

    parentChannelToken: str = ""
    noImprovementAlertWeeks: int = 2


@lru_cache(maxsize=1)
def getSettings() -> Settings:
    settings = Settings()
    if not settings.configSecretName:
        return settings
    secretsClient = boto3.client("secretsmanager", region_name=settings.awsRegion)
    secretValues = json.loads(secretsClient.get_secret_value(SecretId=settings.configSecretName)["SecretString"])
    if not isinstance(secretValues, dict):
        raise RuntimeError("Secrets Manager config payload must be a JSON object")
    return settings.model_copy(update=secretValues)
