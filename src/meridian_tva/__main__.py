"""Point d'entrée : `uv run meridian-tva <commande>`.

  profile    regarde le fichier brut sans rien charger (phase 1 : combien de pays, de formes, de vides...)
  load       charge les 10 000 lignes, normalise, applique le verdict structurel, reconstruit les numéros (idempotent)
  stats      répartition par verdict et motif, réduction du nombre d'appels VIES
  status     disponibilité annoncée des États membres dans VIES (à consulter avant une campagne)
  campaign   campagne de vérification VIES (mode échantillon : --limit ; reprise automatique ; --par-pays N pour
             interroger N États membres en parallèle, un appel à la fois par État)
  report     régénère docs/rapport-reconciliation.md
  api        lance l'API (uvicorn) sur http://127.0.0.1:8000 (documentation : /docs)

Codes de sortie : 0 succès ; 1 erreur ; 2 campagne arrêtée sur code bloquant ; 3 une autre exécution est en cours ;
130 interruption clavier.
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections import Counter
from logging.handlers import RotatingFileHandler

from .campaign import CampaignBlocked, run_campaign
from .config import Settings, enable_native_tls_if_requested
from .load import load, read_rows
from .lock import AlreadyRunning, RunLock
from .normalize import normalize
from .report import write_report


def setup_logging(settings: Settings, verbose: bool) -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    settings.log_dir.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    root.setLevel(logging.DEBUG if verbose else logging.INFO)
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(logging.Formatter("%(asctime)s %(levelname)-7s %(name)s : %(message)s", "%H:%M:%S"))
    root.addHandler(console)
    file_handler = RotatingFileHandler(settings.log_dir / "meridian_tva.log", maxBytes=5_000_000, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-7s %(name)s : %(message)s"))
    root.addHandler(file_handler)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def profile(settings: Settings) -> None:
    rows = read_rows(settings.data_file)
    print(f"Lignes : {len(rows)}")
    print("Pays déclarés :", dict(Counter(r["pays_declare"] for r in rows).most_common()))
    print("Sources :", dict(Counter(r["source_saisie"] for r in rows).most_common()))
    dates = sorted(r["date_saisie"] for r in rows)
    print(f"Dates de saisie : de {dates[0]} à {dates[-1]}")
    empties = Counter(r["numero_tva"] for r in rows if normalize(r["numero_tva"], r["pays_declare"]).is_empty)
    print(f"Vides : {sum(empties.values())} lignes, {len(empties)} formes : {dict(empties)}")
    noisy = sum(1 for r in rows if normalize(r["numero_tva"], r["pays_declare"]).had_noise)
    no_prefix = sum(1 for r in rows if normalize(r["numero_tva"], r["pays_declare"]).prefix_source == "pays_declare")
    print(f"Lignes avec bruit de saisie (casse, séparateurs, espaces) : {noisy}")
    print(f"Lignes sans préfixe pays (pays_declare utilisé) : {no_prefix}")
    import re
    shapes = Counter(re.sub(r"[A-Z]", "A", re.sub(r"[0-9]", "9", r["numero_tva"].upper())) for r in rows)
    print("Formes les plus fréquentes (A = lettre, 9 = chiffre) :")
    for shape, count in shapes.most_common(15):
        print(f"  {count:5d}  {shape!r}")


def stats(settings: Settings) -> None:
    import psycopg

    with psycopg.connect(settings.pg_conninfo) as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM lignes_referentiel")
        total = cur.fetchone()[0]
        print(f"Lignes en base : {total}")
        cur.execute("SELECT verdict_structurel, motif_structurel, count(*) FROM lignes_referentiel GROUP BY 1, 2 ORDER BY 3 DESC")
        for verdict, motif, count in cur.fetchall():
            print(f"  {verdict:19s} {motif:22s} {count:5d}  ({100 * count / total:.1f} %)")
        cur.execute("SELECT count(*), count(*) FILTER (WHERE eligible_vies), coalesce(sum(nb_lignes - 1), 0), coalesce(sum(nb_lignes - 1) FILTER (WHERE eligible_vies), 0) FROM numeros")
        n, eligible, dup, dup_eligible = cur.fetchone()
        print(f"Numéros distincts : {n} ; éligibles VIES : {eligible} ; lignes en doublon : {dup} (dont {dup_eligible} parmi les éligibles)")
        print(f"Appels VIES évités par rapport à une approche naïve : {total - eligible} sur {total} ({100 * (total - eligible) / total:.1f} %)")
        cur.execute("SELECT etat_final, count(*) FROM etat_lignes GROUP BY 1 ORDER BY 2 DESC")
        print("État final par ligne :", dict(cur.fetchall()))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="meridian-tva")
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("profile", help="explore le fichier brut")
    p_load = sub.add_parser("load", help="charge et qualifie le référentiel")
    p_load.add_argument("--file", help="chemin du CSV (défaut : DATA_FILE)")
    sub.add_parser("stats", help="répartition des verdicts")
    sub.add_parser("status", help="disponibilité des États membres dans VIES")
    p_camp = sub.add_parser("campaign", help="campagne VIES")
    p_camp.add_argument("--limit", type=int, help="mode échantillon : nombre maximal de numéros vérifiés par cette exécution")
    p_camp.add_argument("--include-ids", help="identifiants de lignes à vérifier en priorité, séparés par des virgules (ex. 101,201)")
    p_camp.add_argument("--delay", type=float, help="temporisation entre appels en secondes (défaut : VIES_DELAY)")
    p_camp.add_argument("--no-retry-undetermined", action="store_true", help="ne réessaie pas les indéterminés transitoires")
    p_camp.add_argument("--max-attempts", type=int, default=3)
    p_camp.add_argument("--par-pays", type=int, default=1,
                        help="nombre d'États membres interrogés en parallèle, toujours un seul appel à la fois par État (défaut 1 = séquentiel ; 4 est un bon départ)")
    sub.add_parser("report", help="génère le rapport de réconciliation")
    p_api = sub.add_parser("api", help="lance l'API")
    p_api.add_argument("--host", default="127.0.0.1")
    p_api.add_argument("--port", type=int, default=8000)
    p_api.add_argument("--reload", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = Settings()
    setup_logging(settings, args.verbose)
    enable_native_tls_if_requested(settings)
    log = logging.getLogger("meridian")
    try:
        if args.command == "profile":
            profile(settings)
        elif args.command == "load":
            from pathlib import Path

            with RunLock(settings.log_dir / "run.lock"):
                load(settings, Path(args.file) if args.file else None)
        elif args.command == "stats":
            stats(settings)
        elif args.command == "status":
            from .vies_client import ViesClient

            availability = ViesClient(settings).status()
            down = {k: v for k, v in availability.items() if v != "Available"}
            print(f"{len(availability)} États membres ; indisponibles : {down or 'aucun'}")
        elif args.command == "campaign":
            ids = [int(x) for x in args.include_ids.split(",")] if args.include_ids else None
            # Une seule campagne à la fois : deux campagnes en parallèle doubleraient les appels à VIES
            with RunLock(settings.log_dir / "run.lock"):
                run_campaign(settings, limit=args.limit, include_ids=ids, delay=args.delay,
                             retry_undetermined=not args.no_retry_undetermined, max_attempts=args.max_attempts,
                             par_pays=args.par_pays)
        elif args.command == "report":
            text = write_report(settings)
            print(text.split("## 2.")[0])
        elif args.command == "api":
            import uvicorn

            uvicorn.run("meridian_tva.api:app", host=args.host, port=args.port, reload=args.reload)
        return 0
    except AlreadyRunning as exc:
        log.error("Refus : %s. Attendez la fin de l'autre exécution ou supprimez le verrou si elle a planté.", exc)
        return 3
    except KeyboardInterrupt:
        log.warning("Interruption clavier : l'état est en base, relancez la même commande pour reprendre.")
        return 130
    except CampaignBlocked as exc:
        log.error("%s", exc)
        return 2
    except Exception as exc:
        log.exception("Erreur : %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
