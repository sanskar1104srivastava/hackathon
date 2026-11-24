from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from common.constants.errorCodes import ErrorCode

logger = logging.getLogger(__name__)


class AppError(Exception):
    def __init__(self, statusCode: int, errorCode: ErrorCode, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.statusCode = statusCode
        self.errorCode = errorCode
        self.message = message
        self.details = details or {}


def addErrorHandlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handleAppError(_: Request, error: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=error.statusCode,
            content={"errorCode": error.errorCode, "message": error.message, "details": error.details},
        )

    @app.exception_handler(Exception)
    async def handleUnexpectedError(_: Request, error: Exception) -> JSONResponse:
        logger.exception("Unhandled error")
        return JSONResponse(
            status_code=500,
            content={"errorCode": ErrorCode.INTERNAL_ERROR, "message": "Internal server error", "details": {}},
        )
