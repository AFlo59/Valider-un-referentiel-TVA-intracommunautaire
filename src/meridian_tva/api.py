"""API REST appelée par la facturation avant chaque émission hors taxe.

Contrat : l'appelant sait toujours trois choses : le verdict, d'où il sort (appel VIES frais, valeur connue en base,
ou simple contrôle structurel) et de quand il date (verifie_le, age_secondes, fraicheur).

Quand VIES est injoignable :
- s'il existe une valeur connue, même périmée, elle est renvoyée avec fraicheur = "perimee" et le motif de l'échec ;
- sinon le verdict est "indetermine", jamais "invalide", jamais une erreur 5xx muette : la réponse est HTTP 200 avec
  un verdict explicite que la facturation doit traiter comme « ne pas facturer hors taxe ».
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Literal

import psycopg
from fastapi import FastAPI, Query, Response
from pydantic import BaseModel, Field

from . import __version__
from .campaign import store
from .config import Settings, enable_native_tls_if_requested
from .report import names_match
from .structural import COVERED, validate
from .vies_client import ViesClient

log = logging.getLogger(__name__)
settings = Settings()
enable_native_tls_if_requested(settings)
client = ViesClient(settings)

app = FastAPI(
    title="Meridian TVA — vérification des numéros de TVA intracommunautaire",
    version=__version__,
    description="Verdict, origine et fraîcheur pour chaque numéro de TVA, avant toute facturation hors taxe.",
)


class Structurel(BaseModel):
    verdict: str = Field(description="VALIDE_STRUCTURE | INVALIDE_STRUCTURE | HORS_PERIMETRE | ABSENT")
    motif: str
    detail: str


class Verification(BaseModel):
    numero_saisi: str
    numero_normalise: str | None
    pays: str | None
    verdict: Literal["valide", "invalide", "indetermine", "hors_perimetre", "absent"]
    origine: Literal["vies_live", "cache", "structurel"] = Field(description="d'où sort le verdict")
    verifie_le: datetime | None = Field(description="date de la réponse VIES qui fonde le verdict ; null si aucune")
    age_secondes: int | None
    fraicheur: Literal["fraiche", "perimee", "aucune"] = Field(description=f"fraiche si âge <= {settings.verdict_ttl_hours:g} h")
    motif: str = Field(description="motif structurel, code VIES, ou raison de l'indétermination")
    code_vies: str | None
    nom: str | None
    adresse: str | None
    request_identifier: str | None = Field(description="numéro de consultation VIES (preuve), si le demandeur est configuré")
    identite_concordante: bool | None = Field(description="le nom renvoyé par VIES concorde avec la raison sociale (paramètre raison_sociale, sinon celle du référentiel) ; null si non vérifiable")
    facturation_hors_taxe_possible: bool = Field(description="vrai uniquement si verdict = valide, fraicheur = fraiche et identité non contredite")


class Sante(BaseModel):
    statut: str
    base: str
    version: str


def _age(verifie_le: datetime | None) -> int | None:
    if verifie_le is None:
        return None
    return int((datetime.now(timezone.utc) - verifie_le).total_seconds())


def _fraicheur(age: int | None) -> str:
    if age is None:
        return "aucune"
    return "fraiche" if age <= settings.verdict_ttl_hours * 3600 else "perimee"


def _build(numero: str, verdict: str, origine: str, motif: str, structurel, normalise, pays, verifie_le=None,
           code_vies=None, nom=None, adresse=None, request_identifier=None, raison_sociale: str | None = None) -> Verification:
    age = _age(verifie_le)
    fraicheur = _fraicheur(age)
    concordance = names_match(nom, raison_sociale) if (verdict == "valide" and nom and raison_sociale) else None
    return Verification(
        numero_saisi=numero, numero_normalise=normalise, pays=pays, verdict=verdict, origine=origine,
        verifie_le=verifie_le, age_secondes=age, fraicheur=fraicheur, motif=motif, code_vies=code_vies,
        nom=nom, adresse=adresse, request_identifier=request_identifier, identite_concordante=concordance,
        facturation_hors_taxe_possible=(verdict == "valide" and fraicheur == "fraiche" and concordance is not False),
    )


def _raison_sociale_referentiel(cur, normalise: str) -> str | None:
    cur.execute("SELECT string_agg(DISTINCT raison_sociale, ' | ') FROM lignes_referentiel WHERE numero_normalise = %s", (normalise,))
    row = cur.fetchone()
    return row[0] if row else None


@app.get("/health", response_model=Sante, tags=["technique"])
def health() -> Sante:
    try:
        with psycopg.connect(settings.pg_conninfo, connect_timeout=3) as conn:
            conn.execute("SELECT 1")
        base = "ok"
    except psycopg.Error as exc:
        base = f"indisponible : {type(exc).__name__}"
    return Sante(statut="ok" if base == "ok" else "degrade", base=base, version=__version__)


@app.get("/verifier/{numero}", response_model=Verification, tags=["verification"],
         summary="Verdict, origine et fraîcheur pour un numéro de TVA")
def verifier(
    numero: str,
    response: Response,
    pays: str | None = Query(default=None, min_length=2, max_length=2, description="pays déclaré, utilisé si le numéro n'a pas de préfixe"),
    max_age_hours: float = Query(default=settings.verdict_ttl_hours, ge=0, description="au-delà de cet âge, VIES est rappelé"),
    forcer_vies: bool = Query(default=False, description="ignorer la valeur connue et rappeler VIES"),
    raison_sociale: str | None = Query(default=None, description="nom du client facturé, comparé au nom renvoyé par VIES ; à défaut, celui du référentiel"),
) -> Verification:
    return _verifier(numero, response, pays, max_age_hours, forcer_vies, raison_sociale)


@app.get("/verifier", response_model=Verification, tags=["verification"],
         summary="Même service, numéro passé en paramètre (valeurs brutes avec espaces, barres ou vides)")
def verifier_query(
    response: Response,
    numero: str = Query(description="valeur telle que saisie, ex. ' NL505862176B88 ' ou 'N/A'"),
    pays: str | None = Query(default=None, min_length=2, max_length=2),
    max_age_hours: float = Query(default=settings.verdict_ttl_hours, ge=0),
    forcer_vies: bool = Query(default=False),
    raison_sociale: str | None = Query(default=None),
) -> Verification:
    return _verifier(numero, response, pays, max_age_hours, forcer_vies, raison_sociale)


def _verifier(numero: str, response: Response, pays: str | None, max_age_hours: float, forcer_vies: bool,
              raison_sociale: str | None = None) -> Verification:
    response.headers["Cache-Control"] = "no-store"
    v = validate(numero, pays)
    structurel = Structurel(verdict=v.verdict, motif=v.motif, detail=v.detail)
    normalise = None if v.normalized.is_empty else v.normalized.compact
    pays_resolu = v.normalized.country

    if v.verdict == "ABSENT":
        return _build(numero, "absent", "structurel", v.motif, structurel, None, None)
    if v.verdict == "HORS_PERIMETRE":
        return _build(numero, "hors_perimetre", "structurel", v.motif, structurel, normalise, pays_resolu)
    if v.verdict == "INVALIDE_STRUCTURE":
        return _build(numero, "invalide", "structurel", v.motif, structurel, normalise, pays_resolu)

    with psycopg.connect(settings.pg_conninfo) as conn, conn.cursor() as cur:
        # le numéro peut ne pas être dans le référentiel : on le crée pour pouvoir historiser la vérification
        cur.execute("""INSERT INTO numeros (numero_normalise, pays, verdict_structurel, motif_structurel, nb_lignes, eligible_vies)
                       VALUES (%s, %s, 'VALIDE_STRUCTURE', 'OK', 0, true) ON CONFLICT (numero_normalise) DO NOTHING""",
                    (normalise, pays_resolu))
        cur.execute("""SELECT etat, code_vies, definitif, nom, adresse, request_identifier, verifie_le
                       FROM etat_vies_courant WHERE numero_normalise = %s""", (normalise,))
        cached = cur.fetchone()
        cached_age = _age(cached[6]) if cached else None
        usable = cached is not None and cached[2] and cached_age is not None and cached_age <= max_age_hours * 3600
        raison_sociale = raison_sociale or _raison_sociale_referentiel(cur, normalise)

        if usable and not forcer_vies:
            etat, code, _, nom, adresse, rid, verifie_le = cached
            conn.commit()
            return _build(numero, etat, "cache", code, structurel, normalise, pays_resolu, verifie_le, code, nom, adresse, rid, raison_sociale)

        result = client.check(pays_resolu, v.normalized.body or "")
        store(cur, normalise, result, 1, "api")
        cur.execute("SELECT verifie_le FROM verifications_vies WHERE numero_normalise = %s ORDER BY verifie_le DESC LIMIT 1", (normalise,))
        now = cur.fetchone()[0]
        conn.commit()

    if result.definitif and result.etat in ("valide", "invalide"):
        return _build(numero, result.etat, "vies_live", result.code, structurel, normalise, pays_resolu, now,
                      result.code, result.name, result.address, result.request_identifier, raison_sociale)

    # VIES n'a pas tranché
    if cached is not None and cached[2]:
        etat, code, _, nom, adresse, rid, verifie_le = cached
        log.warning("VIES indisponible (%s) pour %s : valeur connue du %s renvoyée comme périmée", result.code, normalise, verifie_le)
        out = _build(numero, etat, "cache", f"VIES indisponible ({result.code}) ; dernière valeur connue", structurel,
                     normalise, pays_resolu, verifie_le, code, nom, adresse, rid, raison_sociale)
        out.fraicheur = "perimee"
        out.facturation_hors_taxe_possible = False
        return out
    return _build(numero, "indetermine", "vies_live", f"VIES n'a pas répondu ({result.code}) et aucune valeur connue", structurel,
                  normalise, pays_resolu, None, result.code)


@app.get("/pays", tags=["technique"], summary="Pays couverts par le contrôle structurel")
def pays_couverts() -> dict:
    return {"couverts": sorted(COVERED)}
