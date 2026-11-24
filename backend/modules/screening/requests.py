from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from modules.screening.checkCatalog import Device

Setting = Literal["facility", "home", "anganwadi", "school"]
AiOutcome = Literal["seen", "notSeen", "unsure"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Measurements(StrictModel):
    weightKg: float | None = Field(None, gt=0.3, lt=200)
    heightCm: float | None = Field(None, gt=30, lt=230)
    muacCm: float | None = Field(None, gt=5, lt=40)
    haemoglobinGdl: float | None = Field(None, gt=2, lt=25)


class AiObservation(StrictModel):
    checkId: str
    outcome: AiOutcome
    reasonHi: str = Field("", max_length=400)


class SpeechResult(StrictModel):
    shownCount: int = Field(ge=1, le=20)
    namedCount: int = Field(ge=0, le=20)


class TaskResult(StrictModel):
    checkId: str
    passed: bool


class ScreeningInput(StrictModel):
    """Everything the field app captured. `answers` maps a check id to the parent's yes (true) or no (false)."""

    screeningId: str = Field(min_length=8, max_length=64, description="Made on the phone so offline re-sync is safe")
    setting: Setting
    screenedAt: datetime
    workerId: str = Field(min_length=1, max_length=64)
    consentGiven: bool
    measurements: Measurements = Measurements()
    answers: dict[str, bool] = {}
    aiObservations: list[AiObservation] = []
    speech: SpeechResult | None = None
    tasks: list[TaskResult] = []
    referralFacilityId: str | None = None


class PhotoCheckRequest(StrictModel):
    checkId: str
    childAgeMonths: float = Field(ge=0, le=228)
    imagesBase64: list[str] = Field(
        min_length=1, max_length=8, description="JPEG images; video frames for video checks"
    )


class DeviceReadingRequest(StrictModel):
    device: Device
    imageBase64: str
