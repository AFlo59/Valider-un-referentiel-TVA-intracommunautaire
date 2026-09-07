# Rapport de réconciliation du référentiel TVA

*Généré le 07/09/2026 19:59 UTC par `uv run meridian-tva report`. Dernière vérification VIES : 07/09/2026 19:58 UTC.*

## 1. Réponse à la question centrale (par ligne du référentiel)

| État final | Lignes | Part | Signification |
|---|---|---|---|
| valide | 16 | 0.2 % | numéro confirmé par VIES à la date indiquée : facturation hors taxe possible si les autres conditions sont réunies |
| invalide | 2795 | 27.9 % | structure fausse (format ou clé) ou numéro non reconnu par VIES : facturer avec TVA, corriger le référentiel |
| indetermine | 6409 | 64.1 % | structure correcte mais non confirmé par VIES (non encore interrogé, ou service indisponible) : ne jamais facturer hors taxe sur cette base |
| hors_perimetre | 519 | 5.2 % | pays hors UE (GB/UK), code pays inexistant (ZZ, QQ, XX) : à requalifier avec le client, régime export le cas échéant |
| absent | 261 | 2.6 % | aucun numéro saisi : à collecter auprès du client |
| **Total** | **10000** | 100 % | |

## 2. Entonnoir : de 10 000 lignes aux appels VIES nécessaires

| Étape | Lignes ou numéros | Commentaire |
|---|---|---|
| Lignes reçues | 10000 | fichier `numeros_tva.csv` |
| Numéro absent | 261 | six formes de vide : '', ' ', '-', 'N/A', 'null', 'NU.LL' |
| Hors périmètre VIES | 519 | GB/UK (Brexit), codes ZZ/QQ/XX |
| Structure invalide | 2605 | longueur, caractères, format ou clé de contrôle |
| Structure valide | 6615 | candidats à VIES, avant dédoublonnage |
| Doublons parmi les candidats | 313 | même numéro normalisé (pays + numéro), vides exclus |
| **Appels VIES nécessaires** | **6302** | contre 10 000 pour une approche naïve : réduction de 37.0 % |
| Appels VIES effectués à ce jour | 204 | 200 numéros distincts, latence moyenne 2002 ms |

## 3. Verdicts structurels et motifs (par ligne)

| Verdict | Motif | Lignes | % |
|---|---|---|---|
| VALIDE_STRUCTURE | OK | 6615 | 66.2 |
| INVALIDE_STRUCTURE | CLE_INVALIDE | 1341 | 13.4 |
| INVALIDE_STRUCTURE | LONGUEUR_INVALIDE | 726 | 7.3 |
| INVALIDE_STRUCTURE | CARACTERES_INVALIDES | 453 | 4.5 |
| HORS_PERIMETRE | PAYS_INCONNU | 311 | 3.1 |
| ABSENT | NUMERO_ABSENT | 261 | 2.6 |
| HORS_PERIMETRE | PAYS_HORS_UE | 208 | 2.1 |
| INVALIDE_STRUCTURE | FORMAT_INVALIDE | 85 | 0.9 |

Traitement de chaque famille de motifs : `OK` → vérification VIES ; `CLE_INVALIDE`, `LONGUEUR_INVALIDE`, `FORMAT_INVALIDE`, `CARACTERES_INVALIDES`, `PAYS_INCOHERENT` → invalide sans appel VIES, correction à demander au client ; `NUMERO_ABSENT` → à collecter ; `PAYS_HORS_UE`, `PAYS_INCONNU`, `PAYS_NON_COUVERT` → hors périmètre, requalification manuelle.

## 4. Répartition par pays déclaré

| Pays déclaré | Lignes | Structure OK | Structure KO | Hors périmètre | Absents |
|---|---|---|---|---|---|
| FR | 974 | 680 | 268 | 0 | 26 |
| DK | 961 | 669 | 269 | 0 | 23 |
| BE | 959 | 673 | 257 | 0 | 29 |
| LU | 956 | 677 | 255 | 0 | 24 |
| SE | 949 | 651 | 271 | 0 | 27 |
| PT | 947 | 675 | 246 | 0 | 26 |
| IT | 947 | 642 | 276 | 0 | 29 |
| NL | 947 | 655 | 264 | 0 | 28 |
| PL | 939 | 685 | 234 | 0 | 20 |
| FI | 902 | 608 | 265 | 0 | 29 |
| ZZ | 115 | 0 | 0 | 115 | 0 |
| QQ | 109 | 0 | 0 | 109 | 0 |
| UK | 104 | 0 | 0 | 104 | 0 |
| GB | 104 | 0 | 0 | 104 | 0 |
| XX | 87 | 0 | 0 | 87 | 0 |

## 5. Doublons

Définition retenue : deux lignes sont des doublons si elles portent le même numéro normalisé (préfixe pays résolu + numéro sans bruit de saisie). Les lignes sans numéro ne sont jamais des doublons entre elles.

- Numéros distincts (non vides) : **9301** pour 9739 lignes portant un numéro
- Lignes en trop : **438** réparties en 396 groupes
- Sur les seuls numéros éligibles VIES : 313 appels évités par le dédoublonnage

