"""App time with a demo offset, so the two-week follow-up loop can be shown live. Always real time in prod."""

from __future__ import annotations

from datetime import datetime, timedelta

from common.config.settings import getSettings
from common.constants.tableKeys import DEMO_CLOCK_PK, DEMO_CLOCK_SK
from common.db.dynamoDbService import getDb
from common.utils.dateTimeUtils import utcNow


def offsetDays() -> int:
    if getSettings().appEnv == "prod":
        return 0
    item = getDb().getItem(DEMO_CLOCK_PK, DEMO_CLOCK_SK)
    return int(item.get("offsetDays", 0)) if item else 0


def now() -> datetime:
    return utcNow() + timedelta(days=offsetDays())


def advanceDays(days: int) -> int:
    getDb().addCounters(DEMO_CLOCK_PK, DEMO_CLOCK_SK, {"offsetDays": days})
    return offsetDays()
