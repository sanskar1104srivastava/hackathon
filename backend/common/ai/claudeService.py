from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any, Literal, TypeVar

import anthropic
from pydantic import BaseModel

from common.config.settings import getSettings
from common.constants.errorCodes import ErrorCode
from common.http.errorHandler import AppError

logger = logging.getLogger(__name__)

ResultModel = TypeVar("ResultModel", bound=BaseModel)
Effort = Literal["low", "medium", "high"]

# On a safety decline the API re-runs the same request on a fallback model it picks by refusal category.
SERVER_SIDE_FALLBACK_BETA = "server-side-fallback-2026-07-01"


def imageBlock(base64Jpeg: str) -> dict[str, Any]:
    return {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": base64Jpeg}}


class ClaudeService:
    """Structured-output calls to Claude. Every call returns a validated Pydantic model or raises AppError."""

    def __init__(self) -> None:
        settings = getSettings()
        self.client = anthropic.Anthropic(api_key=settings.anthropicApiKey or None)
        self.model = settings.claudeModel

    def askForJson(
        self,
        *,
        system: str,
        content: list[dict[str, Any]],
        resultType: type[ResultModel],
        effort: Effort = "medium",
    ) -> ResultModel:
        try:
            response = self.client.beta.messages.create(
                model=self.model,
                max_tokens=16000,
                system=system,
                messages=[{"role": "user", "content": content}],
                output_config={
                    "effort": effort,
                    "format": {"type": "json_schema", "schema": resultType.model_json_schema()},
                },
                betas=[SERVER_SIDE_FALLBACK_BETA],
                fallbacks="default",
            )
        except anthropic.RateLimitError as error:
            raise AppError(503, ErrorCode.AI_UNAVAILABLE, "AI service is busy, try again shortly") from error
        except anthropic.APIStatusError as error:
            logger.error("Claude request failed status=%s request_id=%s", error.status_code, error.request_id)
            raise AppError(502, ErrorCode.AI_UNAVAILABLE, "AI service request failed") from error
        except anthropic.APIConnectionError as error:
            raise AppError(503, ErrorCode.AI_UNAVAILABLE, "AI service is unreachable") from error

        if response.stop_reason == "refusal":
            raise AppError(422, ErrorCode.AI_UNAVAILABLE, "AI declined to assess this input")
        text = next(block.text for block in response.content if block.type == "text")
        return resultType.model_validate_json(text)


@lru_cache(maxsize=1)
def getClaude() -> ClaudeService:
    return ClaudeService()
