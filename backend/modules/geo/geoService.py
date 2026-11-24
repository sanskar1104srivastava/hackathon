"""UP districts and blocks (from the Local Government Directory) and the referral facilities in each district."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel

from common.constants.errorCodes import ErrorCode
from common.http.errorHandler import AppError

GEO_PATH = Path(__file__).resolve().parents[2] / "data" / "geo" / "upDistricts.json"

# Districts whose DEIC is named in a UP Legislative Council reply (it lists 12 operating DEICs; the rest of the
# reply was not readable). Other districts refer to the district hospital.
# ponytail: seeded list; replace with an HFR facility search once the Sahai M4 (HFR) Lambda is live.
KNOWN_DEIC_DISTRICTS = {"aligarh", "ghaziabad", "gautam buddha nagar"}


class Facility(BaseModel):
    facilityId: str
    name: str
    type: Literal["deic", "districtHospital"]
    districtCode: int
    districtName: str
    source: Literal["seed", "hfr"] = "seed"


@lru_cache(maxsize=1)
def loadDistricts() -> list[dict[str, Any]]:
    return json.loads(GEO_PATH.read_text(encoding="utf-8"))["districts"]


@lru_cache(maxsize=1)
def districtsByCode() -> dict[int, dict[str, Any]]:
    return {district["districtCode"]: district for district in loadDistricts()}


def resolveArea(districtCode: int, blockCode: int) -> tuple[str, str]:
    """Returns (districtName, blockName) or raises when the codes are not a UP district and one of its blocks."""
    district = districtsByCode().get(districtCode)
    block = next((b for b in district["blocks"] if b["blockCode"] == blockCode), None) if district else None
    if block is None:
        raise AppError(400, ErrorCode.INVALID_REQUEST, "Unknown district or block code")
    return district["districtName"], block["blockName"]


def facilitiesForDistrict(districtCode: int) -> list[Facility]:
    district = districtsByCode().get(districtCode)
    if district is None:
        raise AppError(400, ErrorCode.INVALID_REQUEST, "Unknown district code")
    name = district["districtName"]
    facilities = [
        Facility(
            facilityId=f"DH-{districtCode}",
            name=f"District Hospital, {name}",
            type="districtHospital",
            districtCode=districtCode,
            districtName=name,
        )
    ]
    if name.lower() in KNOWN_DEIC_DISTRICTS:
        facilities.insert(
            0,
            Facility(
                facilityId=f"DEIC-{districtCode}",
                name=f"DEIC, District Hospital {name}",
                type="deic",
                districtCode=districtCode,
                districtName=name,
            ),
        )
    return facilities


def facilityById(facilityId: str) -> Facility:
    try:
        districtCode = int(facilityId.split("-", 1)[1])
        return next(f for f in facilitiesForDistrict(districtCode) if f.facilityId == facilityId)
    except (IndexError, ValueError, StopIteration, AppError) as error:
        raise AppError(404, ErrorCode.NOT_FOUND, "Facility not found") from error
