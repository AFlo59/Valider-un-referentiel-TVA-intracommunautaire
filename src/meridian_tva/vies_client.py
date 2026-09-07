"""Client VIES (REST documenté : POST /check-vat-number) et interprétation de ses réponses.

Ce que le service peut répondre, tout en HTTP 200 :
- {"valid": true, "name": ..., "address": ..., "requestIdentifier": ...}    -> valide (définitif)
- {"valid": false, ...}                                                      -> invalide (définitif)
- {"actionSucceed": false, "errorWrappers": [{"error": "MS_UNAVAILABLE"}]}   -> indéterminé (transitoire, à réessayer)
  Autres codes : SERVICE_UNAVAILABLE, TIMEOUT, MS_MAX_CONCURRENT_REQ(_TIME), GLOBAL_MAX_CONCURRENT_REQ(_TIME),
  INVALID_INPUT, INVALID_REQUESTER_INFO, VAT_BLOCKED, IP_BLOCKED.
Et ce qu'il peut ne pas répondre : timeout réseau, HTTP 5xx, HTML d'erreur au lieu de JSON.

Règle absolue : une indisponibilité n'est JAMAIS un verdict « invalide ». Le verdict ne dérive jamais d'un seul champ.
Le lien GET de l'interface web (rest-api/ms/{pays}/vat/{numero}) renvoie « isValid: false » avec un userError quand
l'État membre limite le débit : il n'est pas utilisé.
"""

from __future__ import annotations

import logging
import time
from dataclasses import asdict, dataclass

import requests

from .config import Settings

log = logging.getLogger(__name__)

TRANSIENT = {
    "MS_UNAVAILABLE", "SERVICE_UNAVAILABLE", "TIMEOUT", "MS_MAX_CONCURRENT_REQ", "MS_MAX_CONCURRENT_REQ_TIME",
    "GLOBAL_MAX_CONCURRENT_REQ", "GLOBAL_MAX_CONCURRENT_REQ_TIME", "IO_ERROR", "TECHNICAL_ERROR",
}
BLOCKING = {"IP_BLOCKED", "VAT_BLOCKED", "INVALID_REQUESTER_INFO"}   # inutile de continuer la campagne
DEFINITIVE_ERRORS = {"INVALID_INPUT"}                                 # ne changera pas si l'on réessaie

VALIDE, INVALIDE, INDETERMINE = "valide", "invalide", "indetermine"


@dataclass
class ViesResult:
    etat: str                       # valide | invalide | indetermine
    code: str                       # VALID, INVALID, ou code d'erreur VIES / HTTP_xxx / RESEAU_xxx / REPONSE_ILLISIBLE
    definitif: bool                 # False => à réessayer plus tard
    valid: bool | None = None
    name: str | None = None
    address: str | None = None
    request_date: str | None = None
    request_identifier: str | None = None
    raw: dict | None = None
    duree_ms: int | None = None
    http_status: int | None = None

    @property
    def blocking(self) -> bool:
        return self.code in BLOCKING

    def as_dict(self) -> dict:
        return asdict(self)


def _clean(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return None if text in {"", "---"} else text


def interpret(http_status: int | None, payload: dict | None, error: str | None = None,
              duree_ms: int | None = None) -> ViesResult:
    """Transforme (statut HTTP, corps JSON, erreur réseau) en résultat à trois états. Testé unitairement."""
    if error is not None:
        return ViesResult(INDETERMINE, f"RESEAU_{error}", False, duree_ms=duree_ms, http_status=http_status)
    if http_status != 200:
        return ViesResult(INDETERMINE, f"HTTP_{http_status}", False, raw=payload, duree_ms=duree_ms, http_status=http_status)
    if not isinstance(payload, dict):
        return ViesResult(INDETERMINE, "REPONSE_ILLISIBLE", False, duree_ms=duree_ms, http_status=http_status)

    wrappers = payload.get("errorWrappers") or []
    codes = [w.get("error") for w in wrappers if isinstance(w, dict) and w.get("error")]
    user_error = payload.get("userError")
    if user_error and user_error != "VALID":
        codes.append(user_error)
    if payload.get("actionSucceed") is False and not codes:
        codes.append("TECHNICAL_ERROR")
    if codes:
        code = codes[0]
        definitif = code in DEFINITIVE_ERRORS
        return ViesResult(INDETERMINE, code, definitif, raw=payload, duree_ms=duree_ms, http_status=http_status)

    valid = payload.get("valid", payload.get("isValid"))
    if valid is True:
        return ViesResult(VALIDE, "VALID", True, True, _clean(payload.get("name")), _clean(payload.get("address")),
                          payload.get("requestDate"), _clean(payload.get("requestIdentifier")), payload, duree_ms, http_status)
    if valid is False:
        return ViesResult(INVALIDE, "INVALID", True, False, None, None, payload.get("requestDate"),
                          _clean(payload.get("requestIdentifier")), payload, duree_ms, http_status)
    return ViesResult(INDETERMINE, "REPONSE_ILLISIBLE", False, raw=payload, duree_ms=duree_ms, http_status=http_status)


class ViesClient:
    def __init__(self, settings: Settings, session: requests.Session | None = None):
        self.settings = settings
        self.session = session or requests.Session()
        self.session.headers.update({
            "User-Agent": "MeridianTVA/1.0 (verification referentiel clients)",
            "Content-Type": "application/json",
        })

    def check(self, country: str, number: str) -> ViesResult:
        body = {"countryCode": country, "vatNumber": number}
        if self.settings.vies_requester_country and self.settings.vies_requester_number:
            body["requesterMemberStateCode"] = self.settings.vies_requester_country
            body["requesterNumber"] = self.settings.vies_requester_number
        started = time.perf_counter()
        try:
            response = self.session.post(self.settings.vies_url, json=body, timeout=self.settings.vies_timeout)
        except requests.RequestException as exc:
            duree = int((time.perf_counter() - started) * 1000)
            return interpret(None, None, error=type(exc).__name__, duree_ms=duree)
        duree = int((time.perf_counter() - started) * 1000)
        try:
            payload = response.json()
        except ValueError:
            payload = None
        return interpret(response.status_code, payload, duree_ms=duree)

    def status(self) -> dict[str, str]:
        """Disponibilité annoncée par État membre (GET /check-status) : à consulter avant une campagne."""
        response = self.session.get(self.settings.vies_status_url, timeout=self.settings.vies_timeout,
                                    headers={"Content-Type": None})
        response.raise_for_status()
        data = response.json()
        return {c["countryCode"]: c["availability"] for c in data.get("countries", [])}