| Numéro normalisé | Lignes | Canaux | Formes saisies |
|---|---|---|---|
| DK71704289 | 6 | portail_client, reprise_erp | DK 7170 4289 | DK.71704289 | DK71704289 |
| BE0282330178 | 5 | crm, import_fournisseur, reprise_erp | 02.82330178 | 0282330178 |
| DK91970813 | 4 | crm, portail_client, reprise_erp |   DK91970813  | DK.91970813 | dk91970813 |
| FI64379216 | 4 | crm, portail_client, reprise_erp | FI-64379216 | FI64379216 | fi64379216 |
| NL785427788B39 | 4 | crm, reprise_erp | NL 7854 27788B39 | NL.785427788B39 | nl785427788b39 |
| PL2944016503 | 4 | portail_client, reprise_erp |   PL2944016503  | PL 2944 016503 | PL.2944016503 | PL2944016503 |
| PT100405711 | 4 | crm, import_fournisseur, portail_client, saisie_manuelle |   PT100405711  | PT-100405711 | PT100405711 |
| UK26062918 | 4 | crm, portail_client | UK.26062918 | UK26062918 | uk26062918 |

## 6. Vérification en ligne (VIES)

| État | Code VIES | Numéros | Latence moyenne (ms) | Latence max (ms) | Avec n° de consultation |
|---|---|---|---|---|---|
| invalide | INVALID | 183 | 1970 | 5883 | 0 |
| valide | VALID | 16 | 2503 | 7061 | 0 |
| indetermine | MS_MAX_CONCURRENT_REQ | 1 | 253 | 253 | 0 |

**Concordance d'identité.** Sur 16 numéros valides dans VIES, **1** porte un nom concordant avec la raison sociale du référentiel et **15** désignent une autre entreprise. Un numéro « valide » qui n'est pas celui du client facturé n'ouvre aucun droit à l'exonération : ces lignes sont à corriger avec le client avant toute facture hors taxe (les numéros belges sont attribués séquentiellement, un numéro à clé correcte existe souvent).

| Numéro valide | Nom (VIES) | Adresse (VIES) | Raison sociale (référentiel) | Concordance | Vérifié le | Lignes |
|---|---|---|---|---|---|---|
| BE0415621046 | NV PLUTO | Merellaan 46, 9400 Ninove | Papyrus Distribution SARL | NON | 07/09/2026 19:41 | 5443 |
| BE0422449945 | NV LICHT | Europaweg 1, 3560 Lummen | Atlantic Consulting Lda | NON | 07/09/2026 19:41 | 4105 |
| BE0429249051 | SA SA Jean Hamays | Rue de la Grande Ronce 30, 7191 Ecaussinnes | Orion Transports Sp. z o.o. | NON | 07/09/2026 19:42 | 2569 |
| BE0435948583 | ASBL Aremis | Rue de la Consolation 83, 1030 Schaerbeek | Azur Technologies SAS | NON | 07/09/2026 19:42 | 7289 |
| BE0445376884 | BV De Gulden Cop | Kasteelstraat 1, 9140 Temse | Fabrica Technologies GmbH | NON | 07/09/2026 19:43 | 8330 |
| BE0450634086 | NV KIKMOLEN | Kikmolenstraat 3, 3630 Maasmechelen | Kappa Transports A/S | NON | 07/09/2026 19:43 | 4447 |
| BE0455010271 | BVBA PAPER INSERT COUPON BELGIUM | Maalderstraat 5, 2890 Puurs-Sint-Amands | Granit Materials Sp. z o.o. | NON | 07/09/2026 19:43 | 1585 |
| BE0458764468 | BVBA Amai | Gierleseweg 10, 2340 Beerse | Vela Industries Sp. z o.o. | NON | 07/09/2026 19:43 | 6136 |
| BE0461778693 | NV M.V.B. The Art of Wiring | Della Faillelaan 20, 2290 Vorselaar | Kappa Foods Sp. z o.o. | NON | 07/09/2026 19:43 | 8526 |
| BE0471870059 | BV RIMBERT CONSULTING | Ninoofsesteenweg 323, 1500 Halle | Prima Technologies BV | NON | 07/09/2026 19:43 | 7892 |
| BE0472824223 | BV CUYCKENS | Kattestraat 135, 2890 Puurs-Sint-Amands | Prima Distribution Oy | NON | 07/09/2026 19:43 | 417 |
| BE0503858778 | BO DEL MONTE ITALY SARL | VIA FIESCHI 6/5, IT-1612 16121 GENOVA | Granit Industries BV | NON | 07/09/2026 19:44 | 2933 |
| BE0557669925 | Straps, Jean-Marie | Rue Steenvelt 12, 1180 Uccle | Corvus Distribution BV | NON | 07/09/2026 19:46 | 8524 |
| BE0559903992 | BV EYE-TEC | Kemelbeekstraat 80/D, 2460 Kasterlee | Vela Trading AB | NON | 07/09/2026 19:46 | 3150 |
| BE0632645084 | BV Batimea | Bijenstraat 11, 9051 Gent | Papyrus Materials Oy | NON | 07/09/2026 19:49 | 1868 |
| FR89380129866 | SA ORANGE | 111 QUAI DU PRESIDENT ROOSEVELT, 92130 ISSY LES MOULINEAUX | SA ORANGE | oui | 07/09/2026 19:58 | 201 |

Numéros éligibles restant à trancher (non interrogés ou indéterminés transitoires) : **6103**. Relancer `uv run meridian-tva campaign` reprend exactement là : les verdicts définitifs ne sont jamais rappelés.

## 7. Durée de validité d'un verdict

VIES ne répond que pour l'instant présent. Chaque verdict est stocké avec sa date ; l'API le sert comme « frais » pendant 24 h puis le revérifie. La facturation doit consulter l'API avant chaque émission hors taxe, et conserver le numéro de consultation VIES (`request_identifier`) sur la facture : il n'est délivré que si le numéro de TVA de Meridian est transmis en tant que demandeur (non configuré : à renseigner dans .env).
