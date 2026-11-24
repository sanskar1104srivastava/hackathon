"""AI evidence for the rules engine: visible signs in photos and video frames, device readings, and speech."""

from __future__ import annotations

import base64
import binascii
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from common.ai.claudeService import getClaude, imageBlock
from common.ai.deepgramService import transcribeHindi
from common.constants.errorCodes import ErrorCode
from common.http.errorHandler import AppError
from modules.screening.checkCatalog import checksById, getCatalog
from modules.screening.requests import AiOutcome, DeviceReadingRequest, PhotoCheckRequest

SIGN_CHECK_SYSTEM = (
    "You assist frontline health workers in India's child health screening programme (RBSK). You never diagnose. "
    "For each request you decide only whether one named visible sign is present in the images.\n"
    "- outcome 'seen': the sign is clearly visible.\n"
    "- outcome 'notSeen': the relevant body part is clearly visible and the sign is absent.\n"
    "- outcome 'unsure': the image is blurry, dark or cropped, the body part is not visible, or you are not "
    "confident either way. When in doubt, choose 'unsure', because the child will then see a doctor.\n"
    "Write reasonHi as one short sentence in simple Hindi that a health worker can read aloud to a parent, "
    "describing what is visible, without naming a disease."
)

DEVICE_PROMPTS = {
    "weighingScale": ("the weight shown on this weighing scale display", "kg"),
    "muacTape": ("the mid-upper arm circumference shown where this MUAC tape overlaps, in centimetres", "cm"),
    "haemoglobinMeter": ("the haemoglobin value shown on this haemoglobin meter display", "g/dL"),
}


class SignCheckResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    outcome: AiOutcome
    reasonHi: str
    imageQualityOk: bool


class DeviceReadingResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    readable: bool
    value: float | None
    unit: Literal["kg", "cm", "g/dL"]


class SpeechCheckRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    audioBase64: str
    mimeType: Literal["audio/webm", "audio/ogg", "audio/mp4", "audio/wav", "audio/mpeg"]
    cardIds: list[str] = Field(min_length=1, max_length=20)


class SpeechCheckResult(BaseModel):
    transcript: str
    namedCardIds: list[str]
    shownCount: int
    namedCount: int


def checkSign(request: PhotoCheckRequest) -> SignCheckResult:
    check = checksById().get(request.checkId)
    if check is None or check.method not in ("photo", "video"):
        raise AppError(400, ErrorCode.INVALID_REQUEST, "Not a photo or video check")
    frames = " These images are frames from one short video, in time order." if check.method == "video" else ""
    content = [imageBlock(image) for image in request.imagesBase64]
    content.append(
        {
            "type": "text",
            "text": (
                f"Child's age: {request.childAgeMonths:.0f} months.{frames}\nSign to look for: {check.aiTargetEn}."
            ),
        }
    )
    return getClaude().askForJson(system=SIGN_CHECK_SYSTEM, content=content, resultType=SignCheckResult)


def readDevice(request: DeviceReadingRequest) -> DeviceReadingResult:
    target, unit = DEVICE_PROMPTS[request.device]
    instruction = (
        f"Read {target}. Return the number exactly as displayed, with unit {unit}. "
        "If the display or tape marking is not clearly readable, return readable=false and value=null."
    )
    content = [imageBlock(request.imageBase64), {"type": "text", "text": instruction}]
    return getClaude().askForJson(
        system="You read numbers from photos of medical measuring devices.",
        content=content,
        resultType=DeviceReadingResult,
        effort="low",
    )


def checkSpeech(request: SpeechCheckRequest) -> SpeechCheckResult:
    try:
        audio = base64.b64decode(request.audioBase64, validate=True)
    except binascii.Error as error:
        raise AppError(400, ErrorCode.INVALID_REQUEST, "Audio is not valid base64") from error
    cards = {card.id: card for card in getCatalog().pictureCards}
    shown = [cards[cardId] for cardId in request.cardIds if cardId in cards]
    if not shown:
        raise AppError(400, ErrorCode.INVALID_REQUEST, "Unknown picture cards")
    transcript = transcribeHindi(audio, request.mimeType)
    named = [card.id for card in shown if any(word in transcript for word in card.accepted)]
    return SpeechCheckResult(transcript=transcript, namedCardIds=named, shownCount=len(shown), namedCount=len(named))
