"""Temporisation adaptative et nouvelles tentatives : un registre qui limite le débit allonge l'intervalle, jamais le verdict."""

import threading

from meridian_tva.campaign import Pace, verify_with_retries
from meridian_tva.vies_client import INDETERMINE, VALIDE, ViesResult


class FakeClient:
    def __init__(self, results):
        self.results = list(results)
        self.calls = []

    def check(self, country, number):
        self.calls.append((country, number))
        return self.results.pop(0)


def throttled():
    return ViesResult(INDETERMINE, "MS_MAX_CONCURRENT_REQ", False, duree_ms=30)


def valid():
    return ViesResult(VALIDE, "VALID", True, True, "SA ORANGE", None, None, None, {}, 7000)


def test_pace_doubles_when_throttled_and_settles_back(monkeypatch):
    monkeypatch.setattr("meridian_tva.campaign.time.sleep", lambda s: None)
    pace = Pace(1.5, maximum=30)
    assert pace.throttled() == 5.0      # premier refus : au moins 5 s
    assert pace.throttled() == 10.0
    assert pace.throttled() == 20.0
    assert pace.throttled() == 30.0     # plafond
    assert pace.throttled() == 30.0
    pace.settled()
    assert pace.current == 24.0
    for _ in range(20):
        pace.settled()
    assert pace.current == 1.5          # retour à la base, jamais en dessous


def test_retries_use_pace_and_stop_on_definitive(monkeypatch):
    sleeps = []
    monkeypatch.setattr("meridian_tva.campaign.time.sleep", lambda s: sleeps.append(s))
    client = FakeClient([throttled(), throttled(), valid()])
    pace = Pace(1.5)
    result, attempts = verify_with_retries(client, "FR89380129866", "FR", pace, max_attempts=3)
    assert result.etat == VALIDE and attempts == 3
    assert client.calls == [("FR", "89380129866")] * 3
    # temporisation après chaque appel (1.5, 5, 10) + attentes avant nouvelle tentative (5, 10)
    assert sleeps == [1.5, 5.0, 5.0, 10.0, 10.0]
    assert pace.current == 8.0          # 10 s ramené de 20 % après le succès


def test_retries_give_up_as_indetermine_after_max_attempts(monkeypatch):
    monkeypatch.setattr("meridian_tva.campaign.time.sleep", lambda s: None)
    client = FakeClient([throttled(), throttled(), throttled()])
    result, attempts = verify_with_retries(client, "FR89380129866", "FR", 1.5, max_attempts=3)
    assert result.etat == INDETERMINE and not result.definitif and attempts == 3


def test_stop_event_interrupts_between_attempts(monkeypatch):
    monkeypatch.setattr("meridian_tva.campaign.time.sleep", lambda s: None)
    stop = threading.Event()
    stop.set()
    client = FakeClient([throttled(), valid()])
    result, attempts = verify_with_retries(client, "FR89380129866", "FR", 1.5, max_attempts=3, stop=stop)
    assert result.etat == INDETERMINE and attempts == 1 and len(client.calls) == 1
