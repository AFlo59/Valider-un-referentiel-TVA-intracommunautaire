"""Chargement du référentiel : lecture brute du CSV, normalisation, verdict structurel, écriture idempotente.

- Le CSV est lu avec le module csv, en texte : aucune conversion implicite (pandas transformerait 'N/A' et 'null' en NaN
  et ferait disparaître 146 valeurs brutes que le schéma doit conserver).
- lignes_referentiel est mise à jour par INSERT ... ON CONFLICT (id) : un rechargement ne duplique rien.
- numeros est reconstruite depuis les lignes : un numéro normalisé = une entité ; nb_lignes compte les doublons.
"""

from __future__ import annotations

import csv
import logging
from collections import Counter
from datetime import date
from pathlib import Path

import psycopg

from .config import Settings
from .structural import validate

log = logging.getLogger(__name__)

SCHEMA_FILE = Path(__file__).resolve().parents[2] / "sql" / "schema.sql"

UPSERT_LIGNE = """
INSERT INTO lignes_referentiel (id, raison_sociale, pays_declare, numero_brut, date_saisie, source_saisie,
                                numero_normalise, pays_resolu, verdict_structurel, motif_structurel, detail_structurel, charge_le)
VALUES (%(id)s, %(raison_sociale)s, %(pays_declare)s, %(numero_brut)s, %(date_saisie)s, %(source_saisie)s,
        %(numero_normalise)s, %(pays_resolu)s, %(verdict_structurel)s, %(motif_structurel)s, %(detail_structurel)s, now())
ON CONFLICT (id) DO UPDATE SET
    raison_sociale = EXCLUDED.raison_sociale, pays_declare = EXCLUDED.pays_declare, numero_brut = EXCLUDED.numero_brut,
    date_saisie = EXCLUDED.date_saisie, source_saisie = EXCLUDED.source_saisie, numero_normalise = EXCLUDED.numero_normalise,
    pays_resolu = EXCLUDED.pays_resolu, verdict_structurel = EXCLUDED.verdict_structurel,
    motif_structurel = EXCLUDED.motif_structurel, detail_structurel = EXCLUDED.detail_structurel, charge_le = now()
"""

REBUILD_NUMEROS = """
INSERT INTO numeros (numero_normalise, pays, verdict_structurel, motif_structurel, nb_lignes, eligible_vies)
SELECT numero_normalise,
       max(pays_resolu),
       max(verdict_structurel),
       max(motif_structurel),
       count(*),
       bool_and(verdict_structurel = 'VALIDE_STRUCTURE')
FROM lignes_referentiel
WHERE numero_normalise IS NOT NULL
GROUP BY numero_normalise
ON CONFLICT (numero_normalise) DO UPDATE SET
    pays = EXCLUDED.pays, verdict_structurel = EXCLUDED.verdict_structurel, motif_structurel = EXCLUDED.motif_structurel,
    nb_lignes = EXCLUDED.nb_lignes, eligible_vies = EXCLUDED.eligible_vies
"""


def read_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
    expected = {"id", "raison_sociale", "pays_declare", "numero_tva", "date_saisie", "source_saisie"}
    missing = expected - set(reader.fieldnames or [])
    if missing:
        raise ValueError(f"colonnes manquantes dans {path} : {sorted(missing)}")
    return rows


def _parse_date(value: str) -> date | None:
    value = (value or "").strip()
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def prepare(rows: list[dict]) -> list[dict]:
    prepared = []
    for row in rows:
        verdict = validate(row["numero_tva"], row["pays_declare"])
        prepared.append({
            "id": int(row["id"]),
            "raison_sociale": row["raison_sociale"],
            "pays_declare": row["pays_declare"],
            "numero_brut": row["numero_tva"],
            "date_saisie": _parse_date(row["date_saisie"]),
            "source_saisie": row["source_saisie"],
            "numero_normalise": verdict.normalized.compact if not verdict.normalized.is_empty else None,
            "pays_resolu": verdict.normalized.country,
            "verdict_structurel": verdict.verdict,
            "motif_structurel": verdict.motif,
            "detail_structurel": verdict.detail,
        })
    return prepared


def load(settings: Settings, path: Path | None = None) -> dict:
    path = path or settings.data_file
    rows = read_rows(path)
    prepared = prepare(rows)
    log.info("%d lignes lues dans %s", len(prepared), path)

    with psycopg.connect(settings.pg_conninfo) as conn, conn.cursor() as cur:
        cur.execute(SCHEMA_FILE.read_text(encoding="utf-8"))
        cur.execute("SELECT count(*) FROM lignes_referentiel")
        before = cur.fetchone()[0]
        cur.executemany(UPSERT_LIGNE, prepared)
        cur.execute(REBUILD_NUMEROS)
        # numéros qui n'existeraient plus dans le fichier (rechargement d'un fichier corrigé) : on les garde, avec leur historique
        cur.execute("SELECT count(*) FROM lignes_referentiel")
        after = cur.fetchone()[0]
        cur.execute("SELECT count(*), count(*) FILTER (WHERE eligible_vies) FROM numeros")
        n_numeros, n_eligible = cur.fetchone()
        conn.commit()

    verdicts = Counter(p["verdict_structurel"] for p in prepared)
    motifs = Counter((p["verdict_structurel"], p["motif_structurel"]) for p in prepared)
    log.info("Lignes en base avant : %d ; après : %d (rechargement idempotent)", before, after)
    log.info("Verdicts structurels par ligne : %s", dict(verdicts))
    for (verdict, motif), count in sorted(motifs.items(), key=lambda kv: -kv[1]):
        log.info("  %-19s %-22s %5d", verdict, motif, count)
    log.info("Numéros distincts (non vides) : %d ; éligibles VIES : %d", n_numeros, n_eligible)
    return {"lignes": after, "verdicts": dict(verdicts), "numeros": n_numeros, "eligibles_vies": n_eligible}
