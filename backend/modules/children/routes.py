from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from modules.children import apiService
from modules.children.requests import LinkAbhaRequest, RegisterChildRequest

router = APIRouter(prefix="/v1", tags=["children"])


@router.post("/children", status_code=201)
def registerChild(request: RegisterChildRequest) -> dict[str, Any]:
    return apiService.registerChild(request)


@router.get("/children")
def listChildren(districtCode: int, blockCode: int | None = None) -> list[dict[str, Any]]:
    return apiService.listChildren(districtCode, blockCode)


@router.get("/children/{childId}")
def getChild(childId: str) -> dict[str, Any]:
    return apiService.getChildDetail(childId)


@router.put("/children/{childId}/abha")
def linkAbha(childId: str, request: LinkAbhaRequest) -> dict[str, Any]:
    return apiService.linkAbha(childId, request)


@router.get("/abha/search")
def searchAbha(mobile: str = Query(pattern=r"^[6-9]\d{9}$")) -> dict[str, Any]:
    return apiService.searchAbhaByMobile(mobile)
