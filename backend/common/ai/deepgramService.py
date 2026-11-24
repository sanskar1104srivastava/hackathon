from __future__ import annotations

import httpx

from common.config.settings import getSettings
from common.constants.errorCodes import ErrorCode
from common.http.errorHandler import AppError

DEEPGRAM_LISTEN_URL = "https://api.deepgram.com/v1/listen"


def transcribeHindi(audio: bytes, mimeType: str) -> str:
    """Speech to text for a short recording of a child, using the same Deepgram account as the calling system."""
    settings = getSettings()
    if not settings.deepgramApiKey:
        raise AppError(503, ErrorCode.AI_UNAVAILABLE, "Speech service is not configured")
    try:
        response = httpx.post(
            DEEPGRAM_LISTEN_URL,
            params={"model": settings.deepgramModel, "language": "hi"},
            headers={"Authorization": f"Token {settings.deepgramApiKey}", "Content-Type": mimeType},
            content=audio,
            timeout=30,
        )
        response.raise_for_status()
    except httpx.HTTPError as error:
        raise AppError(502, ErrorCode.AI_UNAVAILABLE, "Speech service request failed") from error
    return response.json()["results"]["channels"][0]["alternatives"][0]["transcript"]
