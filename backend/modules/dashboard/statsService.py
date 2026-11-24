"""Running totals per block for the department dashboard. Only counts, never names or phone numbers."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from common.constants.tableKeys import STATS_PK, statsSk
from common.db.dynamoDbService import getDb

COUNTERS = (
    "screened",
    "flaggedDefects",
    "flaggedDeficiencies",
    "flaggedDiseases",
    "flaggedDevelopment",
    "referred",
    "reached",
    "homePlans",
    "improving",
    "alerts",
)


def flaggedCounter(domain: str) -> str:
    return f"flagged{domain[0].upper()}{domain[1:]}"


def recordEvent(child: dict[str, Any], **counters: int) -> None:
    labels = {key: child[key] for key in ("districtCode", "districtName", "blockCode", "blockName")}
    getDb().addCounters(STATS_PK, statsSk(child["districtCode"], child["blockCode"]), counters, labels)


def summary(districtCode: int | None = None) -> dict[str, Any]:
    """State view grouped by district, or one district grouped by block."""
    rows = getDb().query(STATS_PK, f"{districtCode}#" if districtCode else "", limit=2000)
    groupKey, nameKey = ("blockCode", "blockName") if districtCode else ("districtCode", "districtName")
    grouped: dict[int, dict[str, Any]] = defaultdict(lambda: dict.fromkeys(COUNTERS, 0))
    for row in rows:
        group = grouped[row[groupKey]]
        group["code"], group["name"] = row[groupKey], row[nameKey]
        for counter in COUNTERS:
            group[counter] += row.get(counter, 0)
    groups = sorted(grouped.values(), key=lambda group: group["name"])
    totals = {counter: sum(group[counter] for group in groups) for counter in COUNTERS}
    return {"level": "district" if districtCode else "state", "totals": totals, "rows": groups}
