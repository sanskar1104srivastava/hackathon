from __future__ import annotations

import hashlib
import hmac
from functools import lru_cache
from typing import Any

import httpx

from common.config.settings import getSettings
from common.constants.errorCodes import ErrorCode
from common.http.errorHandler import AppError

CARE_MANAGEMENT_PURPOSE = {"text": "Care Management", "code": "CAREMGT", "refUri": "www.abdm.gov.in"}


class SahaiClient:
    """Client for the Sahai production-backend, which runs ABDM M1 (ABHA), M2 (HIP) and M3 (HIU) on Lambda.

    This app is one Sahai customer: it calls `/v1/...` with its API key and receives ABDM events on its webhook.
    """

    def __init__(self) -> None:
        settings = getSettings()
        self.hipId = settings.abdmHipId
        self.hiuId = settings.abdmHiuId
        self.isConfigured = bool(settings.sahaiBaseUrl and settings.sahaiApiKey)
        self.http = httpx.Client(
            base_url=settings.sahaiBaseUrl,
            headers={"Authorization": f"Bearer {settings.sahaiApiKey}"},
            timeout=20,
        )

    def searchAbhaByMobile(self, mobile: str) -> dict[str, Any]:
        return self._send("POST", "/v1/abha/search/by-mobile", {"mobile": mobile})

    def requestLinkToken(
        self, *, abhaAddress: str, patientReference: str, name: str, gender: str, yearOfBirth: int, idempotencyKey: str
    ) -> dict[str, Any]:
        body = {
            "hipId": self.hipId,
            "abhaAddress": abhaAddress,
            "patientReference": patientReference,
            "name": name,
            "gender": gender,
            "yearOfBirth": yearOfBirth,
            "purpose": "LINK_CARE_CONTEXT",
        }
        return self._send("POST", "/v1/link-token", body, idempotencyKey)

    def linkCareContexts(
        self,
        *,
        abhaAddress: str,
        patientReference: str,
        linkToken: str,
        careContexts: list[dict[str, Any]],
        idempotencyKey: str,
    ) -> dict[str, Any]:
        body = {
            "hipId": self.hipId,
            "abhaAddress": abhaAddress,
            "patientReference": patientReference,
            "linkToken": linkToken,
            "careContexts": careContexts,
        }
        return self._send("POST", "/v1/care-contexts/link", body, idempotencyKey)

    def requestConsent(
        self,
        *,
        abhaAddress: str,
        patientReference: str,
        requester: dict[str, str],
        hiTypes: list[str],
        fromIso: str,
        toIso: str,
        idempotencyKey: str,
    ) -> dict[str, Any]:
        body = {
            "abhaAddress": abhaAddress,
            "patientReference": patientReference,
            "hiuId": self.hiuId,
            "purpose": CARE_MANAGEMENT_PURPOSE,
            "requester": requester,
            "hiTypes": hiTypes,
            "dateRange": {"from": fromIso, "to": toIso},
        }
        return self._send("POST", "/v1/consents", body, idempotencyKey)

    def requestHealthInformation(
        self, *, consentId: str, fromIso: str, toIso: str, idempotencyKey: str
    ) -> dict[str, Any]:
        body = {"consentId": consentId, "hiuId": self.hiuId, "dateRange": {"from": fromIso, "to": toIso}}
        return self._send("POST", "/v1/health-information", body, idempotencyKey)

    def getStatus(self, trackingId: str) -> dict[str, Any]:
        return self._send("GET", f"/v1/status/{trackingId}")

    def getDecryptedRecords(self, trackingId: str) -> dict[str, Any]:
        return self._send("GET", f"/v1/health-records/{trackingId}/decrypt")

    def _send(
        self, method: str, path: str, body: dict[str, Any] | None = None, idempotencyKey: str | None = None
    ) -> dict[str, Any]:
        if not self.isConfigured:
            raise AppError(503, ErrorCode.UPSTREAM_ERROR, "ABDM bridge is not configured")
        headers = {"Idempotency-Key": idempotencyKey} if idempotencyKey else {}
        try:
            response = self.http.request(method, path, json=body, headers=headers)
        except httpx.HTTPError as error:
            raise AppError(502, ErrorCode.UPSTREAM_ERROR, "ABDM bridge is unreachable") from error
        if response.status_code >= 400:
            raise AppError(
                424,
                ErrorCode.UPSTREAM_ERROR,
                "ABDM bridge rejected the request",
                {"status": response.status_code, "body": response.text[:500]},
            )
        return response.json() if response.content else {}


def isValidSahaiSignature(rawBody: bytes, signatureHeader: str, secret: str) -> bool:
    """Sahai signs webhooks as `sha256=<hex HMAC-SHA256 of the raw body>` with our webhook secret."""
    if not secret or not signatureHeader:
        return False
    expected = "sha256=" + hmac.new(secret.encode(), rawBody, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signatureHeader)


@lru_cache(maxsize=1)
def getSahai() -> SahaiClient:
    return SahaiClient()
