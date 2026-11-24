from __future__ import annotations

import logging
from typing import Any

import httpx

from common.config.settings import getSettings

logger = logging.getLogger(__name__)


def toWhatsAppNumber(phone: str) -> str:
    digits = "".join(ch for ch in phone if ch.isdigit())
    return f"91{digits}" if len(digits) == 10 else digits


def sendText(phone: str, text: str) -> dict[str, Any] | None:
    """Sends a WhatsApp text through Meta Cloud API, same as the team's existing WhatsApp module.

    Free-form text only reaches a parent inside the 24-hour window after their last message; reminders outside
    that window need an approved template (`sendTemplate`).
    """
    return _post({"type": "text", "text": {"body": text, "preview_url": False}}, phone)


def sendTemplate(
    phone: str, templateName: str, bodyParams: list[str], languageCode: str = "hi"
) -> dict[str, Any] | None:
    component = {"type": "body", "parameters": [{"type": "text", "text": value} for value in bodyParams]}
    payload = {
        "type": "template",
        "template": {"name": templateName, "language": {"code": languageCode}, "components": [component]},
    }
    return _post(payload, phone)


def _post(payload: dict[str, Any], phone: str) -> dict[str, Any] | None:
    settings = getSettings()
    if not (settings.whatsAppAccessToken and settings.whatsAppPhoneNumberId):
        # ponytail: local and demo runs skip sending; set the WhatsApp secrets to go live.
        logger.info("WhatsApp not configured, skipped message type=%s", payload["type"])
        return None
    url = f"https://graph.facebook.com/{settings.whatsAppApiVersion}/{settings.whatsAppPhoneNumberId}/messages"
    response = httpx.post(
        url,
        json={"messaging_product": "whatsapp", "to": toWhatsAppNumber(phone), **payload},
        headers={"Authorization": f"Bearer {settings.whatsAppAccessToken}"},
        timeout=15,
    )
    if response.status_code >= 400:
        logger.error("WhatsApp send failed status=%s body=%s", response.status_code, response.text[:300])
        return None
    return response.json()
