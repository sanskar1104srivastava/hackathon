from __future__ import annotations

import logging
from collections.abc import Iterable

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from common.config.settings import getSettings
from common.http.errorHandler import addErrorHandlers


def createFastApiApp(title: str, routers: Iterable[APIRouter]) -> FastAPI:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    app = FastAPI(title=title, version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=getSettings().corsOrigins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    addErrorHandlers(app)

    @app.get("/v1/health", include_in_schema=False)
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": title}

    for router in routers:
        app.include_router(router)
    return app
