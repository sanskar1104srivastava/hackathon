from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from modules.geo.geoService import Facility, facilitiesForDistrict, loadDistricts

router = APIRouter(prefix="/v1", tags=["geo"])


@router.get("/districts")
def listDistricts() -> list[dict[str, Any]]:
    return loadDistricts()


@router.get("/facilities")
def listFacilities(districtCode: int) -> list[Facility]:
    return facilitiesForDistrict(districtCode)
