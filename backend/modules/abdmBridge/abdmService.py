"""ABDM flows through the Sahai bridge.

HIP (M2): each screening is linked to the child's ABHA as a care context once ABDM sends the link token.
HIU (M3): a doctor's records request becomes a consent request, then a health-information pull.
Sahai answers asynchronously on our webhook, matched to our requests by tracking ID.
"""

from __future__ import annotations

import json
import logging
from datetime import date
from typing import Any

from common.abdm.sahaiClient import getSahai, isValidSahaiSignature
from common.config.settings import getSettings
from common.constants.errorCodes import ErrorCode
from common.constants.tableKeys import PROFILE_SK, childPk, trackingPk
from common.db.dynamoDbService import getDb
from common.http.errorHandler import AppError
from common.utils.dateTimeUtils import nowIso
from modules.abdmBridge.fhirMapper import screeningObservation
from modules.referrals.requests import RecordsRequest

logger = logging.getLogger(__name__)
TRACKING_SK = "TRACK"
HI_TYPES = ["WellnessRecord"]
ABDM_GENDER = {"male": "M", "female": "F"}


def saveTracking(trackingId: str, context: dict[str, Any]) -> None:
    getDb().putItem({"pk": trackingPk(trackingId), "sk": TRACKING_SK, "createdAt": nowIso(), **context})


def startScreeningLink(child: dict[str, Any], screening: dict[str, Any], screeningSk: str) -> None:
    """Best effort: a failed ABDM call never blocks the screening itself."""
    sahai = getSahai()
    if not child.get("abhaAddress") or not sahai.isConfigured:
        return
    try:
        response = sahai.requestLinkToken(
            abhaAddress=child["abhaAddress"],
            patientReference=child["childId"],
            name=child["name"],
            gender=ABDM_GENDER[child["sex"]],
            yearOfBirth=date.fromisoformat(child["dateOfBirth"]).year,
            idempotencyKey=f"link-{screening['screeningId']}",
        )
        saveTracking(
            response["trackingId"], {"kind": "linkToken", "childId": child["childId"], "screeningSk": screeningSk}
        )
    except AppError as error:
        logger.warning("ABDM link token request failed childId=%s error=%s", child["childId"], error.message)


def requestScreeningRecords(child: dict[str, Any], referral: dict[str, Any], requester: RecordsRequest) -> str:
    response = getSahai().requestConsent(
        abhaAddress=child["abhaAddress"],
        patientReference=child["childId"],
        requester={
            "name": requester.requesterName,
            "type": requester.requesterIdType,
            "value": requester.requesterId,
            "system": "https://hpr.abdm.gov.in",
        },
        hiTypes=HI_TYPES,
        fromIso=f"{child['dateOfBirth']}T00:00:00Z",
        toIso=nowIso(),
        idempotencyKey=f"consent-{referral['referralId']}",
    )
    saveTracking(
        response["trackingId"], {"kind": "consent", "childId": child["childId"], "referralId": referral["referralId"]}
    )
    return response["trackingId"]


def fetchRecords(referral: dict[str, Any]) -> dict[str, Any]:
    status = referral.get("recordsStatus", "notRequested")
    if status != "ready":
        return {"recordsStatus": status}
    return {"recordsStatus": status, "records": getSahai().getDecryptedRecords(referral["recordsTrackingId"])}


def handleWebhook(rawBody: bytes, signature: str) -> None:
    if not isValidSahaiSignature(rawBody, signature, getSettings().sahaiWebhookSecret):
        raise AppError(401, ErrorCode.NOT_AUTHENTICATED, "Invalid webhook signature")
    event = json.loads(rawBody)
    tracking = getDb().getItem(trackingPk(str(event.get("trackingId", ""))), TRACKING_SK)
    if tracking is None:
        logger.info("Ignoring unmatched ABDM event type=%s", event.get("eventType"))
        return

    eventType, payload = event.get("eventType"), event.get("payload") or {}
    if tracking["kind"] == "linkToken" and payload.get("linkToken"):
        linkScreening(tracking, payload["linkToken"])
    elif tracking["kind"] == "consent" and eventType == "consent.granted":
        requestHealthInformation(tracking, event["correlationIds"]["consentId"])
    elif tracking["kind"] == "consent" and eventType == "consent.denied":
        updateReferralRecords(tracking, {"recordsStatus": "denied"})
    elif tracking["kind"] == "healthInformation" and eventType == "healthInformation.received":
        updateReferralRecords(tracking, {"recordsStatus": "ready", "recordsTrackingId": event["trackingId"]})


def linkScreening(tracking: dict[str, Any], linkToken: str) -> None:
    db = getDb()
    child = db.getItem(childPk(tracking["childId"]), PROFILE_SK)
    screening = db.getItem(childPk(tracking["childId"]), tracking["screeningSk"])
    if child is None or screening is None:
        return
    careContext = {
        "reference": screening["screeningId"],
        "display": f"RBSK screening {screening['screenedAt'][:10]}",
        "hiTypes": HI_TYPES,
        "clinicalPayload": screeningObservation(screening),
    }
    getSahai().linkCareContexts(
        abhaAddress=child["abhaAddress"],
        patientReference=child["childId"],
        linkToken=linkToken,
        careContexts=[careContext],
        idempotencyKey=f"care-context-{screening['screeningId']}",
    )
    db.setFields(screening["pk"], screening["sk"], {"abdmStatus": "linked"})


def requestHealthInformation(tracking: dict[str, Any], consentId: str) -> None:
    child = getDb().getItem(childPk(tracking["childId"]), PROFILE_SK)
    response = getSahai().requestHealthInformation(
        consentId=consentId,
        fromIso=f"{child['dateOfBirth']}T00:00:00Z",
        toIso=nowIso(),
        idempotencyKey=f"hi-{consentId}",
    )
    saveTracking(
        response["trackingId"],
        {"kind": "healthInformation", "childId": tracking["childId"], "referralId": tracking["referralId"]},
    )
    updateReferralRecords(tracking, {"recordsStatus": "requested"})


def updateReferralRecords(tracking: dict[str, Any], fields: dict[str, Any]) -> None:
    getDb().setFields(childPk(tracking["childId"]), f"REFERRAL#{tracking['referralId']}", fields)
