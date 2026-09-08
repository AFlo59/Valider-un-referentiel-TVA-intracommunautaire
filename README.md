# Meridian Distribution — validation du référentiel de TVA intracommunautaire

Pipeline Python + PostgreSQL + FastAPI qui répond à la question de la direction financière :

> « Parmi nos 10 000 numéros, lesquels sont valides, lesquels ne le sont pas, et lesquels n'ont pas pu être tranchés ? »

Ordre imposé et respecté : **normaliser → dédupliquer → filtrer sur la structure → interroger VIES**. Chaque étape réduit le
volume de la suivante et ses chiffres sont dans le rapport de réconciliation. Une API REST donne ensuite à la facturation,
pour chaque numéro, **le verdict, son origine et sa fraîcheur**.

## Technologies et justification

| Choix | Pourquoi |
|---|---|
| Python 3.12+ avec **uv** | Installation reproductible en une commande (`uv.lock`). |
| **PostgreSQL 16** (compose du kit) | Le schéma sépare ce qui a été reçu (valeur brute) de ce qui a été déduit (valeur normalisée, verdicts datés). Vues SQL pour l'état courant. |
| **csv** + **psycopg 3** pour le chargement | Lecture en texte brut : `pandas` par défaut transforme `N/A` et `null` en NaN et ferait disparaître 146 valeurs brutes. |
| Module structurel **réécrit** (`structural.py`) | Le module annoncé par le brief n'est pas dans le kit. Les dix pays sont implémentés d'après les spécifications nationales (format + clé de contrôle), avec des tests sur des numéros publics réels. |
| **requests** vers l'endpoint REST documenté `POST /check-vat-number` | Le lien GET du brief est l'endpoint privé de l'interface web : il renvoie `isValid: false` avec un `userError` quand l'État membre limite le débit. Le WSDL SOAP reste l'alternative officielle. |
| **FastAPI** | Contrat de réponse typé (Pydantic) donc documentation OpenAPI exacte sur `/docs`. |
| **truststore** (optionnel) | Postes avec interception TLS : certificats système plutôt que `verify=False`, inacceptable sur un service à valeur probante. |

## Lancement depuis zéro

