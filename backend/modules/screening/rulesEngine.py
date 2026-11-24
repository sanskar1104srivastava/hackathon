"""Turns one screening into a green, yellow or red result for each of the four Ds.

Rules decide the colour; AI only supplies evidence (`aiObservations`). An AI answer of "unsure" refers the child.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

from pydantic import BaseModel

from common.utils.dateTimeUtils import DAYS_PER_MONTH
from modules.screening.adviceTexts import ADVICE_HI
from modules.screening.checkCatalog import DOMAINS, Check, Colour, Domain, checksById, checksForAge
from modules.screening.growthService import Sex, computeZScores
from modules.screening.requests import Measurements, ScreeningInput

COLOUR_RANK: dict[Colour, int] = {"green": 0, "yellow": 1, "red": 2}
MCHAT_MEDIUM_RISK, MCHAT_HIGH_RISK = 3, 8
NextStep = Literal["referral", "homePlan"]


class Finding(BaseModel):
    checkId: str
    domain: Domain
    colour: Colour
    noteHi: str
    noteEn: str


class DomainResult(BaseModel):
    colour: Colour
    findings: list[Finding]
    adviceHi: str


class ScreeningOutcome(BaseModel):
    overall: Colour
    domains: dict[Domain, DomainResult]
    growth: dict[str, float | None]
    nextSteps: list[NextStep]


@dataclass(frozen=True)
class ChildFacts:
    sex: Sex
    ageDays: int

    @property
    def ageMonths(self) -> float:
        return self.ageDays / DAYS_PER_MONTH


def worstColour(colours: list[Colour]) -> Colour:
    return max(colours, key=COLOUR_RANK.__getitem__, default="green")


def finding(check: Check, colour: Colour, noteHi: str, noteEn: str) -> Finding:
    return Finding(checkId=check.id, domain=check.domain, colour=colour, noteHi=noteHi, noteEn=noteEn)


def growthFindings(child: ChildFacts, measurements: Measurements) -> tuple[list[Finding], dict[str, float | None]]:
    zScores = computeZScores(child.sex, child.ageDays, measurements.weightKg, measurements.heightCm)
    weightCheck, heightCheck = checksById()["weight"], checksById()["height"]
    findings: list[Finding] = []

    thinness = zScores.weightForHeight if zScores.weightForHeight is not None else zScores.bmiForAge
    if thinness is not None and thinness < -3:
        findings.append(
            finding(
                weightCheck,
                "red",
                f"लंबाई के हिसाब से वज़न बहुत कम है (z {thinness})",
                f"Severe wasting or thinness, z={thinness}",
            )
        )
    elif thinness is not None and thinness < -2:
        findings.append(
            finding(
                weightCheck, "yellow", f"लंबाई के हिसाब से वज़न कम है (z {thinness})", f"Wasting or thinness, z={thinness}"
            )
        )
    elif thinness is None and zScores.weightForAge is not None and zScores.weightForAge < -2:
        findings.append(
            finding(
                weightCheck,
                "yellow",
                f"उम्र के हिसाब से वज़न कम है (z {zScores.weightForAge})",
                f"Underweight, z={zScores.weightForAge}",
            )
        )

    if zScores.heightForAge is not None and zScores.heightForAge < -2:
        findings.append(
            finding(
                heightCheck,
                "yellow",
                f"उम्र के हिसाब से लंबाई कम है (z {zScores.heightForAge})",
                f"Stunting, z={zScores.heightForAge}",
            )
        )
    return findings, asdict(zScores)


def muacFindings(child: ChildFacts, muacCm: float | None) -> list[Finding]:
    check = checksById()["muac"]
    if muacCm is None or not check.appliesAt(child.ageMonths):
        return []
    if muacCm < 11.5:
        return [finding(check, "red", f"बाँह का घेरा {muacCm} सेमी है, बहुत कम", f"MUAC {muacCm} cm, below 11.5")]
    if muacCm < 12.5:
        return [finding(check, "yellow", f"बाँह का घेरा {muacCm} सेमी है, कम", f"MUAC {muacCm} cm, 11.5 to 12.4")]
    return []


def anaemiaCutoffs(ageMonths: float, sex: Sex) -> tuple[float, float] | None:
    """WHO 2011 haemoglobin cut-offs as (anaemia below, severe anaemia below) in g/dL."""
    if ageMonths < 6:
        return None
    if ageMonths < 60:
        return 11.0, 7.0
    if ageMonths < 144:
        return 11.5, 8.0
    if ageMonths < 180 or sex == "female":
        return 12.0, 8.0
    return 13.0, 8.0


def haemoglobinFindings(child: ChildFacts, haemoglobinGdl: float | None) -> list[Finding]:
    cutoffs = anaemiaCutoffs(child.ageMonths, child.sex)
    if haemoglobinGdl is None or cutoffs is None:
        return []
    anaemiaBelow, severeBelow = cutoffs
    check = checksById()["haemoglobin"]
    if haemoglobinGdl < severeBelow:
        return [
            finding(
                check,
                "red",
                f"हीमोग्लोबिन {haemoglobinGdl} है, ख़ून की बहुत ज़्यादा कमी",
                f"Severe anaemia, Hb {haemoglobinGdl} g/dL",
            )
        ]
    if haemoglobinGdl < anaemiaBelow:
        return [
            finding(check, "yellow", f"हीमोग्लोबिन {haemoglobinGdl} है, ख़ून की कमी", f"Anaemia, Hb {haemoglobinGdl} g/dL")
        ]
    return []


def aiFindings(applicable: dict[str, Check], submission: ScreeningInput) -> list[Finding]:
    findings = []
    for observation in submission.aiObservations:
        check = applicable.get(observation.checkId)
        if check is None or check.method not in ("photo", "video") or observation.outcome == "notSeen":
            continue
        if observation.outcome == "seen":
            findings.append(
                finding(
                    check,
                    check.flagColour,
                    f"{check.labelHi}: फ़ोटो या वीडियो में निशान दिखे",
                    f"{check.labelEn}: sign seen",
                )
            )
        else:
            findings.append(
                finding(
                    check,
                    "red",
                    f"{check.labelHi}: पक्का नहीं कह सकते, डॉक्टर को दिखाएँ",
                    f"{check.labelEn}: AI unsure, refer",
                )
            )
    return findings


def questionAndTaskFindings(applicable: dict[str, Check], submission: ScreeningInput) -> list[Finding]:
    findings = []
    for checkId, answer in submission.answers.items():
        check = applicable.get(checkId)
        if check and check.method == "question" and answer:
            findings.append(
                finding(check, check.flagColour, f"{check.labelHi}: परिवार ने बताया", f"{check.labelEn}: reported")
            )
    for task in submission.tasks:
        check = applicable.get(task.checkId)
        if check and check.method == "task" and not task.passed:
            findings.append(
                finding(check, check.flagColour, f"{check.labelHi}: जाँच में ठीक नहीं रहा", f"{check.labelEn}: not passed")
            )
    return findings


def milestoneFindings(applicable: dict[str, Check], submission: ScreeningInput) -> list[Finding]:
    """One delayed milestone is watched at home; two or more are referred (the TDSC community rule)."""
    delayed = [
        check
        for checkId, achieved in submission.answers.items()
        if (check := applicable.get(checkId)) and check.method == "milestone" and not achieved
    ]
    colour: Colour = "red" if len(delayed) >= 2 else "yellow"
    return [
        finding(
            check,
            colour,
            f"{check.labelHi}: उम्र के हिसाब से अभी नहीं करता",
            f"{check.labelEn}: not yet, due by {check.dueByMonths} months",
        )
        for check in delayed
    ]


def mchatFindings(applicable: dict[str, Check], submission: ScreeningInput) -> list[Finding]:
    items = [
        (check, answer)
        for checkId, answer in submission.answers.items()
        if (check := applicable.get(checkId)) and check.method == "mchat"
    ]
    score = sum(1 for check, answer in items if answer == check.riskAnswer)
    if score < MCHAT_MEDIUM_RISK:
        return []
    colour: Colour = "red" if score >= MCHAT_HIGH_RISK else "yellow"
    firstItem = items[0][0]
    return [
        Finding(
            checkId="mchat",
            domain=firstItem.domain,
            colour=colour,
            noteHi=f"व्यवहार और बातचीत के सवालों में {score} बातें ध्यान देने वाली",
            noteEn=f"M-CHAT-R score {score}",
        )
    ]


def expectedNamedShare(ageMonths: float) -> float:
    """Proof-of-concept thresholds for the picture-naming task; tune with the doctor panel."""
    if ageMonths < 36:
        return 0.3
    if ageMonths < 48:
        return 0.6
    return 0.8


def speechFindings(child: ChildFacts, applicable: dict[str, Check], submission: ScreeningInput) -> list[Finding]:
    check, speech = applicable.get("pictureNaming"), submission.speech
    if check is None or speech is None:
        return []
    if speech.namedCount == 0:
        return [finding(check, "red", "चित्र देखकर एक भी नाम नहीं बोला", "Named no pictures")]
    expected = round(expectedNamedShare(child.ageMonths) * speech.shownCount)
    if speech.namedCount < expected:
        return [
            finding(
                check,
                "yellow",
                f"{speech.shownCount} में से {speech.namedCount} चित्रों के नाम बोले",
                f"Named {speech.namedCount} of {speech.shownCount}, expected {expected}",
            )
        ]
    return []


def evaluateScreening(child: ChildFacts, submission: ScreeningInput) -> ScreeningOutcome:
    applicable = {check.id: check for check in checksForAge(child.ageMonths)}
    growth, zScores = growthFindings(child, submission.measurements)
    findings = [
        *growth,
        *muacFindings(child, submission.measurements.muacCm),
        *haemoglobinFindings(child, submission.measurements.haemoglobinGdl),
        *aiFindings(applicable, submission),
        *questionAndTaskFindings(applicable, submission),
        *milestoneFindings(applicable, submission),
        *mchatFindings(applicable, submission),
        *speechFindings(child, applicable, submission),
    ]

    domains: dict[Domain, DomainResult] = {}
    for domain in DOMAINS:
        domainFindings = [item for item in findings if item.domain == domain]
        colour = worstColour([item.colour for item in domainFindings])
        domains[domain] = DomainResult(colour=colour, findings=domainFindings, adviceHi=ADVICE_HI[colour])

    colours = [result.colour for result in domains.values()]
    nextSteps: list[NextStep] = []
    if "red" in colours:
        nextSteps.append("referral")
    if "yellow" in colours:
        nextSteps.append("homePlan")
    return ScreeningOutcome(overall=worstColour(colours), domains=domains, growth=zScores, nextSteps=nextSteps)
