from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Medicine(StrictModel):
    name: str = Field(min_length=1, max_length=80)
    scheduleHi: str = Field(min_length=1, max_length=120, description="When to give it, in Hindi")


class CarePlan(StrictModel):
    careInstructionsHi: str = Field("", max_length=600)
    medicines: list[Medicine] = []
    checkupDates: list[date] = []
    therapyDates: list[date] = []


class DiagnosisRequest(StrictModel):
    doctorName: str = Field(min_length=1, max_length=80)
    diagnosisText: str = Field(min_length=1, max_length=500)
    carePlan: CarePlan = CarePlan()


class RecordsRequest(StrictModel):
    requesterName: str = Field(min_length=1, max_length=80)
    requesterIdType: Literal["HPR", "REGNO"] = "HPR"
    requesterId: str = Field(min_length=1, max_length=64)
