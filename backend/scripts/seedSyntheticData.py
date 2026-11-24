"""Fills the table with synthetic children so the dashboard shows a realistic Uttar Pradesh pattern.

Every record is made up; the brief allows synthetic child data only. Growth and haemoglobin are drawn so the
state-level rates land near NFHS-5 Uttar Pradesh for under-fives (about 40% stunted, about 17% wasted, 66.4%
anaemic at 6 to 59 months). Per-district shifts are random, not real district values.

Usage (needs AWS access to the dev table):
    uv run python -m scripts.seedSyntheticData --per-district 10
"""

from __future__ import annotations

import argparse
import random
import uuid
from datetime import UTC, date, datetime, timedelta

from common.messaging import whatsAppService
from common.utils.dateTimeUtils import DAYS_PER_MONTH
from modules.children.apiService import registerChild
from modules.children.requests import RegisterChildRequest
from modules.geo.geoService import loadDistricts
from modules.referrals.apiService import markArrived
from modules.screening.apiService import submitScreening
from modules.screening.checkCatalog import checksForAge
from modules.screening.growthService import lmsAt
from modules.screening.requests import Measurements, ScreeningInput

FIRST_NAMES = [
    "Aarav",
    "Ananya",
    "Arjun",
    "Diya",
    "Ishaan",
    "Kavya",
    "Rohan",
    "Saanvi",
    "Aditya",
    "Pooja",
    "Karan",
    "Neha",
    "Rahul",
    "Sneha",
    "Vivaan",
    "Priya",
    "Ayaan",
    "Meera",
    "Dev",
    "Zoya",
]
DELAYED_CHILD_RATE = 0.08
REFERRAL_ARRIVAL_RATE = 0.6


def clampedLms(fileName: str, sex: str, x: float, low: float, high: float):
    return lmsAt(fileName, sex, min(max(x, low), high))


def syntheticMeasurements(rng: random.Random, sex: str, ageDays: int, districtShift: float) -> Measurements:
    heightLms = lmsAt("lenanthro.txt", sex, ageDays)
    heightCm = round(heightLms.valueAtSd(rng.gauss(-1.55 + districtShift, 1.1)), 1)
    weightTable, low, high = ("wflanthro.txt", 45, 110) if ageDays <= 730 else ("wfhanthro.txt", 65, 120)
    weightForHeightZ = rng.gauss(-0.95 + districtShift / 2, 1.0)
    weightKg = round(clampedLms(weightTable, sex, round(heightCm, 1), low, high).valueAtSd(weightForHeightZ), 1)
    return Measurements(
        weightKg=weightKg,
        heightCm=heightCm,
        muacCm=round(13.8 + 0.9 * weightForHeightZ + rng.gauss(0, 0.4), 1),  # ponytail: rough link to wasting
        haemoglobinGdl=round(min(max(rng.gauss(10.3, 1.4), 4), 15), 1),
    )


def seedChild(rng: random.Random, district: dict, districtShift: float, today: date) -> None:
    sex = rng.choice(["male", "female"])
    screenedOn = today - timedelta(days=rng.randint(0, 120))
    ageDays = int(rng.uniform(6, 59) * DAYS_PER_MONTH)
    block = rng.choice(district["blocks"])
    child = registerChild(
        RegisterChildRequest(
            name=rng.choice(FIRST_NAMES),
            sex=sex,
            dateOfBirth=screenedOn - timedelta(days=ageDays),
            guardianName="Synthetic guardian",
            guardianPhone=f"60{rng.randint(0, 99_999_999):08d}",
            districtCode=district["districtCode"],
            blockCode=block["blockCode"],
        )
    )
    milestones = [c.id for c in checksForAge(ageDays / DAYS_PER_MONTH) if c.method == "milestone"]
    answers = dict.fromkeys(milestones, True)
    if milestones and rng.random() < DELAYED_CHILD_RATE:
        for checkId in rng.sample(milestones, k=1 if rng.random() < 0.7 else min(2, len(milestones))):
            answers[checkId] = False
    result = submitScreening(
        child["childId"],
        ScreeningInput(
            screeningId=uuid.uuid4().hex,
            setting="anganwadi",
            workerId="synthetic-seed",
            consentGiven=True,
            screenedAt=datetime.combine(screenedOn, datetime.min.time(), UTC),
            measurements=syntheticMeasurements(rng, sex, ageDays, districtShift),
            answers=answers,
        ),
    )
    referral = result.get("referral")
    if referral and rng.random() < REFERRAL_ARRIVAL_RATE:
        markArrived(child["childId"], referral["referralId"])


def main(perDistrict: int, districtLimit: int | None, seed: int) -> int:
    # Synthetic phone numbers must never be messaged.
    whatsAppService.sendText = lambda *args, **kwargs: None
    rng, today = random.Random(seed), date.today()
    districts = loadDistricts()[:districtLimit]
    for district in districts:
        shift = rng.gauss(0, 0.35)
        for _ in range(perDistrict):
            seedChild(rng, district, shift, today)
    return len(districts) * perDistrict


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--per-district", type=int, default=10)
    parser.add_argument("--districts", type=int, default=None, help="Seed only the first N districts")
    parser.add_argument("--seed", type=int, default=42)
    arguments = parser.parse_args()
    print(f"Seeded {main(arguments.per_district, arguments.districts, arguments.seed)} synthetic children")
