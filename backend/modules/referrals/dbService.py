from __future__ import annotations

from typing import Any

from common.constants.errorCodes import ErrorCode
from common.constants.tableKeys import (
    GSI1,
    GSI2,
    OPEN_REFERRALS_GSI1PK,
    UNDER_TREATMENT_GSI1PK,
    childPk,
    facilityGsi2Pk,
)
from common.db.dynamoDbService import getDb
from common.http.errorHandler import AppError


def referralSk(referralId: str) -> str:
    return f"REFERRAL#{referralId}"


def saveReferral(referral: dict[str, Any]) -> None:
    getDb().putItem(
        {
            **referral,
            "pk": childPk(referral["childId"]),
            "sk": referralSk(referral["referralId"]),
            "gsi1pk": OPEN_REFERRALS_GSI1PK,
            "gsi1sk": referral["createdAt"],
            "gsi2pk": facilityGsi2Pk(referral["facilityId"]),
            "gsi2sk": referral["createdAt"],
        }
    )


def getReferral(childId: str, referralId: str) -> dict[str, Any]:
    referral = getDb().getItem(childPk(childId), referralSk(referralId))
    if referral is None:
        raise AppError(404, ErrorCode.NOT_FOUND, "Referral not found")
    return referral


def updateReferral(
    childId: str, referralId: str, fields: dict[str, Any], removeFields: tuple[str, ...] = ()
) -> dict[str, Any]:
    return getDb().setFields(childPk(childId), referralSk(referralId), fields, removeFields)


def listFacilityReferrals(facilityId: str) -> list[dict[str, Any]]:
    return getDb().queryIndex(GSI2, facilityGsi2Pk(facilityId))


def listOpenReferrals() -> list[dict[str, Any]]:
    return getDb().queryIndex(GSI1, OPEN_REFERRALS_GSI1PK, limit=5000)


def listReferralsUnderTreatment() -> list[dict[str, Any]]:
    return getDb().queryIndex(GSI1, UNDER_TREATMENT_GSI1PK, limit=5000)
