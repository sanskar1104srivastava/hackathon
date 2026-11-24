from __future__ import annotations

from typing import Any

from common.constants.tableKeys import childPk
from common.db.dynamoDbService import getDb


def screeningSk(screenedAt: str, screeningId: str) -> str:
    return f"SCREENING#{screenedAt}#{screeningId}"


def saveScreening(screening: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """Stores a screening once. Re-sending the same screening from an offline phone returns the stored copy."""
    pk, sk = childPk(screening["childId"]), screeningSk(screening["screenedAt"], screening["screeningId"])
    isNew = getDb().putItem({**screening, "pk": pk, "sk": sk}, onlyIfNew=True)
    return (screening if isNew else getDb().getItem(pk, sk)), isNew
