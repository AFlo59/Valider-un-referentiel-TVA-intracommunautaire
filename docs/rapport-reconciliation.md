# Rapport de réconciliation du référentiel TVA

*Généré le 08/09/2026 08:18 UTC par `uv run meridian-tva report`. Dernière vérification VIES : 08/09/2026 08:00 UTC.*

## 1. Réponse à la question centrale (par ligne du référentiel)

| État final | Lignes | Part | Signification |
|---|---|---|---|
| valide | 46 | 0.5 % | numéro confirmé par VIES à la date indiquée : facturation hors taxe possible si les autres conditions sont réunies |
| invalide | 3045 | 30.4 % | structure fausse (format ou clé) ou numéro non reconnu par VIES : facturer avec TVA, corriger le référentiel |
| indetermine | 6129 | 61.3 % | structure correcte mais non confirmé par VIES (non encore interrogé, ou service indisponible) : ne jamais facturer hors taxe sur cette base |
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
| Appels VIES effectués à ce jour | 485 | 478 numéros distincts, latence moyenne 3442 ms |

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
| IT | 947 | 642 | 276 | 0 | 29 |
| PT | 947 | 675 | 246 | 0 | 26 |
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
| invalide | INVALID | 420 | 3517 | 17013 | 0 |
| valide | VALID | 45 | 3877 | 10694 | 0 |
| indetermine | MS_MAX_CONCURRENT_REQ | 13 | 430 | 2202 | 0 |