Prérequis : [uv](https://docs.astral.sh/uv/), Docker Desktop, Git.

```bash
git clone <url-du-repo> meridian-tva
cd meridian-tva
cp .env.example .env               # renseignez VIES_REQUESTER_COUNTRY / VIES_REQUESTER_NUMBER (numéro de TVA de Meridian) si vous l'avez
uv sync
docker compose up -d postgres      # PostgreSQL sur localhost:5435 (port du kit), schéma appliqué automatiquement
uv run pytest -q                   # 45 tests : normalisation, clés de contrôle, interprétation des réponses VIES

uv run meridian-tva profile        # phase 1 : regarder le fichier avant de coder (pays, formes, vides)
uv run meridian-tva load           # charge les 10 000 lignes, verdict structurel + motif, numéros dédoublonnés (idempotent)
uv run meridian-tva stats          # répartition par motif, appels VIES évités
uv run meridian-tva status         # États membres indisponibles dans VIES en ce moment
uv run meridian-tva campaign --limit 200 --include-ids 101,201   # mode échantillon (quelques minutes) ; Ctrl+C puis relance = reprise
uv run meridian-tva campaign --par-pays 4                         # campagne complète : 4 États membres en parallèle, un appel à la fois par État
uv run meridian-tva campaign --pays FR --par-pays 1               # ne traiter qu'un État (ou --exclure-pays FR pour reporter le plus limité)
uv run meridian-tva report         # docs/rapport-reconciliation.md
uv run meridian-tva api            # http://127.0.0.1:8000/docs
```

Toute la pile (base + API) en une commande : `docker compose up -d --build` (API sur http://localhost:8000).
Poste avec interception TLS (`CERTIFICATE_VERIFY_FAILED`) : `uv sync --native-tls` et `NATIVE_TLS=1` dans `.env`.

## Ce que fait chaque étape

1. **Normalisation** (`normalize.py`) : détection des six formes de vide avant tout traitement, suppression du bruit de saisie
   (casse, espaces, points, tirets, barres), ajout du préfixe pays depuis `pays_declare` quand le numéro n'en a pas.
   Rien n'est « réparé » : un O à la place d'un 0 reste une lettre parasite.
2. **Verdict structurel** (`structural.py`) : `VALIDE_STRUCTURE` (format et clé corrects), `INVALIDE_STRUCTURE` (motifs
   `LONGUEUR_INVALIDE`, `FORMAT_INVALIDE`, `CARACTERES_INVALIDES`, `CLE_INVALIDE`, `PAYS_INCOHERENT`), `HORS_PERIMETRE`
   (`PAYS_HORS_UE` pour GB/UK, `PAYS_INCONNU` pour ZZ/QQ/XX, `PAYS_NON_COUVERT`), `ABSENT`. Un verdict « structurellement
   valide » signifie seulement que le numéro *pourrait* exister : il ne garantit ni l'existence, ni l'attribution au client.
3. **Chargement** (`load.py`) : `lignes_referentiel` (une ligne par ligne du fichier, clé `id`, valeur brute conservée) et
   `numeros` (un numéro normalisé = une entité, `nb_lignes` compte les doublons). `INSERT ... ON CONFLICT` : un rechargement ne
   duplique rien et ne touche pas à l'historique VIES.
4. **Campagne VIES** (`campaign.py`) : seuls les numéros éligibles et dédoublonnés sont interrogés, un à la fois, avec
   temporisation. Chaque réponse est stockée datée, avec son code et sa réponse brute (JSONB). Verdict définitif = jamais
   rappelé ; indéterminé transitoire = réessayé à la campagne suivante, mais jamais indéfiniment : au-delà de 2 exécutions
   l'ayant tenté sans verdict (`--max-relances`), le numéro reste indéterminé et la campagne l'annonce au démarrage. Dans
   une même exécution, chaque numéro n'est traité qu'une fois (trois appels au plus). `IP_BLOCKED` arrête la campagne.
5. **API** (`api.py`) : `GET /verifier/{numero}?pays=FR&max_age_hours=24` renvoie verdict, `origine` (`vies_live` | `cache` |
   `structurel`), `verifie_le`, `age_secondes`, `fraicheur` (`fraiche` | `perimee` | `aucune`), motif, code VIES, nom et
   adresse, `request_identifier`, et un booléen `facturation_hors_taxe_possible` (vrai uniquement si valide et frais).
6. **Rapport** (`report.py`) : régénéré depuis la base par une commande.

## Les trois états, et les deux autres

VIES ne répond pas oui ou non : il répond `valid` vrai ou faux, ou l'un de treize codes d'erreur, tous en HTTP 200.
Le mapping est explicite (`vies_client.py`) : `VALID` → valide ; `INVALID` → invalide ; `MS_UNAVAILABLE`, `SERVICE_UNAVAILABLE`,
`TIMEOUT`, `*_MAX_CONCURRENT_REQ*`, erreurs réseau, HTTP ≠ 200 → **indéterminé, à réessayer** ; `INVALID_INPUT` → indéterminé
définitif ; `IP_BLOCKED`, `VAT_BLOCKED`, `INVALID_REQUESTER_INFO` → arrêt. Une indisponibilité n'est jamais enregistrée comme
une invalidité. Au niveau du référentiel s'ajoutent deux états que la direction financière doit voir séparément :
**hors périmètre** (GB/UK depuis le Brexit : régime export, pas VIES ; codes pays inexistants) et **absent**.

Les 974 lignes déclarées FR sont des clients domestiques : un numéro FR valide ne donne aucun droit à une facture hors taxe
intracommunautaire. Le rapport le rappelle ; l'API répond pour tous les pays couverts, la règle d'exonération relève de la
facturation.

## Ce qu'il faut savoir sur VIES (mesuré le 07/09/2026)

- Latence de 0,1 s pour un numéro inexistant à 6 à 8 s pour un numéro valide : calibrer sur des numéros faux sous-estime
  le temps d'une campagne d'un facteur 10. À 1,5 s de temporisation plus la latence, la campagne complète demande plusieurs
  heures : elle se lance tôt, l'échantillon de 200 sert à démontrer.
- La limite de requêtes concurrentes est **globale par État membre**, tous utilisateurs confondus : deux appels
  simultanés vers le même registre ne font que provoquer `MS_MAX_CONCURRENT_REQ`. La campagne n'envoie donc jamais plus
  d'un appel à la fois par État, avec attente croissante en cas de limitation. En revanche, des États différents sont des
  registres différents : `--par-pays 4` traite quatre États en parallèle et divise la durée d'autant (le jeu en compte
  dix). Une limite globale au seuil non publié existe aussi : si `GLOBAL_MAX_CONCURRENT_REQ` apparaît, la campagne le
  signale et il faut réduire `--par-pays`. Vérifié en base le 08/09/2026 : les fenêtres BE, DK, FI et FR se chevauchent
  (démarrage simultané à 10h34), IT prend le relais dès que FI se termine, et ainsi de suite.
- **Chaque registre a son propre rythme, et il change avec l'heure.** Campagne du 08/09/2026 en journée : IT répond en
  0,3 s, LU en 0,5 s, DK en 11 s ; le registre français refuse plus d'un appel sur deux à 1,5 s d'intervalle
  (`MS_MAX_CONCURRENT_REQ`) alors qu'il accepte un appel toutes les 20 à 30 s. La temporisation est donc **adaptative par
  worker** : elle double à chaque refus (5, 10, 20, 30 s maximum) et redescend de 20 % à chaque verdict obtenu. Le registre
  le plus limité peut être reporté à la nuit (`--exclure-pays FR`, puis `--pays FR` le soir).
- Le numéro de consultation (`requestIdentifier`), preuve opposable à l'administration, n'est renvoyé que si le numéro de TVA
  du demandeur est transmis (`VIES_REQUESTER_*` dans `.env`).
- L'Allemagne (et d'autres) ne renvoient ni nom ni adresse (`---`) : un « valide » ne prouve pas l'attribution au client.
- `GET /check-status` liste les États membres indisponibles : à consulter avant une campagne (`meridian-tva status`).
- Seuls deux numéros du jeu sont réels (SA DANONE, ligne 101 ; SA ORANGE, ligne 201) : la campagne renverra « valide » pour
  eux et « invalide » pour tous les autres numéros structurellement corrects. C'est attendu, et dit dans le rapport.

