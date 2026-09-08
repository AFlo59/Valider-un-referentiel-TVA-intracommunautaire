# Journal de bord — référentiel TVA

## J1 — cadrage, réduction, chargement

**Lecture du kit.** Le CSV et le XLSX sont strictement identiques (comparés cellule à cellule). Le docker-compose expose
PostgreSQL sur le port hôte **5435**, pas 5432 : première cause d'échec de connexion évitée en lisant le fichier. Le
« module de validation structurelle » annoncé n'est dans aucune ressource ; décision : demander au formateur, et en
attendant le réécrire à partir des spécifications nationales (dix pays, format + clé), avec des tests sur des numéros
publics réels (Danone, Orange, Colruyt, Carlsberg, Nokia, Pirelli, ArcelorMittal, Heineken, Orlen, EDP, Volvo).

**Regarder le fichier avant de coder (`meridian-tva profile`).** Ce que le brief annonce et ce que le jeu contient :

| Brief | Jeu |
|---|---|
| « dix pays » | 15 codes `pays_declare` : les 10 pays UE + ZZ, QQ, XX (311 lignes) + GB, UK (208 lignes) |
| « trois canaux » | 5 valeurs de `source_saisie` |
| « huit ans » | dates du 01/01/2024 au 01/10/2025 |
| « 10 000 numéros » | 10 000 lignes, 9 301 numéros distincts non vides, 261 vides |

Le vide a **six formes** (`''`, `' '`, `-`, `N/A`, `null`, `NU.LL`). Blocage évité de justesse : un premier essai avec
`pandas.read_csv` par défaut donnait 146 vides (il convertit `''`, `N/A` et `null` en NaN et laisse `' '` et `-`) et
perdait la valeur brute. Retour au module `csv` en texte, détection du vide **avant** normalisation, sinon `N/A` devient
le faux numéro « NA » et `null` le faux numéro « NULL » (85 faux doublons).

