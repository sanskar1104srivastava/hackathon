from __future__ import annotations

from datetime import date
from typing import Any

from common.config.settings import getSettings
from common.constants.errorCodes import ErrorCode
from common.http.errorHandler import AppError
from common.messaging import whatsAppService
from common.utils.dateTimeUtils import DAYS_PER_MONTH, nowIso
from modules.abdmBridge import abdmService
from modules.children import dbService as childrenDb
from modules.children.dbService import publicView
from modules.dashboard import statsService
from modules.demo import demoClock
from modules.homePlan import planService
from modules.referrals import apiService as referralService
from modules.screening import dbService
from modules.screening.adviceTexts import DOMAIN_NAMES_HI, NEXT_STEP_HI
from modules.screening.checkCatalog import checksForAge, getCatalog
from modules.screening.requests import ScreeningInput
from modules.screening.rulesEngine import ChildFacts, ScreeningOutcome, evaluateScreening

COLOUR_HI = {"green": "🟢 ठीक", "yellow": "🟡 नज़र रखनी है", "red": "🔴 डॉक्टर को दिखाना है"}


def checksForChildAge(ageMonths: float) -> dict[str, Any]:
    catalog = getCatalog()
    return {"version": catalog.version, "checks": checksForAge(ageMonths), "pictureCards": catalog.pictureCards}


def submitScreening(childId: str, request: ScreeningInput) -> dict[str, Any]:
    child = childrenDb.getChild(childId)
    usesMedia = bool(request.aiObservations or request.speech)
    if usesMedia and not request.consentGiven:
        raise AppError(400, ErrorCode.CONSENT_REQUIRED, "Parent consent is required before photos, video or voice")
    ageDays = (request.screenedAt.date() - date.fromisoformat(child["dateOfBirth"])).days
    if ageDays < 0:
        raise AppError(400, ErrorCode.INVALID_REQUEST, "Screening date is before the date of birth")

    outcome = evaluateScreening(ChildFacts(sex=child["sex"], ageDays=ageDays), request)
    screening = {
        **request.model_dump(mode="json"),
        "childId": childId,
        "ageMonths": round(ageDays / DAYS_PER_MONTH, 1),
        "outcome": outcome.model_dump(mode="json"),
        "createdAt": nowIso(),
    }
    stored, isNew = dbService.saveScreening(screening)
    result: dict[str, Any] = {"screening": publicView(stored), "duplicate": not isNew}
    if isNew:
        result |= applyOutcome(child, stored, outcome, request.referralFacilityId)
    return result


def applyOutcome(
    child: dict[str, Any], screening: dict[str, Any], outcome: ScreeningOutcome, facilityId: str | None
) -> dict[str, Any]:
    flagged = {
        statsService.flaggedCounter(domain): 1 for domain, result in outcome.domains.items() if result.colour != "green"
    }
    statsService.recordEvent(child, screened=1, **flagged)

    effects: dict[str, Any] = {"referral": None, "homePlan": None}
    if "referral" in outcome.nextSteps:
        effects["referral"] = referralService.createReferral(child, screening["screeningId"], outcome, facilityId)
    if "homePlan" in outcome.nextSteps:
        effects["homePlan"] = publicView(planService.assignPlan(child, outcome, demoClock.now()))

    whatsAppService.sendText(child["guardianPhone"], resultMessageHi(child, outcome))
    abdmService.startScreeningLink(
        child, screening, dbService.screeningSk(screening["screenedAt"], screening["screeningId"])
    )
    return effects


def resultMessageHi(child: dict[str, Any], outcome: ScreeningOutcome) -> str:
    lines = [f"{child['name']} की जाँच का नतीजा:"]
    lines += [f"{DOMAIN_NAMES_HI[domain]}: {COLOUR_HI[result.colour]}" for domain, result in outcome.domains.items()]
    lines += [NEXT_STEP_HI[step] for step in outcome.nextSteps] or [NEXT_STEP_HI["none"]]
    appBaseUrl = getSettings().appBaseUrl
    if appBaseUrl:
        lines.append(f"पूरी जानकारी: {appBaseUrl}/parent/{child['childId']}?token={child['parentAccessToken']}")
    return "\n".join(lines)
