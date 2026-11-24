from __future__ import annotations

from fastapi import APIRouter, Header, Request

from modules.abdmBridge.abdmService import handleWebhook

router = APIRouter(prefix="/v1/abdm", tags=["abdm"])


@router.post("/webhook", status_code=204)
async def receiveSahaiWebhook(request: Request, signature: str = Header("", alias="X-Sahai-Signature")) -> None:
    handleWebhook(await request.body(), signature)
