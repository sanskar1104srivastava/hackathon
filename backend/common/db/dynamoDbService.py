from __future__ import annotations

import json
from decimal import Decimal
from functools import lru_cache
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key

from common.config.settings import getSettings


def toDynamo(value: Any) -> Any:
    """DynamoDB rejects floats; round-trip through JSON so every float becomes a Decimal."""
    return json.loads(json.dumps(value, default=str), parse_float=Decimal)


def fromDynamo(value: Any) -> Any:
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    if isinstance(value, dict):
        return {key: fromDynamo(item) for key, item in value.items()}
    if isinstance(value, list):
        return [fromDynamo(item) for item in value]
    return value


class DynamoDbService:
    """Single-table access: items keyed by pk/sk, with two generic indexes (gsi1, gsi2)."""

    def __init__(self, tableName: str | None = None) -> None:
        settings = getSettings()
        dynamodb = boto3.resource(
            "dynamodb", region_name=settings.awsRegion, endpoint_url=settings.dynamoEndpointUrl or None
        )
        self.table = dynamodb.Table(tableName or settings.mainTableName)

    def putItem(self, item: dict[str, Any], onlyIfNew: bool = False) -> bool:
        """Returns False when `onlyIfNew` is set and the item already exists."""
        kwargs: dict[str, Any] = {"Item": toDynamo(item)}
        if onlyIfNew:
            kwargs["ConditionExpression"] = "attribute_not_exists(pk)"
        try:
            self.table.put_item(**kwargs)
        except self.table.meta.client.exceptions.ConditionalCheckFailedException:
            return False
        return True

    def getItem(self, pk: str, sk: str) -> dict[str, Any] | None:
        item = self.table.get_item(Key={"pk": pk, "sk": sk}).get("Item")
        return fromDynamo(item) if item else None

    def setFields(self, pk: str, sk: str, fields: dict[str, Any], removeFields: tuple[str, ...] = ()) -> dict[str, Any]:
        names = {f"#f{i}": name for i, name in enumerate(fields)}
        values = {f":v{i}": value for i, value in enumerate(fields.values())}
        expression = "SET " + ", ".join(f"#f{i} = :v{i}" for i in range(len(fields)))
        if removeFields:
            names |= {f"#r{i}": name for i, name in enumerate(removeFields)}
            expression += " REMOVE " + ", ".join(f"#r{i}" for i in range(len(removeFields)))
        response = self.table.update_item(
            Key={"pk": pk, "sk": sk},
            UpdateExpression=expression,
            ExpressionAttributeNames=names,
            ExpressionAttributeValues=toDynamo(values),
            ConditionExpression="attribute_exists(pk)",
            ReturnValues="ALL_NEW",
        )
        return fromDynamo(response["Attributes"])

    def addCounters(self, pk: str, sk: str, counters: dict[str, int], labels: dict[str, Any] | None = None) -> None:
        """Atomically increments counters, creating the item on first use. `labels` are plain fields to keep set."""
        names = {f"#c{i}": name for i, name in enumerate(counters)}
        values: dict[str, Any] = {f":c{i}": amount for i, amount in enumerate(counters.values())}
        expression = "ADD " + ", ".join(f"#c{i} :c{i}" for i in range(len(counters)))
        if labels:
            names |= {f"#l{i}": name for i, name in enumerate(labels)}
            values |= {f":l{i}": value for i, value in enumerate(labels.values())}
            expression += " SET " + ", ".join(f"#l{i} = :l{i}" for i in range(len(labels)))
        self.table.update_item(
            Key={"pk": pk, "sk": sk},
            UpdateExpression=expression,
            ExpressionAttributeNames=names,
            ExpressionAttributeValues=toDynamo(values),
        )

    def query(self, pk: str, skPrefix: str = "", newestFirst: bool = False, limit: int = 200) -> list[dict[str, Any]]:
        condition = Key("pk").eq(pk)
        if skPrefix:
            condition &= Key("sk").begins_with(skPrefix)
        return self._queryAll(KeyConditionExpression=condition, ScanIndexForward=not newestFirst, limit=limit)

    def queryIndex(self, indexName: str, pkValue: str, skPrefix: str = "", limit: int = 200) -> list[dict[str, Any]]:
        condition = Key(f"{indexName}pk").eq(pkValue)
        if skPrefix:
            condition &= Key(f"{indexName}sk").begins_with(skPrefix)
        return self._queryAll(IndexName=indexName, KeyConditionExpression=condition, limit=limit)

    def _queryAll(self, limit: int, **kwargs: Any) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        while True:
            response = self.table.query(**kwargs)
            items.extend(response.get("Items", []))
            lastKey = response.get("LastEvaluatedKey")
            if not lastKey or len(items) >= limit:
                return fromDynamo(items[:limit])
            kwargs["ExclusiveStartKey"] = lastKey


@lru_cache(maxsize=1)
def getDb() -> DynamoDbService:
    return DynamoDbService()
