"""Creates the app table on a local DynamoDB (moto server) for development without AWS.

uv run moto_server -p 5000                       # in one terminal
uv run python -m scripts.createLocalTable        # once, with dynamoEndpointUrl=http://localhost:5000 in .env
"""

import json
from pathlib import Path

import boto3

from common.config.settings import getSettings

TABLE_DEFINITION = Path(__file__).resolve().parents[1] / "deploy" / "tableDefinition.json"

if __name__ == "__main__":
    settings = getSettings()
    if not settings.dynamoEndpointUrl:
        raise SystemExit("Set dynamoEndpointUrl (for example http://localhost:5000) to use a local table")
    client = boto3.client("dynamodb", region_name=settings.awsRegion, endpoint_url=settings.dynamoEndpointUrl)
    definition = json.loads(TABLE_DEFINITION.read_text()) | {"TableName": settings.mainTableName}
    if settings.mainTableName in client.list_tables()["TableNames"]:
        print(f"Table {settings.mainTableName} already exists")
    else:
        client.create_table(**definition)
        print(f"Created table {settings.mainTableName} at {settings.dynamoEndpointUrl}")
