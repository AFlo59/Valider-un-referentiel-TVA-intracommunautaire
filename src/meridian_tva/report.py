"""Rapport de réconciliation pour la direction financière, régénéré par une commande depuis la base."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import psycopg

from .config import Settings

log = logging.getLogger(__name__)


def _table(cur, sql: str, headers: list[str], params=None) -> str:
    cur.execute(sql, params or {})
    rows = cur.fetchall()
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for row in rows:
        lines.append("| " + " | ".join("" if v is None else str(v) for v in row) + " |")
    return "\n".join(lines)


def _one(cur, sql: str, params=None):
    cur.execute(sql, params or {})
    return cur.fetchone()


def build_report(settings: Settings) -> str:
    with psycopg.connect(settings.pg_conninfo) as conn, conn.cursor() as cur:
        total = _one(cur, "SELECT count(*) FROM lignes_referentiel")[0]
        absents = _one(cur, "SELECT count(*) FROM lignes_referentiel WHERE numero_normalise IS NULL")[0]
        hors = _one(cur, "SELECT count(*) FROM lignes_referentiel WHERE verdict_structurel = 'HORS_PERIMETRE'")[0]
        invalides_struct = _one(cur, "SELECT count(*) FROM lignes_referentiel WHERE verdict_structurel = 'INVALIDE_STRUCTURE'")[0]
        valides_struct = _one(cur, "SELECT count(*) FROM lignes_referentiel WHERE verdict_structurel = 'VALIDE_STRUCTURE'")[0]
        numeros_distincts = _one(cur, "SELECT count(*) FROM numeros")[0]
        eligibles = _one(cur, "SELECT count(*) FROM numeros WHERE eligible_vies")[0]
        doublons_lignes = _one(cur, "SELECT coalesce(sum(nb_lignes - 1), 0) FROM numeros")[0]
        doublons_eligibles = _one(cur, "SELECT coalesce(sum(nb_lignes - 1), 0) FROM numeros WHERE eligible_vies")[0]
        groupes = _one(cur, "SELECT count(*) FROM numeros WHERE nb_lignes > 1")[0]
        verifs, verifies, appels_ms = _one(cur, "SELECT count(*), count(DISTINCT numero_normalise), coalesce(avg(duree_ms),0) FROM verifications_vies")
        etats = dict(_one_all(cur, "SELECT etat_final, count(*) FROM etat_lignes GROUP BY etat_final"))
        derniere = _one(cur, "SELECT max(verifie_le) FROM verifications_vies")[0]

        def pct(n):
            return f"{100 * n / total:.1f} %" if total else "-"

        parts = [f"# Rapport de réconciliation du référentiel TVA\n\n*Généré le {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M UTC')} par `uv run meridian-tva report`. "
                 f"Dernière vérification VIES : {derniere.strftime('%d/%m/%Y %H:%M UTC') if derniere else 'aucune'}.*\n"]

        parts.append("## 1. Réponse à la question centrale (par ligne du référentiel)\n")
        parts.append("| État final | Lignes | Part | Signification |\n|---|---|---|---|")
        meaning = {
            "valide": "numéro confirmé par VIES à la date indiquée : facturation hors taxe possible si les autres conditions sont réunies",
            "invalide": "structure fausse (format ou clé) ou numéro non reconnu par VIES : facturer avec TVA, corriger le référentiel",
            "indetermine": "structure correcte mais non confirmé par VIES (non encore interrogé, ou service indisponible) : ne jamais facturer hors taxe sur cette base",
            "hors_perimetre": "pays hors UE (GB/UK), code pays inexistant (ZZ, QQ, XX) : à requalifier avec le client, régime export le cas échéant",
            "absent": "aucun numéro saisi : à collecter auprès du client",
        }
        for etat in ("valide", "invalide", "indetermine", "hors_perimetre", "absent"):
            parts.append(f"| {etat} | {etats.get(etat, 0)} | {pct(etats.get(etat, 0))} | {meaning[etat]} |")
        parts.append(f"| **Total** | **{total}** | 100 % | |\n")

        parts.append("## 2. Entonnoir : de 10 000 lignes aux appels VIES nécessaires\n")
        parts.append("| Étape | Lignes ou numéros | Commentaire |\n|---|---|---|")
        parts.append(f"| Lignes reçues | {total} | fichier `numeros_tva.csv` |")
        parts.append(f"| Numéro absent | {absents} | six formes de vide : '', ' ', '-', 'N/A', 'null', 'NU.LL' |")
        parts.append(f"| Hors périmètre VIES | {hors} | GB/UK (Brexit), codes ZZ/QQ/XX |")
        parts.append(f"| Structure invalide | {invalides_struct} | longueur, caractères, format ou clé de contrôle |")
        parts.append(f"| Structure valide | {valides_struct} | candidats à VIES, avant dédoublonnage |")
        parts.append(f"| Doublons parmi les candidats | {doublons_eligibles} | même numéro normalisé (pays + numéro), vides exclus |")
        parts.append(f"| **Appels VIES nécessaires** | **{eligibles}** | contre 10 000 pour une approche naïve : réduction de {100 * (1 - eligibles / total):.1f} % |")
        parts.append(f"| Appels VIES effectués à ce jour | {verifs} | {verifies} numéros distincts, latence moyenne {appels_ms:.0f} ms |\n")

        parts.append("## 3. Verdicts structurels et motifs (par ligne)\n")
        parts.append(_table(cur, """
            SELECT verdict_structurel, motif_structurel, count(*) AS lignes, round(100.0 * count(*) / %(total)s, 1) AS part
            FROM lignes_referentiel GROUP BY 1, 2 ORDER BY 3 DESC""", ["Verdict", "Motif", "Lignes", "%"], {"total": total}) + "\n")
        parts.append("Traitement de chaque famille de motifs : `OK` → vérification VIES ; `CLE_INVALIDE`, `LONGUEUR_INVALIDE`, `FORMAT_INVALIDE`, "
                     "`CARACTERES_INVALIDES`, `PAYS_INCOHERENT` → invalide sans appel VIES, correction à demander au client ; "
                     "`NUMERO_ABSENT` → à collecter ; `PAYS_HORS_UE`, `PAYS_INCONNU`, `PAYS_NON_COUVERT` → hors périmètre, requalification manuelle.\n")

        parts.append("## 4. Répartition par pays déclaré\n")
        parts.append(_table(cur, """
            SELECT pays_declare, count(*) AS lignes,
                   count(*) FILTER (WHERE verdict_structurel = 'VALIDE_STRUCTURE') AS structure_ok,
                   count(*) FILTER (WHERE verdict_structurel = 'INVALIDE_STRUCTURE') AS structure_ko,
                   count(*) FILTER (WHERE verdict_structurel = 'HORS_PERIMETRE') AS hors_perimetre,
                   count(*) FILTER (WHERE verdict_structurel = 'ABSENT') AS absents
            FROM lignes_referentiel GROUP BY 1 ORDER BY 2 DESC""",
            ["Pays déclaré", "Lignes", "Structure OK", "Structure KO", "Hors périmètre", "Absents"]) + "\n")

        parts.append("## 5. Doublons\n")
        parts.append(f"Définition retenue : deux lignes sont des doublons si elles portent le même numéro normalisé (préfixe pays résolu + numéro "
                     f"sans bruit de saisie). Les lignes sans numéro ne sont jamais des doublons entre elles.\n\n"
                     f"- Numéros distincts (non vides) : **{numeros_distincts}** pour {total - absents} lignes portant un numéro\n"
                     f"- Lignes en trop : **{doublons_lignes}** réparties en {groupes} groupes\n"
                     f"- Sur les seuls numéros éligibles VIES : {doublons_eligibles} appels évités par le dédoublonnage\n")
        parts.append(_table(cur, """
            SELECT n.numero_normalise, n.nb_lignes, string_agg(DISTINCT l.source_saisie, ', ' ORDER BY l.source_saisie) AS sources,
                   string_agg(DISTINCT l.numero_brut, ' | ') AS formes_brutes
            FROM numeros n JOIN lignes_referentiel l USING (numero_normalise)
            WHERE n.nb_lignes > 1 GROUP BY 1, 2 ORDER BY 2 DESC, 1 LIMIT 8""",
            ["Numéro normalisé", "Lignes", "Canaux", "Formes saisies"]) + "\n")

        parts.append("## 6. Vérification en ligne (VIES)\n")
        parts.append(_table(cur, """
            SELECT etat, code_vies, count(*) AS numeros, round(avg(duree_ms)) AS latence_moy_ms, max(duree_ms) AS latence_max_ms,
                   count(*) FILTER (WHERE request_identifier IS NOT NULL) AS avec_num_consultation
            FROM etat_vies_courant GROUP BY 1, 2 ORDER BY 3 DESC""",
            ["État", "Code VIES", "Numéros", "Latence moyenne (ms)", "Latence max (ms)", "Avec n° de consultation"]) + "\n")
        parts.append(_table(cur, """
            SELECT e.numero_normalise, v.nom, replace(v.adresse, E'\\n', ', ') AS adresse, to_char(v.verifie_le, 'DD/MM/YYYY HH24:MI') AS verifie_le,
                   string_agg(l.id::text, ', ' ORDER BY l.id) AS lignes
            FROM etat_numeros e JOIN etat_vies_courant v USING (numero_normalise) JOIN lignes_referentiel l USING (numero_normalise)
            WHERE e.etat_final = 'valide' GROUP BY 1, 2, 3, 4 ORDER BY 1""",
            ["Numéro valide", "Nom (VIES)", "Adresse (VIES)", "Vérifié le", "Lignes"]) + "\n")
        restants = _one(cur, "SELECT count(*) FROM etat_numeros WHERE eligible_vies AND etat_final = 'indetermine'")[0]
        parts.append(f"Numéros éligibles restant à trancher (non interrogés ou indéterminés transitoires) : **{restants}**. "
                     f"Relancer `uv run meridian-tva campaign` reprend exactement là : les verdicts définitifs ne sont jamais rappelés.\n")

        parts.append("## 7. Durée de validité d'un verdict\n")
        parts.append(f"VIES ne répond que pour l'instant présent. Chaque verdict est stocké avec sa date ; l'API le sert comme « frais » pendant "
                     f"{settings.verdict_ttl_hours:g} h puis le revérifie. La facturation doit consulter l'API avant chaque émission hors taxe, "
                     f"et conserver le numéro de consultation VIES (`request_identifier`) sur la facture : il n'est délivré que si le numéro "
                     f"de TVA de Meridian est transmis en tant que demandeur ({'configuré' if settings.vies_requester_number else 'non configuré : à renseigner dans .env'}).\n")
        return "\n".join(parts)


def _one_all(cur, sql: str):
    cur.execute(sql)
    return cur.fetchall()


def write_report(settings: Settings) -> str:
    text = build_report(settings)
    settings.report_file.parent.mkdir(parents=True, exist_ok=True)
    settings.report_file.write_text(text, encoding="utf-8", newline="\n")
    log.info("Rapport écrit : %s", settings.report_file)
    return text
