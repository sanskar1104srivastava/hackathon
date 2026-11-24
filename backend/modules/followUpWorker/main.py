"""Lambda entry point for the daily EventBridge schedule."""

from __future__ import annotations

import logging
from typing import Any

from modules.demo import demoClock
from modules.followUpWorker.followUpService import runDaily

logging.basicConfig(level=logging.INFO)


def handler(event: dict[str, Any], context: Any) -> dict[str, int]:
    return runDaily(demoClock.now())
