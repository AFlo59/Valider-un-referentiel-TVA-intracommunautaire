"""Interprétation des réponses VIES : une indisponibilité n'est jamais un verdict « invalide »."""

from meridian_tva.vies_client import INDETERMINE, INVALIDE, VALIDE, interpret

VALID_DANONE = {
    "countryCode": "FR", "vatNumber": "27552032534", "requestDate": "2026-09-07T14:47:50.391Z", "valid": True,
    "requestIdentifier": "", "name": "SA DANONE", "address": "59 RUE LA FAYETTE\n75009 PARIS",
}
INVALID_KEY = {"countryCode": "FR", "vatNumber": "00552032534", "requestDate": "2026-09-07T14:47:59.930Z", "valid": False,
               "requestIdentifier": "", "name": "---", "address": "---"}
THROTTLED = {"actionSucceed": False, "errorWrappers": [{"error": "MS_MAX_CONCURRENT_REQ"}]}
MS_DOWN = {"actionSucceed": False, "errorWrappers": [{"error": "MS_UNAVAILABLE"}]}
INVALID_INPUT = {"actionSucceed": False, "errorWrappers": [{"error": "INVALID_INPUT"}]}
IP_BLOCKED = {"actionSucceed": False, "errorWrappers": [{"error": "IP_BLOCKED"}]}
DE_VALID_NO_IDENTITY = {"countryCode": "DE", "vatNumber": "811128135", "valid": True, "name": "---", "address": "---", "requestIdentifier": ""}
WEB_UI_THROTTLED = {"isValid": False, "requestDate": "2026-09-07T14:47:41.786Z", "userError": "MS_MAX_CONCURRENT_REQ",
                    "name": "---", "address": "---", "requestIdentifier": "", "vatNumber": "27552032534"}


def test_valid_response():
    r = interpret(200, VALID_DANONE, duree_ms=6700)
    assert r.etat == VALIDE and r.code == "VALID" and r.definitif and r.valid is True
    assert r.name == "SA DANONE" and r.request_identifier is None  # vide sans demandeur


def test_invalid_response_is_definitive():
    r = interpret(200, INVALID_KEY)
    assert r.etat == INVALIDE and r.code == "INVALID" and r.definitif and r.name is None


def test_throttling_is_indeterminate_and_retryable():
    r = interpret(200, THROTTLED)
    assert r.etat == INDETERMINE and r.code == "MS_MAX_CONCURRENT_REQ" and not r.definitif and not r.blocking


def test_member_state_down_is_indeterminate():
    r = interpret(200, MS_DOWN)
    assert r.etat == INDETERMINE and r.code == "MS_UNAVAILABLE" and not r.definitif


def test_invalid_input_is_indeterminate_but_definitive():
    r = interpret(200, INVALID_INPUT)
    assert r.etat == INDETERMINE and r.code == "INVALID_INPUT" and r.definitif


def test_ip_blocked_is_blocking():
    r = interpret(200, IP_BLOCKED)
    assert r.etat == INDETERMINE and r.blocking


def test_web_ui_style_isvalid_false_with_user_error_is_not_invalid():
    r = interpret(200, WEB_UI_THROTTLED)
    assert r.etat == INDETERMINE and r.code == "MS_MAX_CONCURRENT_REQ"


def test_de_valid_without_identity():
    r = interpret(200, DE_VALID_NO_IDENTITY)
    assert r.etat == VALIDE and r.name is None and r.address is None


def test_http_error_and_network_error_are_indeterminate():
    assert interpret(503, None).code == "HTTP_503"
    assert interpret(200, None).code == "REPONSE_ILLISIBLE"
    r = interpret(None, None, error="ConnectTimeout")
    assert r.etat == INDETERMINE and r.code == "RESEAU_ConnectTimeout" and not r.definitif
