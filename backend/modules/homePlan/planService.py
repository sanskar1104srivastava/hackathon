"""Home activity plan for a yellow result (UC-5) and its weekly progress check (UC-6)."""

from __future__ import annotations

import json
import secrets
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel

from common.config.settings import getSettings
from common.constants.errorCodes import ErrorCode
from common.constants.tableKeys import ACTIVE_PLAN_SK, ACTIVE_PLANS_GSI1PK, GSI1, childPk
from common.db.dynamoDbService import getDb
from common.http.errorHandler import AppError
from common.messaging import whatsAppService
from common.utils.dateTimeUtils import ageInMonths
from modules.alerts.alertService import createAlert
from modules.children import dbService as childrenDb
from modules.dashboard import statsService
from modules.screening.rulesEngine import ScreeningOutcome

ACTIVITIES_PATH = Path(__file__).resolve().parents[2] / "data" / "rules" / "homeActivities.json"
Focus = Literal["speech", "movement", "social", "learning", "nutrition"]
IMPROVED_WEEK_SCORE = 0.6
IMPROVED_STEP = 0.15

FOCUS_BY_CHECK: dict[str, Focus] = {
    "pictureNaming": "speech",
    "babbles": "speech",
    "singleWords": "speech",
    "twoWordPhrases": "speech",
    "sitsWithoutSupport": "movement",
    "standsWithSupport": "movement",
    "walksWithSupport": "movement",
    "standsAlone": "movement",
    "walksAlone": "movement",
    "movementVideo": "movement",
    "socialSmile": "social",
    "gestures": "social",
    "mchat": "social",
    "followsObject": "social",
    "turnsToSound": "social",
    "attentionTask": "learning",
}


class Activity(BaseModel):
    id: str
    focus: Focus
    stage: int
    minAgeMonths: float
    maxAgeMonths: float
    checkMethod: Literal["voice", "photo", "video", "none"]
    titleHi: str
    stepsHi: str


@lru_cache(maxsize=1)
def loadActivities() -> list[Activity]:
    return [Activity(**item) for item in json.loads(ACTIVITIES_PATH.read_text(encoding="utf-8"))["activities"]]


def focusAreasFor(outcome: ScreeningOutcome) -> list[Focus]:
    yellow = [item for result in outcome.domains.values() for item in result.findings if item.colour == "yellow"]
    return sorted({FOCUS_BY_CHECK.get(item.checkId, "nutrition") for item in yellow})


def todaysActivities(child: dict[str, Any], plan: dict[str, Any], today: date) -> list[Activity]:
    """One activity per focus area, rotating daily among those that suit the child's age and plan stage."""
    ageMonths = ageInMonths(date.fromisoformat(child["dateOfBirth"]), today)
    dayNumber = (today - date.fromisoformat(plan["startedOn"])).days
    chosen = []
    for focus in plan["focusAreas"]:
        suitable = [a for a in loadActivities() if a.focus == focus and a.minAgeMonths <= ageMonths <= a.maxAgeMonths]
        atStage = [a for a in suitable if a.stage == plan["stage"]] or suitable
        if atStage:
            chosen.append(atStage[dayNumber % len(atStage)])
    return chosen


def getActivePlan(childId: str) -> dict[str, Any] | None:
    return getDb().getItem(childPk(childId), ACTIVE_PLAN_SK)


def assignPlan(child: dict[str, Any], outcome: ScreeningOutcome, now: datetime) -> dict[str, Any]:
    focusAreas = focusAreasFor(outcome)
    existing = getActivePlan(child["childId"])
    if existing:
        merged = sorted(set(existing["focusAreas"]) | set(focusAreas))
        return getDb().setFields(existing["pk"], existing["sk"], {"focusAreas": merged})
    plan = {
        "pk": childPk(child["childId"]),
        "sk": ACTIVE_PLAN_SK,
        "gsi1pk": ACTIVE_PLANS_GSI1PK,
        "gsi1sk": child["childId"],
        "childId": child["childId"],
        "focusAreas": focusAreas,
        "stage": 1,
        "startedOn": now.date().isoformat(),
        "weekStartedOn": now.date().isoformat(),
        "weekPoints": 0,
        "previousWeekScore": None,
        "noImprovementWeeks": 0,
        "countedImproving": False,
        "alertRaised": False,
        "lastSentOn": None,
    }
    getDb().putItem(plan)
    statsService.recordEvent(child, homePlans=1)
    return plan


def recordProgress(childId: str, activityId: str, score: float) -> dict[str, Any]:
    plan = getActivePlan(childId)
    if plan is None:
        raise AppError(404, ErrorCode.NOT_FOUND, "No active home plan")
    if activityId not in {activity.id for activity in loadActivities()}:
        raise AppError(400, ErrorCode.INVALID_REQUEST, "Unknown activity")
    return getDb().setFields(plan["pk"], plan["sk"], {"weekPoints": plan["weekPoints"] + score})


def sendTodaysActivities(child: dict[str, Any], plan: dict[str, Any], today: date) -> None:
    if plan.get("lastSentOn") == today.isoformat():
        return
    lines = [f"• {activity.titleHi}: {activity.stepsHi}" for activity in todaysActivities(child, plan, today)]
    whatsAppService.sendText(child["guardianPhone"], f"{child['name']} के लिए आज के खेल:\n" + "\n".join(lines))
    getDb().setFields(plan["pk"], plan["sk"], {"lastSentOn": today.isoformat()})


def evaluateWeek(child: dict[str, Any], plan: dict[str, Any], today: date) -> dict[str, Any]:
    """Improving moves the plan to its next stage; no improvement for N weeks alerts the ASHA."""
    expectedPoints = 7 * max(1, len(plan["focusAreas"]))
    weekScore = round(min(1.0, plan["weekPoints"] / expectedPoints), 2)
    previous = plan["previousWeekScore"]
    improved = weekScore >= IMPROVED_WEEK_SCORE or (previous is not None and weekScore >= previous + IMPROVED_STEP)

    fields: dict[str, Any] = {"previousWeekScore": weekScore, "weekPoints": 0, "weekStartedOn": today.isoformat()}
    if improved:
        fields |= {"noImprovementWeeks": 0, "stage": min(plan["stage"] + 1, 2)}
        if not plan["countedImproving"]:
            statsService.recordEvent(child, improving=1)
            fields["countedImproving"] = True
    else:
        fields["noImprovementWeeks"] = plan["noImprovementWeeks"] + 1
        if fields["noImprovementWeeks"] >= getSettings().noImprovementAlertWeeks and not plan["alertRaised"]:
            createAlert(
                child,
                "noImprovement",
                f"{child['name']}: {fields['noImprovementWeeks']} हफ़्ते से घर के खेलों में सुधार नहीं। दोबारा जाँच करें या रेफ़र करें।",
            )
            fields["alertRaised"] = True
    return getDb().setFields(plan["pk"], plan["sk"], fields)


def listActivePlans() -> list[dict[str, Any]]:
    return getDb().queryIndex(GSI1, ACTIVE_PLANS_GSI1PK, limit=5000)


def verifyParentToken(childId: str, token: str) -> dict[str, Any]:
    child = childrenDb.getChild(childId)
    if not secrets.compare_digest(child["parentAccessToken"], token):
        raise AppError(401, ErrorCode.NOT_AUTHENTICATED, "Invalid parent link")
    return child
