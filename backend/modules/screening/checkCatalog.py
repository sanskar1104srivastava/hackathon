from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

Domain = Literal["defects", "deficiencies", "diseases", "development"]
Method = Literal["measurement", "photo", "video", "voice", "milestone", "mchat", "question", "task"]
Colour = Literal["green", "yellow", "red"]
Device = Literal["weighingScale", "muacTape", "haemoglobinMeter"]

DOMAINS: tuple[Domain, ...] = ("defects", "deficiencies", "diseases", "development")
CATALOG_PATH = Path(__file__).resolve().parents[2] / "data" / "rules" / "checkCatalog.json"


class Check(BaseModel):
    id: str
    domain: Domain
    rbskCondition: int | None = None
    method: Method
    minAgeMonths: float
    maxAgeMonths: float
    labelEn: str
    labelHi: str
    promptHi: str
    aiTargetEn: str = ""
    device: Device | None = None
    dueByMonths: float | None = None
    riskAnswer: bool | None = None
    flagColour: Colour = "red"

    def appliesAt(self, ageMonths: float) -> bool:
        return self.minAgeMonths <= ageMonths < self.maxAgeMonths + 1


class PictureCard(BaseModel):
    id: str
    symbol: str
    wordHi: str
    accepted: list[str]


class Catalog(BaseModel):
    version: str
    checks: list[Check]
    pictureCards: list[PictureCard]


@lru_cache(maxsize=1)
def getCatalog() -> Catalog:
    return Catalog.model_validate_json(CATALOG_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def checksById() -> dict[str, Check]:
    return {check.id: check for check in getCatalog().checks}


def checksForAge(ageMonths: float) -> list[Check]:
    return [check for check in getCatalog().checks if check.appliesAt(ageMonths)]
