"""Campagne de vérification VIES : temporisée, journalisée, reprenable, un appel à la fois PAR ÉTAT MEMBRE.

- Ne sont interrogés que les numéros éligibles (structure valide, pays interrogeable), dédoublonnés : c'est là que se
  gagne la réduction du nombre d'appels.
- L'état est en base : un numéro avec un verdict définitif (valide/invalide) n'est jamais rappelé ; un indéterminé
  transitoire (service ou État membre indisponible, débit limité) est réessayé à la campagne suivante.
- La limite de requêtes concurrentes de VIES est globale PAR ÉTAT MEMBRE : un worker par pays, jamais deux appels
  simultanés vers le même registre. `par_pays` fixe combien d'États sont interrogés en même temps (1 = séquentiel).
  Il existe aussi une limite globale au seuil non publié : si GLOBAL_MAX_CONCURRENT_REQ apparaît, réduire `par_pays`.
- Un code bloquant (IP_BLOCKED, VAT_BLOCKED, INVALID_REQUESTER_INFO) arrête toute la campagne : insister aggraverait.
- Ctrl+C : les appels en cours se terminent (quelques secondes), tout ce qui est commité est conservé, la relance reprend.
"""

from __future__ import annotations

import logging
import threading
import time
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

import psycopg
from psycopg.types.json import Json

from .config import Settings
from .vies_client import ViesClient, ViesResult

log = logging.getLogger(__name__)


class CampaignBlocked(Exception):
    pass


@dataclass
class CampaignStats:
    pending_total: int = 0
    processed: int = 0
    valides: int = 0
    invalides: int = 0
    indetermines: int = 0
    calls: int = 0
    total_ms: int = 0
    codes: dict[str, int] = field(default_factory=dict)
    blocked_code: str | None = None

    def merge(self, other: "CampaignStats") -> None:
        self.pending_total += other.pending_total
        self.processed += other.processed
        self.valides += other.valides
        self.invalides += other.invalides
        self.indetermines += other.indetermines
        self.calls += other.calls
        self.total_ms += other.total_ms
        for code, count in other.codes.items():
            self.codes[code] = self.codes.get(code, 0) + count
        self.blocked_code = self.blocked_code or other.blocked_code


INSERT_VERIFICATION = """
INSERT INTO verifications_vies (numero_normalise, etat, code_vies, definitif, nom, adresse, request_date,
                                request_identifier, reponse, duree_ms, tentative, origine)
VALUES (%(numero)s, %(etat)s, %(code)s, %(definitif)s, %(nom)s, %(adresse)s, %(request_date)s,
        %(request_identifier)s, %(reponse)s, %(duree_ms)s, %(tentative)s, %(origine)s)
"""

SELECT_PENDING = """
SELECT n.numero_normalise, n.pays
FROM numeros n
LEFT JOIN etat_vies_courant v USING (numero_normalise)
WHERE n.eligible_vies
  AND (v.numero_normalise IS NULL OR (NOT v.definitif AND %(retry)s))
ORDER BY n.numero_normalise
"""

SELECT_BY_IDS = """
SELECT DISTINCT n.numero_normalise, n.pays
FROM lignes_referentiel l JOIN numeros n USING (numero_normalise)
WHERE l.id = ANY(%(ids)s) AND n.eligible_vies
"""


def store(cur, numero: str, result: ViesResult, tentative: int, origine: str) -> None:
    cur.execute(INSERT_VERIFICATION, {
        "numero": numero, "etat": result.etat, "code": result.code, "definitif": result.definitif,
        "nom": result.name, "adresse": result.address, "request_date": result.request_date,
        "request_identifier": result.request_identifier, "reponse": Json(result.raw) if result.raw is not None else None,
        "duree_ms": result.duree_ms, "tentative": tentative, "origine": origine,
    })


def verify_with_retries(client: ViesClient, numero: str, pays: str, delay: float, max_attempts: int,
                        stats: CampaignStats | None = None, stop: threading.Event | None = None) -> tuple[ViesResult, int]:
    """Appelle VIES jusqu'à obtenir un résultat définitif ou épuiser les tentatives. Retourne (résultat, tentatives)."""
    body = numero[len(pays):]
    result: ViesResult | None = None
    for attempt in range(1, max_attempts + 1):
        result = client.check(pays, body)
        if stats is not None:
            stats.calls += 1
            stats.total_ms += result.duree_ms or 0
        time.sleep(delay)
        if result.definitif or result.blocking:
            return result, attempt
        if stop is not None and stop.is_set():
            return result, attempt
        if attempt < max_attempts:
            wait = 10 * attempt if "CONCURRENT" in result.code else 5 * attempt
            log.warning("[%s] %s : %s (tentative %d/%d), nouvelle tentative dans %d s", pays, numero, result.code, attempt, max_attempts, wait)
            time.sleep(wait)
    assert result is not None
    return result, max_attempts


class _SharedLimit:
    """Limite --limit partagée entre les workers : nombre maximal de numéros traités par cette exécution."""

    def __init__(self, limit: int | None):
        self.limit = limit
        self.count = 0
        self._lock = threading.Lock()

    def take(self) -> bool:
        with self._lock:
            if self.limit is not None and self.count >= self.limit:
                return False
            self.count += 1
            return True


