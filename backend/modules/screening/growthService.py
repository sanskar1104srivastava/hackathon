"""WHO growth z-scores from the official LMS tables.

Tables come from github.com/WorldHealthOrganization: `anthro` (Child Growth Standards, 0 to 5 years, by age in
days or by length/height) and `anthroplus` (Growth Reference 2007, 5 to 19 years, by age in months).
Method: the WHO LMS formula, with WHO's restricted adjustment beyond +/-3 SD for weight-based indicators.
"""

from __future__ import annotations

import bisect
import csv
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Literal

from common.utils.dateTimeUtils import DAYS_PER_MONTH

WHO_DIR = Path(__file__).resolve().parents[2] / "data" / "who"
STANDARDS_LAST_DAY = 1856
LENGTH_TABLE_LAST_DAY = 730
Sex = Literal["male", "female"]


@dataclass(frozen=True)
class Lms:
    l: float  # noqa: E741 - WHO's own name for the Box-Cox power
    m: float
    s: float

    def valueAtSd(self, sd: float) -> float:
        return self.m * (1 + self.l * self.s * sd) ** (1 / self.l)


@dataclass(frozen=True)
class GrowthZScores:
    weightForAge: float | None = None
    heightForAge: float | None = None
    weightForHeight: float | None = None
    bmiForAge: float | None = None


@cache
def loadTable(fileName: str) -> dict[int, tuple[list[float], list[Lms]]]:
    """Per WHO sex code (1 male, 2 female): the sorted x values (age or length) and their LMS rows."""
    rows: dict[int, list[tuple[float, Lms]]] = {1: [], 2: []}
    with (WHO_DIR / fileName).open(encoding="utf-8") as file:
        reader = csv.reader(file, delimiter="\t")
        next(reader)
        for row in reader:
            rows[int(row[0])].append((float(row[1]), Lms(float(row[2]), float(row[3]), float(row[4]))))
    return {sex: ([x for x, _ in data], [lms for _, lms in data]) for sex, data in rows.items()}


def lmsAt(fileName: str, sex: Sex, x: float) -> Lms | None:
    """LMS at `x`, linearly interpolated between table rows. None when `x` is outside the table."""
    xs, values = loadTable(fileName)[1 if sex == "male" else 2]
    if not xs[0] <= x <= xs[-1]:
        return None
    index = bisect.bisect_left(xs, x)
    if xs[index] == x:
        return values[index]
    low, high = values[index - 1], values[index]
    t = (x - xs[index - 1]) / (xs[index] - xs[index - 1])
    return Lms(low.l + t * (high.l - low.l), low.m + t * (high.m - low.m), low.s + t * (high.s - low.s))


def zScore(value: float, lms: Lms, restricted: bool) -> float:
    z = ((value / lms.m) ** lms.l - 1) / (lms.l * lms.s)
    if not restricted or -3 <= z <= 3:
        return z
    if z > 3:
        sd3 = lms.valueAtSd(3)
        return 3 + (value - sd3) / (sd3 - lms.valueAtSd(2))
    sd3 = lms.valueAtSd(-3)
    return -3 + (value - sd3) / (lms.valueAtSd(-2) - sd3)


def computeZScores(sex: Sex, ageDays: int, weightKg: float | None, heightCm: float | None) -> GrowthZScores:
    def score(fileName: str, x: float, value: float | None, restricted: bool = True) -> float | None:
        if value is None:
            return None
        lms = lmsAt(fileName, sex, x)
        return round(zScore(value, lms, restricted), 2) if lms else None

    if ageDays <= STANDARDS_LAST_DAY:
        # ponytail: assumes length is measured lying down under 2 years and standing after, as the field app asks.
        heightTable = "wflanthro.txt" if ageDays <= LENGTH_TABLE_LAST_DAY else "wfhanthro.txt"
        return GrowthZScores(
            weightForAge=score("weianthro.txt", ageDays, weightKg),
            heightForAge=score("lenanthro.txt", ageDays, heightCm, restricted=False),
            weightForHeight=score(heightTable, round(heightCm, 1), weightKg) if heightCm else None,
        )

    ageMonths = ageDays / DAYS_PER_MONTH
    bmi = weightKg / (heightCm / 100) ** 2 if weightKg and heightCm else None
    return GrowthZScores(
        weightForAge=score("wfawho2007.txt", ageMonths, weightKg),
        heightForAge=score("hfawho2007.txt", ageMonths, heightCm, restricted=False),
        bmiForAge=score("bfawho2007.txt", ageMonths, bmi),
    )
