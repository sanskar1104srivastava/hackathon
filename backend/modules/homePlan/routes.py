"""The parent's own page, opened from the QR code or the WhatsApp link (UC-5)."""

from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from modules.children import dbService as childrenDb
from modules.children.dbService import publicView
from modules.demo import demoClock
from modules.homePlan import planService

router = APIRouter(prefix="/v1/parent", tags=["parent"])


class ProgressRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    activityId: str
    score: float = Field(1.0, ge=0, le=1, description="1 when done well; AI checks can give partial credit")


@router.get("/{childId}")
def getParentView(childId: str, token: str) -> dict[str, Any]:
    child = planService.verifyParentToken(childId, token)
    today: date = demoClock.now().date()
    latest = next(iter(childrenDb.listChildRecords(childId, "SCREENING#", limit=1)), None)
    referral = next(iter(childrenDb.listChildRecords(childId, "REFERRAL#", limit=1)), None)
    plan = planService.getActivePlan(childId)
    return {
        "child": {key: child[key] for key in ("childId", "name", "sex", "dateOfBirth")},
        "latestResult": latest and {"screenedAt": latest["screenedAt"], "outcome": latest["outcome"]},
        "referral": referral and publicView(referral),
        "homePlan": plan
        and {
            "focusAreas": plan["focusAreas"],
            "stage": plan["stage"],
            "todaysActivities": [a.model_dump() for a in planService.todaysActivities(child, plan, today)],
        },
    }


@router.post("/{childId}/progress")
def recordProgress(childId: str, token: str, request: ProgressRequest) -> dict[str, Any]:
    planService.verifyParentToken(childId, token)
    plan = planService.recordProgress(childId, request.activityId, request.score)
    return {"weekPoints": plan["weekPoints"]}