**Normalisation.** 2 140 lignes portent du bruit de saisie (casse, espaces, points, tirets), 532 n'ont pas de préfixe pays.
Décision : retirer le bruit, ajouter le préfixe depuis `pays_declare`, ne rien réparer (un O n'est pas un 0, un BE à
9 chiffres n'est pas complété). Chaque décision est comptée : elles font varier le total de valides structurels de
plusieurs points.

**Clés de contrôle.** Deux erreurs de ma part corrigées par les tests : un numéro suédois mal recopié (Volvo est
SE556012579001, organisationsnummer 556012-5790), et un exemple néerlandais qui passait par l'ancienne règle mod 11 alors
qu'il devait tester la nouvelle règle mod 97 (remplacé par NL000000093B12, valide seulement sous mod 97).

**Chargement.** 10 000 lignes en 0,5 s. Verdicts : 6 615 structure valide (66,2 %), 2 605 invalides (clé 1 341, longueur 726,
caractères 453, format 85), 519 hors périmètre, 261 absents. 6 302 numéros distincts éligibles à VIES : **3 698 appels
évités (37 %)**. Rechargement immédiat : toujours 10 000 lignes, aucun doublon.

**Mesure de VIES avant la campagne.** Trois appels manuels : Danone valide en 6,7 s, clé fausse « invalide » en 0,12 s,
numéro inventé « invalide » en 0,58 s. Puis GB → `INVALID_INPUT`, un numéro letton → `MS_UNAVAILABLE` (la Lettonie était
indisponible dans `check-status`), l'Allemagne valide mais nom et adresse « --- ». La réponse qui contredit l'attente :
le lien du brief (`GET /rest-api/ms/FR/vat/…`) renvoie `isValid: false` avec `userError: MS_MAX_CONCURRENT_REQ` pour le
numéro de Danone, qui est valide. Conséquence directe sur le modèle : le verdict ne dérive jamais d'un seul champ, le code
brut est conservé, et l'indisponibilité est un troisième état, réessayé. Calcul : 6 302 appels à 1,5 s + latence
(0,1 à 8 s) = 5 à 10 heures pour le référentiel entier ; l'échantillon de 200 sert à la démonstration.

## J2 — vérification en ligne et API

**Campagne échantillon (200 numéros + lignes 101 et 201).** Premier appel : `MS_MAX_CONCURRENT_REQ` sur FR27552032534,
puis nouvelle tentative après 10 s, puis 20 s, puis indéterminé. Le piège s'est présenté dès le premier numéro de la
campagne réelle : sans la logique de nouvelles tentatives et sans l'état « indéterminé », Danone aurait été enregistré
invalide. Résultat : 200 numéros, 220 appels, 16 min, latence moyenne 1,8 s (0,03 s pour une erreur, 7,6 s pour Orange) ;
**16 valides, 183 invalides, 1 indéterminé**. Relance avec `--include-ids 101 --limit 1` : « à vérifier maintenant : 6 103 »,
les 199 verdicts définitifs ne sont pas rappelés, Danone est réessayé (encore `MS_MAX_CONCURRENT_REQ` : l'État membre FR
limitait fortement le débit ce soir-là) et reste indéterminé, ce qui est la bonne réponse.

**La surprise de la campagne : 15 numéros belges « valides » qui ne sont pas nos clients.** Les numéros belges sont
attribués séquentiellement ; un numéro synthétique à clé correcte a donc de bonnes chances d'exister. VIES répond
`valid: true` avec le nom d'une autre entreprise (NV PLUTO, BV Batimea…) là où le référentiel dit « Papyrus Distribution
SARL ». Seul SA ORANGE concorde. Conséquence sur le modèle et le rapport : une colonne de concordance nom VIES / raison
sociale, et la règle « valide mais non concordant = à corriger avec le client, pas de facture hors taxe ». Un jury qui ne
voit que « valide » verrait 16 clients exonérables ; il y en a un.

**Interception TLS du poste.** `uv sync` et `requests` échouaient en `CERTIFICATE_VERIFY_FAILED` (proxy/antivirus).
Résolu par `uv sync --native-tls` et `truststore` activé par `NATIVE_TLS=1` : les certificats du système sont utilisés,
la vérification n'est jamais désactivée.

**API.** Contrat typé (Pydantic) pour que `/docs` dise vrai. Décision sur le cas « VIES injoignable et rien en mémoire » :
HTTP 200 avec `verdict = indetermine` et le code d'erreur en motif, plutôt qu'un 503 : l'appelant a une réponse explicite à
traiter comme « ne pas facturer hors taxe ». Avec une valeur périmée en mémoire, elle est servie marquée `perimee` et
`facturation_hors_taxe_possible = false`.

**Rapport.** Régénéré par `meridian-tva report` depuis les vues SQL ; c'est la seule source des chiffres présentés.

**Test final.** Suppression du dossier, nouveau clone, `.env`, `docker compose up -d --build` (base + image de l'API),
`uv sync`, 56 tests, `load`, `campaign --limit 2 --include-ids 201`, `report`, API en conteneur : tout passe. Le test a
révélé un « avant : 10 000 » sur base vide au premier chargement. Après isolation lanceur par lanceur sur des bases
vides : dans un environnement tout juste créé par `uv sync`, le premier `uv run meridian-tva …` (uv 0.9.3, Windows)
exécute la commande deux fois en parallèle (10 000 insertions puis 10 000 mises à jour). L'exécutable direct, `python -m`,
et un `uv run meridian-tva --help` préalable ne le font pas. Aucune campagne réelle n'a été doublée (journaux vérifiés),
mais deux campagnes en parallèle doubleraient les appels à VIES : verrou d'exécution ajouté (`lock.py`, code 3).

**Mémoire.** Conteneurs plafonnés (PostgreSQL 512 MB, API 256 MB), modèle de `.wslconfig` dans `docs/` : la VM WSL2 de
Docker Desktop avait pris 24 GB après une soirée de constructions d'images.

**Campagne complète, 08/09 matin.** Lancée en séquentiel : 6 103 numéros restants à 4 à 6 s l'un, soit 6 à 9 heures.
Question posée : peut-on contourner la lenteur par un « JSON caché » du site ? Non : l'interface web appelle le même
endpoint, VIES ne possède aucune base (il relaie chaque appel au registre national) et il n'existe aucun dump. Ce qui est
légitime : la limite étant par État membre, un worker par État avec un seul appel à la fois par registre. Implémenté
(`--par-pays N`, `ThreadPoolExecutor`, une session HTTP et une connexion par worker, limite `--limit` partagée, arrêt
propre sur Ctrl+C ou code bloquant, avertissement si `GLOBAL_MAX_CONCURRENT_REQ`). Le verrou d'exécution reste valable :
un seul processus, plusieurs threads.

**Campagne complète relancée à 10h34 sur base neuve, 4 États en parallèle.** État à 14h25 (vues SQL) :

| Pays | Vérifiés | Valides | Invalides | Indéterminés | Fenêtre | Latence moyenne |
|---|---|---|---|---|---|---|
| BE | 644 | 39 | 548 | 57 | 10h35 → 12h51 | 3,8 s |
| DK | 620 | 40 | 567 | 13 | 10h34 → 13h30 | 11,1 s |
| FI | 581 | 55 | 526 | 0 | 10h34 → 10h59 | 1,1 s |
| FR | 459 / 643 | 2 | 195 | 262 | 10h35 → en cours | 3,9 s |
| IT | 604 | 0 | 604 | 0 | 10h59 → 11h17 | 0,3 s |
| LU | 652 | 69 | 583 | 0 | 11h17 → 11h39 | 0,5 s |
| NL | 619 | 0 | 602 | 17 | 11h39 → 13h11 | 2,8 s |
| PL | 659 | 4 | 655 | 0 | 12h51 → 13h21 | 0,5 s |
| PT | 650 | 7 | 643 | 0 | 13h12 → 13h33 | 0,5 s |
| SE | 630 | 0 | 630 | 0 | 13h21 → 13h45 | 0,7 s |

Le parallélisme est visible dans les fenêtres : quatre États démarrent ensemble, chaque État suivant prend le relais du
premier terminé. Trois enseignements : (1) chaque registre a son rythme propre, de 0,3 s (IT) à 11 s (DK) ; (2) le
registre français refuse plus d'un appel sur deux en journée (`MS_MAX_CONCURRENT_REQ`) mais accepte un appel toutes les
20 à 30 s, d'où une temporisation adaptative par worker (5, 10, 20, 30 s, puis retour progressif) plutôt que trois
tentatives perdues par numéro ; (3) 216 numéros « valides » pour l'instant, presque tous des numéros existants attribués
à d'autres entreprises (BE, DK, FI, LU numérotent séquentiellement) : la concordance d'identité du rapport n'est pas un
détail, c'est le cœur du verdict. Ajout des filtres `--pays` / `--exclure-pays` pour reporter un registre limité à la
nuit.

**Brexit, vérifié.** `POST check-vat-number` avec `GB` → `INVALID_INPUT` ; `check-status` liste 28 codes dont `XI` et
sans `GB`. HMRC expose son propre service de vérification, mais il exige désormais des identifiants d'application
(HTTP 401 `MISSING_CREDENTIALS`) : hors périmètre du brief, mentionné dans le README.

**Pas de boucle sans fin.** Question posée : « sera réessayé » veut-il dire indéfiniment ? Dans une exécution, chaque
numéro est traité une fois (trois appels au plus). Entre exécutions, les indéterminés revenaient à chaque relance sans
limite : plafond ajouté, deux exécutions par numéro (`--max-relances 2`, soit six appels), annoncé au démarrage.
Vérifié en base : chaque numéro traité a exactement une vérification à ce stade.

**14h28 : ancien worker FR arrêté, relance du nouveau code sur tout sauf la France** (`--par-pays 4 --exclure-pays FR`)
pour les 87 indéterminés BE/DK/NL ; la temporisation adaptative se voit immédiatement (« [BE] temporisation portée à
8 s »). La France (184 jamais tentés + 262 indéterminés, tous des clients domestiques sans enjeu d'exonération) est
reportée au soir : `uv run meridian-tva campaign --pays FR`.
