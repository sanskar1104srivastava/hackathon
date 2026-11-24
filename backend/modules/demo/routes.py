"""Demo-only controls. Disabled in prod."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from common.config.settings import getSettings
from common.constants.errorCodes import ErrorCode
from common.http.errorHandler import AppError
from modules.demo import demoClock
from modules.followUpWorker.followUpService import runDaily

router = APIRouter(prefix="/v1/demo", tags=["demo"])


@router.get("/clock")
def getClock() -> dict[str, Any]:
    return {"offsetDays": demoClock.offsetDays(), "now": demoClock.now().isoformat(timespec="seconds")}


@router.post("/skip-week")
def skipWeek() -> dict[str, Any]:
    """Moves app time forward 7 days and runs the daily follow-up, so the weekly loop shows up immediately."""
    if getSettings().appEnv == "prod":
        raise AppError(403, ErrorCode.INVALID_REQUEST, "Demo controls are disabled in prod")
    offset = demoClock.advanceDays(7)
    return {"offsetDays": offset, "followUp": runDaily(demoClock.now())}