## Numéros britanniques et Brexit

VIES ne connaît plus le Royaume-Uni : `POST check-vat-number` avec `countryCode: GB` renvoie `INVALID_INPUT`
(vérifié le 08/09/2026), et la liste des États de `check-status` contient `XI` (Irlande du Nord, toujours dans le
système TVA de l'Union pour les biens) mais pas `GB`. Les 208 lignes GB/UK du référentiel sont donc classées
« hors périmètre » avec le motif `PAYS_HORS_UE`, et l'API répond `hors_perimetre` pour elles. Un numéro britannique reste
vérifiable, mais ailleurs : l'API de HMRC (`api.service.hmrc.gov.uk/organisations/vat/check-vat-number/lookup/{vrn}`)
exige désormais des identifiants d'application (réponse `MISSING_CREDENTIALS`, HTTP 401, mesurée le 08/09/2026) ; et une
vente au Royaume-Uni relève du régime des exportations, pas de la livraison intracommunautaire.

## Résultats du 07/09/2026

| Étape | Résultat |
|---|---|
| Chargement | 10 000 lignes en 0,5 s ; rechargement : 10 000 → 10 000 (idempotent) |
| Verdicts structurels (lignes) | 6 615 valides (66,2 %) ; 2 605 invalides (clé 1 341, longueur 726, caractères 453, format 85) ; 519 hors périmètre ; 261 absents |
| Réduction des appels VIES | 10 000 → **6 302** numéros distincts éligibles (**− 37,0 %**), dont 313 doublons évités |
| Campagne échantillon (200 numéros + lignes 101 et 201) | 220 appels, 16 min, latence moyenne 1,8 s ; **16 valides, 183 invalides, 1 indéterminé** (`MS_MAX_CONCURRENT_REQ` ×3, réessayé à la relance) |
| Concordance d'identité | 1 seul valide concordant (SA ORANGE) ; 15 numéros belges existent dans VIES mais désignent d'autres entreprises : à corriger, pas d'exonération |
| Reprise | relance : « à vérifier maintenant : 6 103 » ; les 199 verdicts définitifs ne sont pas rappelés |
| API | `/verifier/BE0415621046` → `origine: cache`, `fraicheur: fraiche` ; `/verifier/FR27552032534` → `indetermine` (VIES limite le débit) ; `?max_age_hours=0` → nouvel appel VIES |

Le rapport complet est dans `docs/rapport-reconciliation.md` (régénéré par `uv run meridian-tva report`).

## Une seule exécution à la fois

Un verrou (`logs/run.lock`, `msvcrt` sous Windows, `fcntl` ailleurs) refuse un second `load` ou une seconde `campaign`
pendant qu'une exécution tourne : deux campagnes en parallèle doubleraient les appels à VIES, dont la limite de requêtes
concurrentes est globale par État membre. Le second processus s'arrête avec le code 3. Le verrou est libéré à la fin du
processus, Ctrl+C compris.

Ce verrou répond aussi à un comportement observé avec `uv` 0.9.3 sous Windows : dans un environnement tout juste créé par
`uv sync`, le premier `uv run meridian-tva …` lançait la commande deux fois en parallèle (constaté en base : 10 000
insertions puis 10 000 mises à jour pour un seul `load`). Un lancement direct par `.venv/Scripts/meridian-tva` ou
`uv run python -m meridian_tva` ne le fait pas, et un premier `uv run meridian-tva --help` suffit à l'éviter.

## Mémoire et ressources

- Conteneurs plafonnés (`deploy.resources.limits`) : PostgreSQL 512 MB, API 256 MB. Le référentiel et son historique VIES
  pèsent quelques dizaines de MB.
- Le chargement lit le CSV en une passe (10 000 lignes, moins de 20 MB en mémoire) ; la campagne traite un numéro à la fois
  et commite après chacun.
- Docker Desktop tourne dans une machine virtuelle WSL2 qui, sans limite, peut prendre la moitié de la RAM et ne pas la
  rendre. Modèle de `%USERPROFILE%\.wslconfig` dans `docs/wslconfig.example` (10 GB, récupération progressive) ; il
  s'applique après `wsl --shutdown`. Après une session : `docker compose down` ; de temps en temps : `docker builder prune`.

## Structure du dépôt

```
src/meridian_tva/   config.py, normalize.py, structural.py, load.py, vies_client.py, campaign.py, report.py, api.py, __main__.py
sql/schema.sql      tables lignes_referentiel, numeros, verifications_vies ; vues etat_vies_courant, etat_numeros, etat_lignes
tests/              45 tests (normalisation, clés de contrôle des 10 pays sur des numéros réels, interprétation VIES)
data/               numeros_tva.csv et .xlsx (kit)
docs/               note-architecture.md, rapport-reconciliation.md (généré), journal-de-bord.md, docker-compose.fourni.yml
docker-compose.yml  PostgreSQL (kit, port 5435) + API ; Dockerfile de l'API
```

## Auteur

AFlo59 — brief Simplon « Valider un référentiel de TVA intracommunautaire », septembre 2026.
