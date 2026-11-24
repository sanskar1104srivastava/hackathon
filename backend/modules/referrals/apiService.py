from __future__ import annotations

import uuid
from typing import Any

from common.constants.errorCodes import ErrorCode
from common.constants.tableKeys import UNDER_TREATMENT_GSI1PK
from common.http.errorHandler import AppError
from common.messaging import whatsAppService
from common.utils.dateTimeUtils import nowIso
from modules.abdmBridge import abdmService
from modules.children import dbService as childrenDb
from modules.children.dbService import publicView
from modules.dashboard import statsService
from modules.geo.geoService import facilitiesForDistrict, facilityById
from modules.referrals import dbService
from modules.referrals.requests import DiagnosisRequest, RecordsRequest
from modules.screening.rulesEngine import ScreeningOutcome


def createReferral(
    child: dict[str, Any], screeningId: str, outcome: ScreeningOutcome, facilityId: str | None
) -> dict[str, Any]:
    """The digital version of RBSK's three-part referral card: observations, facility, and later the treatment."""
    facility = facilityById(facilityId) if facilityId else facilitiesForDistrict(child["districtCode"])[0]
    redFindings = [item for result in outcome.domains.values() for item in result.findings if item.colour == "red"]
    referral = {
        "referralId": uuid.uuid4().hex,
        "childId": child["childId"],
        "childName": child["name"],
        "guardianPhone": child["guardianPhone"],
        "screeningId": screeningId,
        "facilityId": facility.facilityId,
        "facilityName": facility.name,
        "reasonsHi": [item.noteHi for item in redFindings],
        "reasonsEn": [item.noteEn for item in redFindings],
        "status": "sent",
        "remindersSent": [],
        "createdAt": nowIso(),
    }
    dbService.saveReferral(referral)
    statsService.recordEvent(child, referred=1)
    whatsAppService.sendText(
        child["guardianPhone"],
        (
            f"{child['name']} को डॉक्टर को दिखाना ज़रूरी है।\nकहाँ जाएँ: {facility.name}\n"
            f"क्यों: {'; '.join(referral['reasonsHi'])}\nयह पर्ची अस्पताल में दिखाएँ। जाँच और इलाज मुफ़्त है।"
        ),
    )
    return publicView(referral)


def listFacilityReferrals(facilityId: str) -> list[dict[str, Any]]:
    facilityById(facilityId)
    return [publicView(item) for item in dbService.listFacilityReferrals(facilityId)]


def markArrived(childId: str, referralId: str) -> dict[str, Any]:
    referral = dbService.getReferral(childId, referralId)
    if referral["status"] != "sent":
        return publicView(referral)
    statsService.recordEvent(childrenDb.getChild(childId), reached=1)
    updated = dbService.updateReferral(
        childId, referralId, {"status": "reached", "reachedAt": nowIso()}, removeFields=("gsi1pk", "gsi1sk")
    )
    return publicView(updated)


def recordDiagnosis(childId: str, referralId: str, request: DiagnosisRequest) -> dict[str, Any]:
    """Diagnosis stays with the doctor; recording it starts the treatment reminders for the family (UC-7)."""
    if dbService.getReferral(childId, referralId)["status"] == "sent":
        markArrived(childId, referralId)
    child = childrenDb.getChild(childId)
    updated = dbService.updateReferral(
        childId,
        referralId,
        {
            "status": "underTreatment",
            "doctorName": request.doctorName,
            "diagnosisText": request.diagnosisText,
            "carePlan": request.carePlan.model_dump(mode="json"),
            "diagnosedAt": nowIso(),
            "gsi1pk": UNDER_TREATMENT_GSI1PK,
            "gsi1sk": childId,
        },
    )
    if request.carePlan.careInstructionsHi:
        whatsAppService.sendText(
            child["guardianPhone"],
            f"{child['name']} के इलाज के लिए डॉक्टर की सलाह:\n{request.carePlan.careInstructionsHi}",
        )
    return publicView(updated)


def requestRecords(childId: str, referralId: str, request: RecordsRequest) -> dict[str, Any]:
    child = childrenDb.getChild(childId)
    if not child.get("abhaAddress"):
        raise AppError(409, ErrorCode.INVALID_REQUEST, "Child has no linked ABHA address")
    referral = dbService.getReferral(childId, referralId)
    trackingId = abdmService.requestScreeningRecords(child, referral, request)
    return publicView(
        dbService.updateReferral(
            childId, referralId, {"recordsStatus": "consentRequested", "consentTrackingId": trackingId}
        )
    )


def getRecords(childId: str, referralId: str) -> dict[str, Any]:
    referral = dbService.getReferral(childId, referralId)
    return abdmService.fetchRecords(referral)