**Concordance d'identité.** Sur 45 numéros valides dans VIES, **1** porte un nom concordant avec la raison sociale du référentiel et **44** désignent une autre entreprise. Un numéro « valide » qui n'est pas celui du client facturé n'ouvre aucun droit à l'exonération : ces lignes sont à corriger avec le client avant toute facture hors taxe (les numéros belges sont attribués séquentiellement, un numéro à clé correcte existe souvent).

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
| BE0634782846 | SRL GEMBALIM | Chaussée de Namur 52, 5030 Gembloux | Vela Distribution Lda | NON | 08/09/2026 07:04 | 9475 |
| BE0644779289 | BV TOTAAL RENOVATIE DELRUE | Marconistraat 5, 8400 Oostende | Kappa Technologies SAS | NON | 08/09/2026 07:04 | 2157 |
| BE0648617818 | SCS BORIS GILSON ENTREPRISES | Rue Batta SART 150/a, 4845 Jalhay | Ardent Distribution SAS | NON | 08/09/2026 07:04 | 3164 |
| BE0651797042 | Sawicz, Eva | Rue Joseph Muller 95/A4, 4607 Dalhem | Prima Industries GmbH | NON | 08/09/2026 07:05 | 989 |
| BE0675387640 | Callens, Katrien | Graaf de Smet de Naeyerlaan 129, 8500 Kortrijk | Global Services GmbH | NON | 08/09/2026 07:06 | 3737, 7399 |
| BE0675715064 | Leys, Dennis | Kinderstraat 1/GL-R, 2547 Lint | Fabrica Trading A/S | NON | 08/09/2026 07:06 | 2714 |
| BE0678796595 | Cool, Laurence | Rue du Hoek 10, 1630 Linkebeek | Batavia Materials SARL | NON | 08/09/2026 07:06 | 9586 |
| BE0684515835 | Kongnaka, Sivilai | Bakendonk 25, 2200 Herentals | Hanse Consulting Sp. z o.o. | NON | 08/09/2026 07:07 | 4866 |
| BE0684835737 | Geelen, Philippe | Rue du Panorama 13, 4680 Oupeye | Delta Distribution GmbH | NON | 08/09/2026 07:07 | 1060 |
| BE0686905104 | Limbourg, Dany | Rue de Favarcq 183, 7970 Beloeil | Prima Services Oy | NON | 08/09/2026 07:07 | 2049 |
| BE0702885556 | Janssen, Laura | Diestersteenweg 404, 3680 Maaseik | Textil Distribution Lda | NON | 08/09/2026 07:08 | 7356 |
| BE0722907742 | Inem, Fatma | Burgemeester Van Ackerwijk M 3, 9240 Zele | Azur Services SA | NON | 08/09/2026 07:09 | 1588 |
| BE0724642359 | Moustie, Aron | Louis van Beethovenstraat 45/3, 1070 Anderlecht | Vertex Technologies NV | NON | 08/09/2026 07:09 | 5483 |
| BE0729774451 | BV JELOBA | Clemenceaustraat 185, 2860 Sint-Katelijne-Waver | Vertex Materials SA | NON | 08/09/2026 07:09 | 8338 |
| BE0746905443 | BV Team Platteeuw | Kwadestraat 53, 8800 Roeselare | Alpine Distribution Oy | NON | 08/09/2026 07:10 | 7815 |
| BE0766554376 | BV Reno Solar Screens | Nijverheidsstraat 9 unit 1, 2990 Wuustwezel | Meridian Technologies GmbH | NON | 08/09/2026 07:11 | 2211 |
| BE0776547257 | Devresse, Cindy | Rue de Nanwet 33, 6922 Wellin | Lumen Industries Lda | NON | 08/09/2026 07:12 | 6280 |
| BE0781825146 | BV HVDS Management & Consultancy | Vaaltweg 23, 3020 Herent | Vela Distribution Sp. z o.o. | NON | 08/09/2026 07:12 | 6721 |
| BE0783258370 | CommV BG Concepts | Kwetterstraat 6, 3130 Begijnendijk | Delta Consulting SA | NON | 08/09/2026 07:12 | 2306 |
| BE0783644786 | Vanhemelryck, Logan | Diesbeekstraat 43, 1654 Beersel | Kappa Distribution Sp. z o.o. | NON | 08/09/2026 07:12 | 4957 |
| BE0786259828 | BV Vrije Stijl | Oevelenberg 41, 2275 Lille | Verso Trading Sp. z o.o. | NON | 08/09/2026 07:12 | 2127 |
| BE0797739480 | CommV FGAcademy | Mereldreef 43, 3140 Keerbergen | Meridian Services GmbH | NON | 08/09/2026 07:13 | 1938 |
| BE0801646305 | BV APOLLO MANAGEMENT & CONSULTING | Hulststraat 110, 3080 Tervuren | Alpine Industries SARL | NON | 08/09/2026 07:13 | 8702 |
| BE0804675178 | SRL GROSSI RAFAEL | Rue Is. Parmentier 305, 5300 Andenne | Solaris Services GmbH | NON | 08/09/2026 07:15 | 3472 |
| BE0805234909 | SRL Orion Pax | Rue de la Giloterie 19, 5070 Fosses-la-Ville | Delta Foods Sp. z o.o. | NON | 08/09/2026 07:15 | 1056 |
| BE0832147459 | BV Individual Light and Technical Solutions | Roosbeeksestraat 31, 3370 Boutersem | Textil Technologies Sp. z o.o. | NON | 08/09/2026 07:16 | 1432 |
| BE0870549264 | SPRL PATRICK ET SES JARDINS DU LUXEMBOURG | Rue de Liège 2, 5300 Andenne | Orion Transports Sp. z o.o. | NON | 08/09/2026 07:18 | 8208 |
| BE0871093949 | Van Landuyt, Jan | Bruul 6, 9700 Oudenaarde | Batavia Consulting NV | NON | 08/09/2026 07:19 | 6017 |
| BE0879769115 | Bossuyt, Kris | Vlasstraat 7, 8780 Oostrozebeke | Prima Logistics BV | NON | 08/09/2026 07:19 | 6321 |
| FR89380129866 | SA ORANGE | 111 QUAI DU PRESIDENT ROOSEVELT, 92130 ISSY LES MOULINEAUX | SA ORANGE | oui | 07/09/2026 19:58 | 201 |

Numéros éligibles restant à trancher (non interrogés ou indéterminés transitoires) : **5837**. Relancer `uv run meridian-tva campaign` reprend exactement là : les verdicts définitifs ne sont jamais rappelés.

## 7. Durée de validité d'un verdict

VIES ne répond que pour l'instant présent. Chaque verdict est stocké avec sa date ; l'API le sert comme « frais » pendant 24 h puis le revérifie. La facturation doit consulter l'API avant chaque émission hors taxe, et conserver le numéro de consultation VIES (`request_identifier`) sur la facture : il n'est délivré que si le numéro de TVA de Meridian est transmis en tant que demandeur (non configuré : à renseigner dans .env).
