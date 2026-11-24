from __future__ import annotations

from datetime import UTC, date, datetime

DAYS_PER_MONTH = 30.4375


def utcNow() -> datetime:
    return datetime.now(UTC)


def nowIso() -> str:
    return utcNow().isoformat(timespec="seconds")


def ageInDays(dateOfBirth: date, onDate: date) -> int:
    return (onDate - dateOfBirth).days


def ageInMonths(dateOfBirth: date, onDate: date) -> float:
    return ageInDays(dateOfBirth, onDate) / DAYS_PER_MONTH
