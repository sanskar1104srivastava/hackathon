"""Tool endpoints for the team's existing calling agent and WhatsApp bot.

A parent calls and asks what happens next for their child; the agent calls `GET /status` with the caller's number
and reads back `summaryHi`. It must confirm the child's name and birth month with the caller before sharing it.
"""

from __future__ import annotations

import secrets
from typing import Any

from fastapi import APIRouter, Header
from pydantic import BaseModel, ConfigDict, Field

from common.config.settings import getSettings
from common.constants.errorCodes import ErrorCode
from common.http.errorHandler import AppError
from modules.alerts.alertService import createAlert
from modules.children import dbService as childrenDb
from modules.demo import demoClock
from modules.homePlan import planService
from modules.screening.adviceTexts import DOMAIN_NAMES_HI
from modules.screening.apiService import COLOUR_HI

router = APIRouter(prefix="/v1/parent-channel", tags=["parent channel"])
REFERRAL_STATUS_HI = {"sent": "अभी अस्पताल नहीं पहुँचे", "reached": "अस्पताल पहुँच गए", "underTreatment": "इलाज चल रहा है"}


class CallbackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phone: str = Field(pattern=r"^[6-9]\d{9}$")
    childId: str | None = None
    questionText: str = Field(min_length=1, max_length=500)


def requireChannelToken(token: str) -> None:
    expected = getSettings().parentChannelToken
    if not expected or not secrets.compare_digest(expected, token):
        raise AppError(401, ErrorCode.NOT_AUTHENTICATED, "Invalid channel token")


def childStatusHi(child: dict[str, Any]) -> dict[str, Any]:
    childId = child["childId"]
    latest = next(iter(childrenDb.listChildRecords(childId, "SCREENING#", limit=1)), None)
    referral = next(iter(childrenDb.listChildRecords(childId, "REFERRAL#", limit=1)), None)
    plan = planService.getActivePlan(childId)
    lines = []
    if latest:
        lines.append(f"{child['name']} की आख़िरी जाँच {latest['screenedAt'][:10]} को हुई।")
        lines += [
            f"{DOMAIN_NAMES_HI[domain]}: {COLOUR_HI[result['colour']]}"
            for domain, result in latest["outcome"]["domains"].items()
        ]
    if referral:
        lines.append(f"डॉक्टर को दिखाना है: {referral['facilityName']}। स्थिति: {REFERRAL_STATUS_HI[referral['status']]}।")
        if referral.get("carePlan", {}).get("careInstructionsHi"):
            lines.append(f"डॉक्टर की सलाह: {referral['carePlan']['careInstructionsHi']}")
    if plan:
        activities = planService.todaysActivities(child, plan, demoClock.now().date())
        lines += [f"आज का खेल: {activity.titleHi}। {activity.stepsHi}" for activity in activities]
    return {
        "childId": childId,
        "name": child["name"],
        "dateOfBirth": child["dateOfBirth"],
        "summaryHi": "\n".join(lines) or "अभी कोई जाँच दर्ज नहीं है।",
    }


@router.get("/status")
def getStatus(phone: str, channelToken: str = Header(alias="X-Channel-Token")) -> dict[str, Any]:
    requireChannelToken(channelToken)
    return {"children": [childStatusHi(child) for child in childrenDb.listChildrenByPhone(phone)]}


@router.post("/callback-request", status_code=201)
def requestCallback(request: CallbackRequest, channelToken: str = Header(alias="X-Channel-Token")) -> dict[str, Any]:
    requireChannelToken(channelToken)
    children = childrenDb.listChildrenByPhone(request.phone)
    child = next((c for c in children if c["childId"] == request.childId), children[0] if children else None)
    if child is None:
        raise AppError(404, ErrorCode.NOT_FOUND, "No child registered with this phone number")
    alert = createAlert(child, "callbackRequested", f"{child['name']} के परिवार का सवाल: {request.questionText}")
    return {"alertId": alert["alertId"]}
