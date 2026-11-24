from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from modules.alerts.alertService import closeAlert, listOpenAlerts

router = APIRouter(prefix="/v1/alerts", tags=["alerts"])


@router.get("")
def getOpenAlerts(districtCode: int) -> list[dict[str, Any]]:
    return listOpenAlerts(districtCode)


@router.post("/{childId}/{alertId}/close")
def close(childId: str, alertId: str) -> dict[str, Any]:
    return closeAlert(childId, alertId)
