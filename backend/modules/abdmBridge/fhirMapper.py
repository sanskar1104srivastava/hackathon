"""Builds the FHIR resource the Sahai data flow wraps into an ABDM WellnessRecord bundle for one screening."""

from __future__ import annotations

from typing import Any

from modules.screening.adviceTexts import DOMAIN_NAMES_HI

LOINC = "http://loinc.org"
UCUM = "http://unitsofmeasure.org"

MEASUREMENT_CODES = {
    "weightKg": ({"coding": [{"system": LOINC, "code": "29463-7", "display": "Body weight"}]}, "kg"),
    "heightCm": ({"coding": [{"system": LOINC, "code": "8302-2", "display": "Body height"}]}, "cm"),
    "muacCm": ({"text": "Mid-upper arm circumference"}, "cm"),
    "haemoglobinGdl": (
        {"coding": [{"system": LOINC, "code": "718-7", "display": "Hemoglobin [Mass/volume] in Blood"}]},
        "g/dL",
    ),
}


def screeningObservation(screening: dict[str, Any]) -> dict[str, Any]:
    components: list[dict[str, Any]] = []
    for field, value in screening["measurements"].items():
        if value is None:
            continue
        code, unit = MEASUREMENT_CODES[field]
        components.append({"code": code, "valueQuantity": {"value": value, "unit": unit, "system": UCUM, "code": unit}})
    for domain, result in screening["outcome"]["domains"].items():
        notes = "; ".join(item["noteEn"] for item in result["findings"]) or "no findings"
        components.append(
            {
                "code": {"text": f"RBSK {domain} ({DOMAIN_NAMES_HI[domain]})"},
                "valueString": f"{result['colour']}: {notes}",
            }
        )
    return {
        "resourceType": "Observation",
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "exam",
                        "display": "Exam",
                    }
                ]
            }
        ],
        "code": {"text": "RBSK child health screening across the 4Ds"},
        "effectiveDateTime": screening["screenedAt"],
        "component": components,
    }
