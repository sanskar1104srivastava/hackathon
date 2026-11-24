from __future__ import annotations

import secrets
import uuid
from typing import Any

from common.abdm.sahaiClient import getSahai
from common.constants.tableKeys import ACTIVE_PLAN_SK
from common.utils.dateTimeUtils import nowIso
from modules.children import dbService
from modules.children.requests import LinkAbhaRequest, RegisterChildRequest
from modules.geo.geoService import resolveArea


def registerChild(request: RegisterChildRequest) -> dict[str, Any]:
    districtName, blockName = resolveArea(request.districtCode, request.blockCode)
    child = {
        **request.model_dump(mode="json"),
        "childId": uuid.uuid4().hex,
        "districtName": districtName,
        "blockName": blockName,
        "parentAccessToken": secrets.token_urlsafe(16),
        "createdAt": nowIso(),
    }
    dbService.saveChild(child)
    return withParentLink(child)


def withParentLink(child: dict[str, Any]) -> dict[str, Any]:
    """Public child view plus the link the parent opens from the QR code."""
    return {
        **dbService.publicView(child),
        "parentLinkPath": f"/parent/{child['childId']}?token={child['parentAccessToken']}",
    }


def listChildren(districtCode: int, blockCode: int | None) -> list[dict[str, Any]]:
    return [dbService.publicView(child) for child in dbService.listChildrenInArea(districtCode, blockCode)]


def getChildDetail(childId: str) -> dict[str, Any]:
    child = dbService.getChild(childId)
    records = dbService.listChildRecords
    return {
        "child": withParentLink(child),
        "screenings": [dbService.publicView(item) for item in records(childId, "SCREENING#", limit=10)],
        "referrals": [dbService.publicView(item) for item in records(childId, "REFERRAL#")],
        "alerts": [dbService.publicView(item) for item in records(childId, "ALERT#", limit=10)],
        "homePlan": next((dbService.publicView(item) for item in records(childId, ACTIVE_PLAN_SK, limit=1)), None),
    }


def linkAbha(childId: str, request: LinkAbhaRequest) -> dict[str, Any]:
    dbService.getChild(childId)
    return dbService.publicView(dbService.updateChild(childId, {"abhaAddress": request.abhaAddress}))


def searchAbhaByMobile(mobile: str) -> dict[str, Any]:
    return getSahai().searchAbhaByMobile(mobile)
