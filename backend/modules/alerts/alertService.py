"""Tasks for the ASHA: re-check a child, chase a referral, or call a parent back."""

from __future__ import annotations

import uuid
from typing import Any, Literal

from common.constants.errorCodes import ErrorCode
from common.constants.tableKeys import GSI2, alertsGsi2Pk, childPk
from common.db.dynamoDbService import getDb
from common.http.errorHandler import AppError
from common.utils.dateTimeUtils import nowIso
from modules.children.dbService import publicView
from modules.dashboard import statsService

AlertKind = Literal["noImprovement", "referralNotReached", "callbackRequested"]


def createAlert(child: dict[str, Any], kind: AlertKind, messageHi: str) -> dict[str, Any]:
    createdAt = nowIso()
    alert = {
        "alertId": uuid.uuid4().hex,
        "childId": child["childId"],
        "childName": child["name"],
        "guardianPhone": child["guardianPhone"],
        "blockName": child["blockName"],
        "kind": kind,
        "messageHi": messageHi,
        "status": "open",
        "createdAt": createdAt,
    }
    getDb().putItem(
        {
            **alert,
            "pk": childPk(child["childId"]),
            "sk": f"ALERT#{createdAt}#{alert['alertId']}",
            "gsi2pk": alertsGsi2Pk(child["districtCode"]),
            "gsi2sk": f"open#{createdAt}",
        }
    )
    statsService.recordEvent(child, alerts=1)
    return alert


def listOpenAlerts(districtCode: int) -> list[dict[str, Any]]:
    return [publicView(item) for item in getDb().queryIndex(GSI2, alertsGsi2Pk(districtCode), "open#")]


def closeAlert(childId: str, alertId: str) -> dict[str, Any]:
    alert = next((item for item in getDb().query(childPk(childId), "ALERT#") if item["alertId"] == alertId), None)
    if alert is None:
        raise AppError(404, ErrorCode.NOT_FOUND, "Alert not found")
    closed = getDb().setFields(alert["pk"], alert["sk"], {"status": "closed", "gsi2sk": f"closed#{nowIso()}"})
    return publicView(closed)
