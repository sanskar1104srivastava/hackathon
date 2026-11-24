from __future__ import annotations

from typing import Any

from common.constants.errorCodes import ErrorCode
from common.constants.tableKeys import GSI1, GSI2, PROFILE_SK, areaGsi2Pk, childPk, phoneGsi1Pk
from common.db.dynamoDbService import getDb
from common.http.errorHandler import AppError

KEY_FIELDS = ("pk", "sk", "gsi1pk", "gsi1sk", "gsi2pk", "gsi2sk")
PRIVATE_FIELDS = (*KEY_FIELDS, "parentAccessToken")


def publicView(item: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in item.items() if key not in PRIVATE_FIELDS}


def saveChild(child: dict[str, Any]) -> None:
    getDb().putItem(
        {
            **child,
            "pk": childPk(child["childId"]),
            "sk": PROFILE_SK,
            "gsi1pk": phoneGsi1Pk(child["guardianPhone"]),
            "gsi1sk": child["childId"],
            "gsi2pk": areaGsi2Pk(child["districtCode"]),
            "gsi2sk": f"{child['blockCode']}#{child['name'].lower()}#{child['childId']}",
        }
    )


def getChild(childId: str) -> dict[str, Any]:
    child = getDb().getItem(childPk(childId), PROFILE_SK)
    if child is None:
        raise AppError(404, ErrorCode.NOT_FOUND, "Child not found")
    return child


def updateChild(childId: str, fields: dict[str, Any]) -> dict[str, Any]:
    return getDb().setFields(childPk(childId), PROFILE_SK, fields)


def listChildrenInArea(districtCode: int, blockCode: int | None) -> list[dict[str, Any]]:
    prefix = f"{blockCode}#" if blockCode is not None else ""
    return getDb().queryIndex(GSI2, areaGsi2Pk(districtCode), prefix)


def listChildrenByPhone(phone: str) -> list[dict[str, Any]]:
    return getDb().queryIndex(GSI1, phoneGsi1Pk(phone))


def listChildRecords(childId: str, skPrefix: str, newestFirst: bool = True, limit: int = 20) -> list[dict[str, Any]]:
    return getDb().query(childPk(childId), skPrefix, newestFirst=newestFirst, limit=limit)
