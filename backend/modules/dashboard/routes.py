from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from modules.dashboard.statsService import summary

router = APIRouter(prefix="/v1/dashboard", tags=["dashboard"])


@router.get("/summary")
def getSummary(districtCode: int | None = None) -> dict[str, Any]:
    return summary(districtCode)
