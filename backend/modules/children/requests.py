from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from common.utils.dateTimeUtils import utcNow

MAX_AGE_DAYS = 19 * 365


class RegisterChildRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=80)
    sex: Literal["male", "female"]
    dateOfBirth: date
    guardianName: str = Field(min_length=1, max_length=80)
    guardianPhone: str = Field(pattern=r"^[6-9]\d{9}$", description="10-digit Indian mobile number")
    districtCode: int
    blockCode: int
    abhaAddress: str | None = Field(None, max_length=80)

    @field_validator("dateOfBirth")
    @classmethod
    def birthDateInRange(cls, value: date) -> date:
        ageDays = (utcNow().date() - value).days
        if not 0 <= ageDays <= MAX_AGE_DAYS:
            raise ValueError("date of birth must be in the past and within 18 years")
        return value


class LinkAbhaRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    abhaAddress: str = Field(min_length=3, max_length=80)
