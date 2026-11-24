from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from modules.screening import aiCheckService, apiService
from modules.screening.aiCheckService import (
    DeviceReadingResult,
    SignCheckResult,
    SpeechCheckRequest,
    SpeechCheckResult,
)
from modules.screening.requests import DeviceReadingRequest, PhotoCheckRequest, ScreeningInput

router = APIRouter(prefix="/v1", tags=["screening"])


@router.get("/checks")
def listChecks(ageMonths: float = Query(ge=0, le=228)) -> dict[str, Any]:
    return apiService.checksForChildAge(ageMonths)


@router.post("/children/{childId}/screenings", status_code=201)
def submitScreening(childId: str, request: ScreeningInput) -> dict[str, Any]:
    return apiService.submitScreening(childId, request)


@router.post("/ai/sign-check")
def checkSign(request: PhotoCheckRequest) -> SignCheckResult:
    return aiCheckService.checkSign(request)


@router.post("/ai/device-reading")
def readDevice(request: DeviceReadingRequest) -> DeviceReadingResult:
    return aiCheckService.readDevice(request)


@router.post("/ai/speech-check")
def checkSpeech(request: SpeechCheckRequest) -> SpeechCheckResult:
    return aiCheckService.checkSpeech(request)
