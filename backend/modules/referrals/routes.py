from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from modules.referrals import apiService
from modules.referrals.requests import DiagnosisRequest, RecordsRequest

router = APIRouter(prefix="/v1", tags=["referrals"])


@router.get("/facilities/{facilityId}/referrals")
def listFacilityReferrals(facilityId: str) -> list[dict[str, Any]]:
    return apiService.listFacilityReferrals(facilityId)


@router.post("/children/{childId}/referrals/{referralId}/arrival")
def markArrived(childId: str, referralId: str) -> dict[str, Any]:
    return apiService.markArrived(childId, referralId)


@router.post("/children/{childId}/referrals/{referralId}/diagnosis")
def recordDiagnosis(childId: str, referralId: str, request: DiagnosisRequest) -> dict[str, Any]:
    return apiService.recordDiagnosis(childId, referralId, request)


@router.post("/children/{childId}/referrals/{referralId}/records-request")
def requestRecords(childId: str, referralId: str, request: RecordsRequest) -> dict[str, Any]:
    return apiService.requestRecords(childId, referralId, request)


@router.get("/children/{childId}/referrals/{referralId}/records")
def getRecords(childId: str, referralId: str) -> dict[str, Any]:
    return apiService.getRecords(childId, referralId)
