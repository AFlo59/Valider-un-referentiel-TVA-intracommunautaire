"""Campagne de vérification VIES : un seul appel à la fois, temporisée, journalisée, reprenable.

- Ne sont interrogés que les numéros éligibles (structure valide, pays interrogeable), dédoublonnés : c'est là que se
  gagne la réduction du nombre d'appels.
- L'état est en base : un numéro avec un verdict définitif (valide/invalide) n'est jamais rappelé ; un indéterminé
  transitoire (service ou État membre indisponible, débit limité) est réessayé à la campagne suivante.
- Un seul worker : la limite de requêtes concurrentes de VIES est globale par État membre, paralléliser ne fait que
  provoquer MS_MAX_CONCURRENT_REQ.
- Un code bloquant (IP_BLOCKED, VAT_BLOCKED, INVALID_REQUESTER_INFO) arrête la campagne : insister aggraverait la situation.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

import psycopg
from psycopg.types.json import Json

from .config import Settings
from .vies_client import INDETERMINE, ViesClient, ViesResult

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
                        stats: CampaignStats | None = None) -> tuple[ViesResult, int]:
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
        if attempt < max_attempts:
            wait = 10 * attempt if "CONCURRENT" in result.code else 5 * attempt
            log.warning("%s : %s (tentative %d/%d), nouvelle tentative dans %d s", numero, result.code, attempt, max_attempts, wait)
            time.sleep(wait)
    assert result is not None
    return result, max_attempts


def run_campaign(settings: Settings, limit: int | None = None, include_ids: list[int] | None = None,
                 delay: float | None = None, retry_undetermined: bool = True, max_attempts: int = 3,
                 client: ViesClient | None = None) -> CampaignStats:
    delay = settings.vies_delay if delay is None else delay
    client = client or ViesClient(settings)
    stats = CampaignStats()

    with psycopg.connect(settings.pg_conninfo) as conn, conn.cursor() as cur:
        pending: list[tuple[str, str]] = []
        if include_ids:
            cur.execute(SELECT_BY_IDS, {"ids": include_ids})
            pending.extend(cur.fetchall())
        cur.execute(SELECT_PENDING, {"retry": retry_undetermined})
        seen = {p[0] for p in pending}
        pending.extend(row for row in cur.fetchall() if row[0] not in seen)
        stats.pending_total = len(pending)
        cur.execute("SELECT count(*) FROM numeros WHERE eligible_vies")
        eligible = cur.fetchone()[0]
        log.info("Numéros éligibles VIES : %d ; à vérifier maintenant : %d%s ; rythme %.1f s/appel",
                 eligible, len(pending), f" (limite {limit})" if limit else "", delay)
        if not pending:
            log.info("Rien à faire : tous les numéros éligibles ont un verdict définitif.")
            return stats

        for numero, pays in pending:
            if limit is not None and stats.processed >= limit:
                log.info("Limite de %d numéro(s) atteinte pour cette exécution.", limit)
                break
            result, attempts = verify_with_retries(client, numero, pays, delay, max_attempts, stats)
            store(cur, numero, result, attempts, "campagne")
            conn.commit()  # un commit par numéro : l'état de reprise est toujours à jour
            stats.processed += 1
            stats.codes[result.code] = stats.codes.get(result.code, 0) + 1
            if result.etat == "valide":
                stats.valides += 1
                log.info("%s -> VALIDE (%s) %d ms", numero, result.name or "identité non communiquée", result.duree_ms or 0)
            elif result.etat == "invalide":
                stats.invalides += 1
                log.info("%s -> invalide %d ms", numero, result.duree_ms or 0)
            else:
                stats.indetermines += 1
                log.warning("%s -> INDÉTERMINÉ (%s)%s", numero, result.code, "" if result.definitif else ", sera réessayé")
            if result.blocking:
                raise CampaignBlocked(f"code bloquant {result.code} reçu : campagne arrêtée après {stats.processed} numéros")
            if stats.processed % 25 == 0:
                log.info("Progression : %d/%d (valides %d, invalides %d, indéterminés %d, %d appels)",
                         stats.processed, stats.pending_total, stats.valides, stats.invalides, stats.indetermines, stats.calls)

    avg = stats.total_ms / stats.calls if stats.calls else 0
    log.info("Fin de campagne : %d numéros, %d appels, latence moyenne %.0f ms ; valides %d, invalides %d, indéterminés %d ; codes %s",
             stats.processed, stats.calls, avg, stats.valides, stats.invalides, stats.indetermines, stats.codes)
    return stats