def _worker(settings: Settings, label: str, items: list[tuple[str, str]], delay: float, max_attempts: int,
            shared: _SharedLimit, stop: threading.Event, client: ViesClient | None = None) -> CampaignStats:
    """Traite une liste de (numéro, pays) séquentiellement : un appel à la fois vers chaque registre national."""
    stats = CampaignStats(pending_total=len(items))
    client = client or ViesClient(settings)  # une session HTTP et une connexion par worker : ni l'une ni l'autre n'est partageable
    with psycopg.connect(settings.pg_conninfo) as conn, conn.cursor() as cur:
        for numero, pays in items:
            if stop.is_set():
                break
            if not shared.take():
                log.info("[%s] limite de %d numéro(s) atteinte pour cette exécution.", label, shared.limit)
                break
            result, attempts = verify_with_retries(client, numero, pays, delay, max_attempts, stats, stop)
            store(cur, numero, result, attempts, "campagne")
            conn.commit()  # un commit par numéro : l'état de reprise est toujours à jour
            stats.processed += 1
            stats.codes[result.code] = stats.codes.get(result.code, 0) + 1
            if result.etat == "valide":
                stats.valides += 1
                log.info("[%s] %s -> VALIDE (%s) %d ms", label, numero, result.name or "identité non communiquée", result.duree_ms or 0)
            elif result.etat == "invalide":
                stats.invalides += 1
                log.info("[%s] %s -> invalide %d ms", label, numero, result.duree_ms or 0)
            else:
                stats.indetermines += 1
                log.warning("[%s] %s -> INDÉTERMINÉ (%s)%s", label, numero, result.code, "" if result.definitif else ", sera réessayé")
            if result.blocking:
                stats.blocked_code = result.code
                stop.set()
                log.error("[%s] code bloquant %s : arrêt de toute la campagne", label, result.code)
                break
            if stats.processed % 25 == 0:
                log.info("[%s] progression : %d/%d (valides %d, invalides %d, indéterminés %d)",
                         label, stats.processed, stats.pending_total, stats.valides, stats.invalides, stats.indetermines)
    return stats


def run_campaign(settings: Settings, limit: int | None = None, include_ids: list[int] | None = None,
                 delay: float | None = None, retry_undetermined: bool = True, max_attempts: int = 3,
                 client: ViesClient | None = None, par_pays: int = 1) -> CampaignStats:
    delay = settings.vies_delay if delay is None else delay
    par_pays = max(1, par_pays)

    with psycopg.connect(settings.pg_conninfo) as conn, conn.cursor() as cur:
        pending: list[tuple[str, str]] = []
        if include_ids:
            cur.execute(SELECT_BY_IDS, {"ids": include_ids})
            pending.extend(cur.fetchall())
        cur.execute(SELECT_PENDING, {"retry": retry_undetermined})
        seen = {p[0] for p in pending}
        pending.extend(row for row in cur.fetchall() if row[0] not in seen)
        cur.execute("SELECT count(*) FROM numeros WHERE eligible_vies")
        eligible = cur.fetchone()[0]

    groups: "OrderedDict[str, list[tuple[str, str]]]" = OrderedDict()
    for numero, pays in pending:
        groups.setdefault(pays, []).append((numero, pays))
    log.info("Numéros éligibles VIES : %d ; à vérifier maintenant : %d sur %d État(s)%s ; rythme %.1f s/appel par État ; États en parallèle : %d",
             eligible, len(pending), len(groups), f" (limite {limit})" if limit else "", delay, min(par_pays, max(1, len(groups))))
    if not pending:
        log.info("Rien à faire : tous les numéros éligibles ont un verdict définitif.")
        return CampaignStats()

    shared = _SharedLimit(limit)
    stop = threading.Event()
    total = CampaignStats()
    started = time.perf_counter()

    if par_pays == 1 or len(groups) == 1:
        try:
            total.merge(_worker(settings, "campagne", pending, delay, max_attempts, shared, stop, client))
        except KeyboardInterrupt:
            stop.set()
            raise
    else:
        with ThreadPoolExecutor(max_workers=par_pays, thread_name_prefix="vies") as pool:
            futures = {pool.submit(_worker, settings, pays, items, delay, max_attempts, shared, stop): pays
                       for pays, items in groups.items()}
            try:
                for future in as_completed(futures):
                    total.merge(future.result())
            except KeyboardInterrupt:
                stop.set()
                log.warning("Interruption demandée : les appels en cours se terminent, puis arrêt (quelques secondes).")
                pool.shutdown(wait=True, cancel_futures=True)
                raise

    elapsed = time.perf_counter() - started
    avg = total.total_ms / total.calls if total.calls else 0
    log.info("Fin de campagne : %d numéros en %.0f s (%.1f s/numéro), %d appels, latence moyenne %.0f ms ; valides %d, invalides %d, indéterminés %d ; codes %s",
             total.processed, elapsed, elapsed / total.processed if total.processed else 0, total.calls, avg,
             total.valides, total.invalides, total.indetermines, total.codes)
    if "GLOBAL_MAX_CONCURRENT_REQ" in total.codes or "GLOBAL_MAX_CONCURRENT_REQ_TIME" in total.codes:
        log.warning("VIES a signalé sa limite globale : relancer avec une valeur de --par-pays plus faible.")
    if total.blocked_code:
        raise CampaignBlocked(f"code bloquant {total.blocked_code} reçu : campagne arrêtée après {total.processed} numéros")
    return total
