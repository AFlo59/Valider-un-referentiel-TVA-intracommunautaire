# Rapport de réconciliation du référentiel TVA

*Généré le 08/09/2026 12:33 UTC par `uv run meridian-tva report`. Dernière vérification VIES : 08/09/2026 12:33 UTC.*

## 1. Réponse à la question centrale (par ligne du référentiel)

| État final | Lignes | Part | Signification |
|---|---|---|---|
| valide | 230 | 2.3 % | numéro confirmé par VIES à la date indiquée : facturation hors taxe possible si les autres conditions sont réunies |
| invalide | 8459 | 84.6 % | structure fausse (format ou clé) ou numéro non reconnu par VIES : facturer avec TVA, corriger le référentiel |
| indetermine | 531 | 5.3 % | structure correcte mais non confirmé par VIES (non encore interrogé, ou service indisponible) : ne jamais facturer hors taxe sur cette base |
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
| Appels VIES effectués à ce jour | 6157 | 6126 numéros distincts, latence moyenne 2486 ms |

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
| invalide | INVALID | 5585 | 2575 | 19376 | 0 |
| indetermine | MS_MAX_CONCURRENT_REQ | 325 | 333 | 6731 | 0 |
| valide | VALID | 216 | 3712 | 18657 | 0 |

Par registre national (chaque État membre a son propre rythme et sa propre disponibilité) :

| Pays | Éligibles | Vérifiés | Valides | Invalides | Indéterminés | Jamais interrogés | Latence moyenne (ms) |
|---|---|---|---|---|---|---|---|
| BE | 644 | 644 | 39 | 553 | 52 | 0 | 3853 |
| DK | 620 | 620 | 40 | 580 | 0 | 0 | 11352 |
| FI | 581 | 581 | 55 | 526 | 0 | 0 | 1052 |
| FR | 643 | 467 | 2 | 199 | 266 | 176 | 3881 |
| IT | 604 | 604 | 0 | 604 | 0 | 0 | 288 |
| LU | 652 | 652 | 69 | 583 | 0 | 0 | 497 |
| NL | 619 | 619 | 0 | 612 | 7 | 0 | 2883 |
| PL | 659 | 659 | 4 | 655 | 0 | 0 | 456 |
| PT | 650 | 650 | 7 | 643 | 0 | 0 | 465 |
| SE | 630 | 630 | 0 | 630 | 0 | 0 | 735 |

**Concordance d'identité.** Sur 216 numéros valides dans VIES, **0** portent un nom concordant avec la raison sociale du référentiel et **216** désignent une autre entreprise. Un numéro « valide » qui n'est pas celui du client facturé n'ouvre aucun droit à l'exonération : ces lignes sont à corriger avec le client avant toute facture hors taxe (les numéros belges sont attribués séquentiellement, un numéro à clé correcte existe souvent).

| Numéro valide | Nom (VIES) | Adresse (VIES) | Raison sociale (référentiel) | Concordance | Vérifié le | Lignes |
|---|---|---|---|---|---|---|
| BE0415621046 | NV PLUTO | Merellaan 46, 9400 Ninove | Papyrus Distribution SARL | NON | 08/09/2026 09:03 | 5443 |
| BE0422449945 | NV LICHT | Europaweg 1, 3560 Lummen | Atlantic Consulting Lda | NON | 08/09/2026 09:03 | 4105 |
| BE0429249051 | SA SA Jean Hamays | Rue de la Grande Ronce 30, 7191 Ecaussinnes | Orion Transports Sp. z o.o. | NON | 08/09/2026 09:04 | 2569 |
| BE0445376884 | BV De Gulden Cop | Kasteelstraat 1, 9140 Temse | Fabrica Technologies GmbH | NON | 08/09/2026 09:05 | 8330 |
| BE0455010271 | BVBA PAPER INSERT COUPON BELGIUM | Maalderstraat 5, 2890 Puurs-Sint-Amands | Granit Materials Sp. z o.o. | NON | 08/09/2026 09:08 | 1585 |
| BE0458764468 | BVBA Amai | Gierleseweg 10, 2340 Beerse | Vela Industries Sp. z o.o. | NON | 08/09/2026 09:08 | 6136 |
| BE0461778693 | NV M.V.B. The Art of Wiring | Della Faillelaan 20, 2290 Vorselaar | Kappa Foods Sp. z o.o. | NON | 08/09/2026 09:08 | 8526 |
| BE0471870059 | BV RIMBERT CONSULTING | Ninoofsesteenweg 323, 1500 Halle | Prima Technologies BV | NON | 08/09/2026 09:10 | 7892 |
| BE0472824223 | BV CUYCKENS | Kattestraat 135, 2890 Puurs-Sint-Amands | Prima Distribution Oy | NON | 08/09/2026 09:10 | 417 |
| BE0503858778 | BO DEL MONTE ITALY SARL | VIA FIESCHI 6/5, IT-1612 16121 GENOVA | Granit Industries BV | NON | 08/09/2026 09:15 | 2933 |
| BE0557669925 | Straps, Jean-Marie | Rue Steenvelt 12, 1180 Uccle | Corvus Distribution BV | NON | 08/09/2026 09:20 | 8524 |
| BE0559903992 | BV EYE-TEC | Kemelbeekstraat 80/D, 2460 Kasterlee | Vela Trading AB | NON | 08/09/2026 09:21 | 3150 |
| BE0632645084 | BV Batimea | Bijenstraat 11, 9051 Gent | Papyrus Materials Oy | NON | 08/09/2026 09:29 | 1868 |
| BE0634782846 | SRL GEMBALIM | Chaussée de Namur 52, 5030 Gembloux | Vela Distribution Lda | NON | 08/09/2026 09:29 | 9475 |
| BE0644779289 | BV CASA DELRUE | Marconistraat 5, 8400 Oostende | Kappa Technologies SAS | NON | 08/09/2026 09:29 | 2157 |
| BE0648617818 | SCS BORIS GILSON ENTREPRISES | Rue Batta SART 150/a, 4845 Jalhay | Ardent Distribution SAS | NON | 08/09/2026 09:29 | 3164 |
| BE0651797042 | Sawicz, Eva | Rue Joseph Muller 95/A4, 4607 Dalhem | Prima Industries GmbH | NON | 08/09/2026 09:30 | 989 |
| BE0675387640 | Callens, Katrien | Graaf de Smet de Naeyerlaan 129, 8500 Kortrijk | Global Services GmbH | NON | 08/09/2026 09:31 | 3737, 7399 |
| BE0675715064 | Leys, Dennis | Kinderstraat 1/GL-R, 2547 Lint | Fabrica Trading A/S | NON | 08/09/2026 09:32 | 2714 |
| BE0678796595 | Cool, Laurence | Rue du Hoek 10, 1630 Linkebeek | Batavia Materials SARL | NON | 08/09/2026 09:32 | 9586 |
| BE0686905104 | Limbourg, Dany | Rue de Favarcq 183, 7970 Beloeil | Prima Services Oy | NON | 08/09/2026 09:34 | 2049 |
| BE0702885556 | Janssen, Laura | Diestersteenweg 404, 3680 Maaseik | Textil Distribution Lda | NON | 08/09/2026 09:35 | 7356 |
| BE0722907742 | Inem, Fatma | Burgemeester Van Ackerwijk M 3, 9240 Zele | Azur Services SA | NON | 08/09/2026 09:37 | 1588 |
| BE0724642359 | Moustie, Aron | Louis van Beethovenstraat 45/3, 1070 Anderlecht | Vertex Technologies NV | NON | 08/09/2026 09:38 | 5483 |
| BE0729774451 | BV JELOBA | Clemenceaustraat 185, 2860 Sint-Katelijne-Waver | Vertex Materials SA | NON | 08/09/2026 09:38 | 8338 |
| BE0746905443 | BV Team Platteeuw | Kwadestraat 53, 8800 Roeselare | Alpine Distribution Oy | NON | 08/09/2026 09:39 | 7815 |
| BE0766554376 | BV Reno Solar Screens | Nijverheidsstraat 9 unit 1, 2990 Wuustwezel | Meridian Technologies GmbH | NON | 08/09/2026 09:40 | 2211 |
| BE0776547257 | Devresse, Cindy | Rue de Nanwet 33, 6922 Wellin | Lumen Industries Lda | NON | 08/09/2026 09:40 | 6280 |
| BE0781825146 | BV HVDS Management & Consultancy | Vaaltweg 23, 3020 Herent | Vela Distribution Sp. z o.o. | NON | 08/09/2026 09:40 | 6721 |
| BE0783258370 | CommV BG Concepts | Kwetterstraat 6, 3130 Begijnendijk | Delta Consulting SA | NON | 08/09/2026 09:41 | 2306 |
| BE0783644786 | Vanhemelryck, Logan | Diesbeekstraat 43, 1654 Beersel | Kappa Distribution Sp. z o.o. | NON | 08/09/2026 09:41 | 4957 |
| BE0786259828 | BV Vrije Stijl | Oevelenberg 41, 2275 Lille | Verso Trading Sp. z o.o. | NON | 08/09/2026 09:41 | 2127 |
| BE0797739480 | CommV FGAcademy | Mereldreef 43, 3140 Keerbergen | Meridian Services GmbH | NON | 08/09/2026 09:42 | 1938 |
| BE0801646305 | BV APOLLO MANAGEMENT & CONSULTING | Hulststraat 110, 3080 Tervuren | Alpine Industries SARL | NON | 08/09/2026 09:42 | 8702 |
| BE0804675178 | SRL GROSSI RAFAEL | Rue Is. Parmentier 305, 5300 Andenne | Solaris Services GmbH | NON | 08/09/2026 09:43 | 3472 |
| BE0805234909 | SRL Orion Pax | Rue de la Giloterie 19, 5070 Fosses-la-Ville | Delta Foods Sp. z o.o. | NON | 08/09/2026 09:43 | 1056 |
| BE0832147459 | BV Individual Light and Technical Solutions | Roosbeeksestraat 31, 3370 Boutersem | Textil Technologies Sp. z o.o. | NON | 08/09/2026 09:43 | 1432 |
| BE0870549264 | SPRL PATRICK ET SES JARDINS DU LUXEMBOURG | Rue de Liège 2, 5300 Andenne | Orion Transports Sp. z o.o. | NON | 08/09/2026 09:46 | 8208 |
| BE0879769115 | Bossuyt, Kris | Vlasstraat 7, 8780 Oostrozebeke | Prima Logistics BV | NON | 08/09/2026 09:46 | 6321 |
| DK17404547 | Guldsmeden i Glamsbjerg/          Henning Skovgaard Hansen | Søndergade 19, 5620 Glamsbjerg | Corvus Transports Lda | NON | 08/09/2026 08:50 | 7412 |
| DK18496887 | Park by Maibom | Grønnegade 15, 7430 Ikast | Vela Trading Sp. z o.o. | NON | 08/09/2026 08:52 | 6243 |
| DK20446005 | Regnskabskontoret Det Grå Guld | Lindevej 30, 4850 Stubbekøbing | Nord Industries Sp. z o.o. | NON | 08/09/2026 08:57 | 5100 |
| DK25395417 | I Centrum | Nørregade 8, 7570 Vemb | Granit Technologies A/S | NON | 08/09/2026 09:03 | 9613 |
| DK26282977 | Andersen Sanitet & Varme | Automatikvej 1, 2860 Søborg | Kappa Industries Sp. z o.o. | NON | 08/09/2026 09:04 | 8880 |
| DK26527120 | HG 39 Jannie v/Eiler Haraldsen | Anders Nielsens Vej 29 st mf, 9400 Nørresundby | Granit Industries Lda | NON | 08/09/2026 09:04 | 3504 |
| DK26820456 | MENY, ØSTERGADE 16-18 ApS | Østergade 16-18, 4700 Næstved | Meridian Services SAS | NON | 08/09/2026 09:05 | 8842 |
| DK27370500 | Jesper Vonsild Tømrer | Svalevej 32, 7100 Vejle | Baltic Materials Lda | NON | 08/09/2026 09:06 | 6114 |
| DK29081972 | Baunhøj Connexion v/Anette BaunhøjOlsen | Ørnebakken 52, 2840 Holte | Vertex Distribution SpA | NON | 08/09/2026 09:08 | 1505 |
| DK29373183 | DM Følgebiler | Ulvehavevej 42A, 7100 Vejle | Cobalt Services SA | NON | 08/09/2026 09:10 | 6306 |
| DK29787034 | EGA-TEKNIK ApS | Myntestien 22, 3310 Ølsted | Vela Foods Lda | NON | 08/09/2026 09:11 | 2183 |
| DK30194381 | DRONNINGBORG MURERFORRETNING ApS | Fjordlyvej 3, 8930 Randers NØ | Cobalt Consulting BV | NON | 08/09/2026 09:13 | 6141 |
| DK31097274 | Sandfield Software | Joensuuvej 16, 4000 Roskilde | Alpine Transports GmbH | NON | 08/09/2026 09:16 | 2296 |
| DK31137160 | x.i.stenz v/Lykke Stenz Lindgren | Nygade 27, 3720 Aakirkeby | Baltic Trading SARL | NON | 08/09/2026 09:16 | 3643 |
| DK32747310 | Sydsjælland Autorude Service      v/Simon Stitz Marquardsen | Sorøvej 509, 4700 Næstved | Atlantic Logistics BV | NON | 08/09/2026 09:20 | 2814 |
| DK33111827 | NOS | Grønnevej 249 3 5, 2830 Virum | Metallo Materials SA | NON | 08/09/2026 09:21 | 545 |
| DK37441961 | El Izi Concept Store | Nykær 36 15 tv, 2605 Brøndby | Delta Transports AB | NON | 08/09/2026 09:28 | 5574 |
| DK38305328 | Rustik Coiffure - by Louise Olivia | Rosensgade 34 st th, 8000 Aarhus C | Textil Logistics GmbH | NON | 08/09/2026 09:29 | 9576 |
| DK38419609 | KK Aarhus - Lys og re-design | Nørre Allé 25, 8000 Aarhus C | Nord Transports GmbH | NON | 08/09/2026 09:30 | 2537 |
| DK39183056 | Innargi A/S | Amerika Plads 29, 2100 København Ø | Atlantic Industries BV | NON | 08/09/2026 09:33 | 5162 |
| DK39289067 | Flemming Braasch, 431 Kirke       Hyllinge ApS | Elverdamsvej 308, 4070 Kirke Hyllinge | Lumen Distribution BV | NON | 08/09/2026 09:33 | 9125 |
| DK39690721 | Svedkonceptet ApS | Højbyvej 19, 4320 Lejre | Baltic Transports SpA | NON | 08/09/2026 09:34 | 5486 |
| DK40427538 | SPS Danmark ApS | Spånnebæk 26, 4300 Holbæk | Fabrica Distribution SA | NON | 08/09/2026 09:35 | 2516 |
| DK40966617 | Modelbyggeri ApS | Knabstrup Møllebakke 6, 4440 Mørkøv | Batavia Industries A/S | NON | 08/09/2026 09:36 | 690 |
| DK41277211 | Yes Group Løkken ApS | Vendelbogade 29, 9480 Løkken | Vertex Technologies NV | NON | 08/09/2026 09:38 | 2304, 3538 |
| DK42075442 | Let Bogføring ApS | Slagslundevej 4A, 3550 Slangerup | Vertex Trading Sp. z o.o. | NON | 08/09/2026 09:39 | 9940 |
| DK42676756 | PP import | Fuglebakken 23 1 tv, 4760 Vordingborg | Textil Industries BV | NON | 08/09/2026 09:42 | 6162 |
| DK43060368 | Blikkenslager Daniel Kolbe ApS | Hørve Kirkevej 7B, 4534 Hørve | Corvus Logistics SA | NON | 08/09/2026 09:42 | 7686 |
| DK43075659 | Landbrug v/Jais Andreasen | Havndalvej 59, 8970 Havndal | Metallo Distribution BV | NON | 08/09/2026 09:43 | 25 |
| DK43624423 | Thejs Hjort Christiansen | Tronkærvej 61, 8530 Hjortshøj | Vertex Services SAS | NON | 08/09/2026 09:43 | 279, 4666 |
| DK44383918 | Krøldrup Krea | Borgmestervej 11A, 8700 Horsens | Papyrus Logistics AB | NON | 08/09/2026 09:44 | 1106 |
| DK44913852 | Compenso Energy Balance 6 ApS | Gammelbrovej 8B, 4300 Holbæk | Vela Distribution SpA | NON | 08/09/2026 09:45 | 7123 |
| DK44945894 | Bekker Kommunikation | Toftøjevej 35A, 2720 Vanløse | Atlantic Distribution Oy | NON | 08/09/2026 09:46 | 548, 5710 |
| DK45406784 | Thy GSD | Boulevarden 34 4 tv, 9000 Aalborg | Fabrica Trading Lda | NON | 08/09/2026 09:46 | 7000 |
| DK45428575 | Uni-Alfa Byg ApS | Stamholmen 109G, 2650 Hvidovre | Fabrica Foods SpA | NON | 08/09/2026 09:47 | 4767 |
| DK45505774 | And | Faste Batteri Vej 104 5 mf, 2300 København S | Vela Services SARL | NON | 08/09/2026 09:48 | 5175 |
| DK45869598 | Illumo ApS | Århusvej 290, 8570 Trustrup | Atlantic Technologies AB | NON | 08/09/2026 09:48 | 8457 |
| DK50549151 | Stûbert Hansen Arkitekter | Møllevej 32A, 3140 Ålsgårde | Fabrica Consulting SpA | NON | 08/09/2026 09:56 | 2795, 7556 |
| DK79614068 | Landmand                          Leif Stagsted | Stagstedvej 38, 9460 Brovst | Corvus Materials AB | NON | 08/09/2026 10:53 | 7506 |
| DK87927059 | Maskinstation                     v/John Bisgaard Kristensen | Fyrkildevej 50, 9610 Nørager | Global Logistics Oy | NON | 08/09/2026 11:06 | 7545 |
| FI02767264 | Riihimäen Kaukolämpö Oy | PL 79, 11101 RIIHIMÄKI | Papyrus Distribution SAS | NON | 08/09/2026 08:36 | 8439 |
| FI05299013 | Multicatering Oy | Teknobulevardi 3-5, 01530 VANTAA | Meridian Distribution A/S | NON | 08/09/2026 08:36 | 8094 |
| FI09808030 | Metsäyhtymä Kanninen Jaana ja Milla | c/oc/o Kiteen tilikeskus Keisarinkuja 2, 82500 KITEE | Orion Technologies Lda | NON | 08/09/2026 08:37 | 693 |
| FI11787021 | Juntunen Risto Ilmari / Risto Juntunen | 00000 OSOITE TUNTEMATON | Meridian Consulting SARL | NON | 08/09/2026 08:38 | 1597, 4517 |
| FI11925738 | Kärkkäinen Markku Kaleva kuolinpesä | 00000 OSOITE TUNTEMATON | Nord Foods Sp. z o.o. | NON | 08/09/2026 08:38 | 6570 |
| FI12225821 | Parila Hannu Tapio | 00000 OSOITE TUNTEMATON | Baltic Services AB | NON | 08/09/2026 08:38 | 7579 |
| FI12801833 | Soininen Heikki Olavi | 00000 OSOITE TUNTEMATON | Fabrica Industries Lda | NON | 08/09/2026 08:38 | 2261 |
| FI14223352 | Hyyppä Keijo Ensio | 00000 OSOITE TUNTEMATON | Lumen Materials Sp. z o.o. | NON | 08/09/2026 08:38 | 1509 |
| FI14302069 | Ketomäki Veikko Iisakki kuolinpesä | 00000 OSOITE TUNTEMATON | Orion Distribution A/S | NON | 08/09/2026 08:38 | 2185 |
| FI14994122 | Linkup Oy | c/oc/o Forum Partners Oy Unioninkatu 20-22, 00130 HELSINKI | Baltic Foods NV | NON | 08/09/2026 08:38 | 1523 |
| FI15803420 | Metsäyhtymä Ilomäki Hannu ja Heikki | VIRTAINTIE 1122, 61650 KALAKOSKI | Fabrica Industries SAS | NON | 08/09/2026 08:39 | 7806 |
| FI16425628 | Saarimäki Tero Johannes | Soukanperäntie 659, 63370 TAIPALUS | Delta Consulting Oy | NON | 08/09/2026 08:39 | 9071 |
| FI17056975 | Petäjä Erkki Antero / EP Service & Import | Palvikuja 1 C, 05460 HYVINKÄÄ | Metallo Industries SARL | NON | 08/09/2026 08:39 | 1284 |
| FI18494715 | Kiinteistö Oy Turun Länsikulma | c/oEvli Rahastoyhtiö Oy PL 1081, 00101 HELSINKI | Atlantic Industries Oy | NON | 08/09/2026 08:39 | 1553 |
| FI18564496 | Panelia Woods Oy | Nummelantie 84, 01810 LUHTAJOKI | Orion Technologies BV | NON | 08/09/2026 08:39 | 538, 720 |
| FI21157189 | Metsäyhtymä Seppänen Ulla ja Sirviö Eero | Linnantaustie 41 A 2, 87250 KAJAANI | Cobalt Trading Sp. z o.o. | NON | 08/09/2026 08:40 | 8005 |
| FI22544797 | Hiirola Pirjo Marjatta | Oikotie 4, 42100 JÄMSÄ | Ardent Materials NV | NON | 08/09/2026 08:40 | 8710 |
| FI22790971 | Saarikalle Holding Oy | PL 747, 00101 HELSINKI | Global Consulting SARL | NON | 08/09/2026 08:40 | 5102 |
| FI22937734 | Kiinteistö Oy Plaza Loiste | c/oNewsec PAM Finland PL 52, 00101 HELSINKI | Delta Consulting Sp. z o.o. | NON | 08/09/2026 08:41 | 5155 |
| FI23692353 | Ourex Oy | Mäkirinteentie 3, 36220 KANGASALA | Batavia Industries A/S | NON | 08/09/2026 08:41 | 1897 |
| FI24009368 | Lehtola Pertti Olavi | 00000 OSOITE TUNTEMATON | Fabrica Services SA | NON | 08/09/2026 08:41 | 6204, 6319 |
| FI24134134 | Kuronen Jorma Väinö Kullervo / Metsäpalvelu Jorma Kuronen | c/oc/o Prikaatintie Prikaatintie 8 A 2, 87500 KAJAANI | Granit Technologies SARL | NON | 08/09/2026 08:41 | 5609 |
| FI24268597 | JT-Koneet Oy | Koussantie 20, 81260 AHVENINEN | Global Distribution SpA | NON | 08/09/2026 08:41 | 7040, 9256 |
| FI24736389 | MinnAgent Ky | Piikatie 1, 70820 KUOPIO | Prima Distribution SpA | NON | 08/09/2026 08:41 | 4037 |
| FI24956728 | Reinikainen Ville Herman / RPR Rakennus | Rahkakatu 50, 15610 LAHTI | Ardent Materials GmbH | NON | 08/09/2026 08:41 | 9041 |
| FI25252968 | Lindström Anita Linnea | 00000 OSOITE TUNTEMATON | Vertex Transports GmbH | NON | 08/09/2026 08:41 | 5503 |
| FI25452732 | AMI Finland Oy | c/oTT-Rummet Mustamäentie 30 A 18, 04600 MÄNTSÄLÄ | Verso Consulting SA | NON | 08/09/2026 08:41 | 3202 |
| FI25566406 | Hatech Kiinteistötekniikka Oy | Vanamontie 8, 45120 KOUVOLA | Corvus Industries AB | NON | 08/09/2026 08:41 | 4091 |
| FI26606369 | Knaapila Sound Oy | c/oSuperhertta Isoistentie 6 A, 02200 ESPOO | Granit Trading AB | NON | 08/09/2026 08:41 | 38 |
| FI26878778 | Ståhlstedt Heidi Katriina / Siivous Nekku | Oikotie 2, 02880 VEIKKOLA | Orion Distribution Oy | NON | 08/09/2026 08:41 | 5647 |
| FI27000844 | HA-KO Consulting Oy | c/oMiika Kokko Hirvikoirankatu 25, 20900 TURKU | Alpine Industries BV | NON | 08/09/2026 08:42 | 5913 |
| FI27519283 | Metsäyhtymä Leppälä Mikko, Pekka ja Teemu | Tiitonrannantie 155, 85800 HAAPAJÄRVI | Kappa Transports SAS | NON | 08/09/2026 08:42 | 3432 |
| FI28417203 | KPK-Service Oy | Koukkaritie 2 B 5, 03100 NUMMELA | Nord Trading Sp. z o.o. | NON | 08/09/2026 08:42 | 9499 |
| FI28591703 | Kapulainen Lauri Juho Aleksi | Menninkäiskuja 4, 04230 KERAVA | Azur Foods Lda | NON | 08/09/2026 08:42 | 7882 |
| FI28619411 | Pukuvuokraamo Kavaljeeri Oy | Käpytikantie 2 as. 1, 36220 KANGASALA | Batavia Materials GmbH | NON | 08/09/2026 08:42 | 7343 |
| FI28694024 | Suominen Meeri Tuulikki | Karjatie 7 as. 6, 96900 SAARENKYLÄ | Vela Trading SA | NON | 08/09/2026 08:42 | 6163 |
| FI29579597 | Ryhänen Niina-Maria Pauliina / TES BEAUTÉ | Kaskelankuja 12 D 2, 01200 VANTAA | Lusitania Materials SA | NON | 08/09/2026 08:42 | 4916 |
| FI30004838 | Kosamo Raimo Kalevi kuolinpesä | 00000 OSOITE TUNTEMATON | Batavia Technologies Oy | NON | 08/09/2026 08:42 | 6847 |
| FI30926365 | Bello Korede Kabiru / KBell Collective | c/oBello Kotkatie 6 A 1, 02620 ESPOO | Solaris Consulting BV | NON | 08/09/2026 08:43 | 4277 |
| FI31155486 | Explicans oy | Taidemaalarinkatu 7 B 19, 00430 HELSINKI | Corvus Services NV | NON | 08/09/2026 08:43 | 6431 |
| FI32156376 | Ikonen Meiju Maaria / Meikos Tattoo | Repolankatu 6, 81700 LIEKSA | Alpine Logistics AB | NON | 08/09/2026 08:43 | 3041 |
| FI32302951 | LJA Holdings Oy | Kihintie 7, 01830 LEPSÄMÄ | Cobalt Distribution Lda | NON | 08/09/2026 08:43 | 4438 |
| FI32524167 | Laihian pizzeria ja ravintola Oy | Tampereentie 84, 66400 LAIHIA | Granit Consulting Sp. z o.o. | NON | 08/09/2026 08:43 | 5262 |
| FI32651588 | Holm Susanna Katariina | Aimontapontie 655, 25520 PERNIÖ AS | Orion Logistics Oy | NON | 08/09/2026 08:44 | 7967 |
| FI32799486 | Piipari Marika Anneli / Skilljoy Academy | Ristinarkunaukio 2 C 115, 33560 TAMPERE | Cobalt Industries BV | NON | 08/09/2026 08:44 | 3454 |
| FI32947629 | Linnunrata OÜ | Pikaliiva tn 90/2-32 13516 Tallinn, ESTONIA | Cobalt Foods SA | NON | 08/09/2026 08:44 | 642, 2062 |
| FI33489463 | Arnella Consulting Oy Ab | Högåsantie 9, 04130 SIPOO | Lumen Technologies Lda | NON | 08/09/2026 08:44 | 3124 |
| FI34496622 | Faruque Bushra | Helokantie 5h as. 3, 40640 JYVÄSKYLÄ | Textil Industries Lda | NON | 08/09/2026 08:44 | 5192 |
| FI34979683 | Metsäyhtymä Lehikoinen Arja ja Leena-Liisa | 00000 OSOITE TUNTEMATON | Nord Technologies GmbH | NON | 08/09/2026 08:44 | 9739 |
| FI35897145 | Enfralux Oy | Runkokuja 5 A, 01730 VANTAA | Nord Distribution Sp. z o.o. | NON | 08/09/2026 08:44 | 2051 |
| FI35928415 | GG-Rakennus ja Urakointi Oy | Hallitie 2, 06400 PORVOO | Verso Industries GmbH | NON | 08/09/2026 08:44 | 8896 |
| FI36168921 | El Huseyin Muhammed / Memo Pizza | Erkinpellontie 15 D 26, 80140 JOENSUU | Solaris Logistics Oy | NON | 08/09/2026 08:44 | 8683 |
| FI36470071 | Islam Md Samiul | Katumantie 25 B 27, 13250 HÄMEENLINNA | Verso Consulting SAS | NON | 08/09/2026 08:45 | 5219 |
| FI91136826 | Västi Jouko,Eeva,Riitta ja Jarmo | VATAJANTIE 17, 61450 KYLÄNPÄÄ | Alpine Consulting Oy | NON | 08/09/2026 08:57 | 7930, 8916 |
| FI91591407 | KALLI ILMARI PERIKUNTA | ILMOITUSSUONTIE 16/AS.HOIT. AUNE KALLI, 27400 KIUKAINEN | Lusitania Trading Oy | NON | 08/09/2026 08:57 | 1790 |
| FR56883050023 | SAS FRANCE LEADS | 24 RUE RENON, 94300 VINCENNES | Metallo Materials A/S | NON | 08/09/2026 11:42 | 6851 |
| FR58878591742 | MME LOPES CINDY | 31 RUE D AGUESSEAU, 94490 ORMESSON SUR MARNE | Corvus Technologies Oy | NON | 08/09/2026 11:48 | 2011 |
| LU16204565 | KERSTING LUXEMBOURG, SARL | 209, RUE DES ROMAINS, L-8041  BERTRANGE | Lusitania Materials NV | NON | 08/09/2026 09:19 | 7997 |
| LU18470631 | WEBTRANS S.A. | BP 2, RUE DE CIMETIERE, L-8001  STRASSEN | Global Foods SAS | NON | 08/09/2026 09:19 | 7419 |
| LU19219241 | D.S. CONCEPT IMMO S.A R.L. | 4, RUE JOHANNES GUTENBERG, L-1649  LUXEMBOURG | Corvus Logistics SARL | NON | 08/09/2026 09:19 | 2952 |
| LU19412112 | SACEM LUXEMBOURG, SOCIETE CIVILE | 76, RUE DE MERL, L-2146  LUXEMBOURG | Corvus Trading Sp. z o.o. | NON | 08/09/2026 09:20 | 7910 |
| LU19433548 | AZURFIVE S.A R.L. | 25, MONTEE DE CLAUSEN, L-1343  LUXEMBOURG | Lusitania Foods SARL | NON | 08/09/2026 09:20 | 6948 |
| LU19940949 | LCGF S.A R.L. | 8, RUE DE LA LIBERATION, L-7347  STEINSEL | Prima Transports Sp. z o.o. | NON | 08/09/2026 09:20 | 4414 |
| LU20172854 | POULL                                   MONIQUE MATHILDE | 1, DUERFSTROOSS, L-9636  BERLE | Vertex Trading SARL | NON | 08/09/2026 09:20 | 557 |
| LU20289564 | EAU'CEANE S.A.R.L. | 5, RUE DE MAMER, L-8081  BERTRANGE | Atlantic Consulting SARL | NON | 08/09/2026 09:20 | 6782 |
| LU20465140 | PATRIMONIA INTERNATIONAL S.A R.L. | 37, RUE DE MAMER, L-8185  KOPSTAL | Vertex Industries Sp. z o.o. | NON | 08/09/2026 09:20 | 8237 |
| LU20573657 | GLIMO | 1, UM KLAPPCHEN, L-5720  ASPELT | Alpine Foods Sp. z o.o. | NON | 08/09/2026 09:20 | 4729 |
| LU20650626 | FERTOF SA | 80A, RUE DE KEHLEN, L-8295  KEISPELT | Prima Industries Lda | NON | 08/09/2026 09:20 | 5703 |
| LU20926526 | TOP GERANCES S.AR.L. | 19, OM BECHEL, L-6833  BIWER | Prima Logistics A/S | NON | 08/09/2026 09:20 | 8489 |
| LU21302851 | MILA VLADY S.A R.L. | 121, RUE CYPRIEN MERJAI, L-2145  LUXEMBOURG | Metallo Industries SpA | NON | 08/09/2026 09:20 | 2539 |
| LU21661275 | FTC FUTURES FUND SICAV | 2, RUE D'ALSACE, L-1122  LUXEMBOURG | Atlantic Technologies Sp. z o.o. | NON | 08/09/2026 09:20 | 8459 |
| LU22086051 | AVRIPARK S.A R.L. | 49, BOULEVARD ROYAL, L-2449  LUXEMBOURG | Metallo Transports Sp. z o.o. | NON | 08/09/2026 09:20 | 5633 |
| LU22903538 | BRAUN & TOTH ABSAUGTECHNIK GMBH | 18, IM BRUCH, D-63897  MILTENBERG | Solaris Industries SAS | NON | 08/09/2026 09:20 | 9269 |
| LU23157384 | GUNCO S.A R.L. | 7, RUE LAITESCHBAACH, L-5324  CONTERN | Baltic Trading Oy | NON | 08/09/2026 09:20 | 5697 |
| LU23159113 | LABEL K  S.A.R.L. | 39, MAISON, L-9772  TROINE | Orion Foods GmbH | NON | 08/09/2026 09:21 | 9535 |
| LU23211188 | H&S GLOBAL | 2, RUE JEAN MONNET, L-2180  LUXEMBOURG | Textil Transports Lda | NON | 08/09/2026 09:21 | 3830 |
| LU23413363 | BAI?A                                   ZAIGA | 2, HEPPESCHGAASS, L-9940  ASSELBORN | Ardent Transports GmbH | NON | 08/09/2026 09:21 | 5273 |
| LU23492756 | WAREMA RENKHOFF SE | 2, HANS-WILHELM-RENKHOFF-STR., D-97828  MARKTHEIDENFELD | Prima Distribution GmbH | NON | 08/09/2026 09:21 | 6925 |
| LU23703225 | HAMMES & KRAMP GARTGENGESTALTUNG GMBH | 3A, OTTO-HAHN-STRASSE, D-54329  KONZ | Lusitania Technologies NV | NON | 08/09/2026 09:21 | 3655 |
| LU24649049 | JALA HOLDING S.A R.L. | 17, RUE LEON LAVAL, L-3372  LEUDELANGE | Metallo Distribution Lda | NON | 08/09/2026 09:21 | 3355 |
| LU24879439 | KOWALCZYK                               AGNIESZKA ALINA | 1, ELSTERNWEG, D-56841  TRABEN-TRARBACH | Solaris Industries BV | NON | 08/09/2026 09:21 | 9036 |
| LU25227246 | HOEFER                                  RICHARD | 13, AVENIDA DEL MAR, E-07184  CALVIA, MALLORCA | Alpine Transports A/S | NON | 08/09/2026 09:21 | 3385 |
| LU25390274 | GENENCOR INTERNATIONAL BV | 4, WILLEM EINTHOVENSTRAAT, NL-2342  BH OEGSTGEEST | Fabrica Foods Oy | NON | 08/09/2026 09:21 | 9511 |
| LU27595555 | L&P AUTOMOTIVE LUXEMBOURG, S.A R.L. | 17, BOULEVARD F.W. RAIFFEISEN, L-2411  LUXEMBOURG | Alpine Logistics Lda | NON | 08/09/2026 09:22 | 3926 |
| LU29524128 | ACI ELEVATION SAS | 49, RUE DE BOULT, F-51110  ISLES SUR SUIPPE | Lumen Distribution GmbH | NON | 08/09/2026 09:22 | 1413 |
| LU29841688 | G. LUSATTI & CIE | 13, RUE DE LA PAIX, L-3871  SCHIFFLANGE | Cobalt Foods SA | NON | 08/09/2026 09:22 | 2591 |
| LU30466215 | FAB N YOU SARL-S | 9A, RUE DE BEGEM, L-4029  ESCH SUR ALZETTE | Nord Transports BV | NON | 08/09/2026 09:22 | 1084 |
| LU30505350 | DA SILVA NAPOMUCENO                     HUGO ANDRE | 31, RUE KINNIKSHAFF, L-8838  WAHL | Kappa Industries SARL | NON | 08/09/2026 09:22 | 5472 |
| LU30538728 | FLIESEN JECKEL GMBH | 9, BAHNHOFSALLEE, D-86438  KISSING | Lusitania Foods SA | NON | 08/09/2026 09:22 | 5535 |
| LU30643205 | SOFINNOVA TELETHON GP | 4, RUE PETERNELCHEN, L-2370  HOWALD | Verso Industries Oy | NON | 08/09/2026 09:22 | 5369 |
| LU31040158 | WATERCAT LUXEMBOURG S.A R.L. | 31A, RUE LENTZ, L-3509  DUDELANGE | Kappa Industries A/S | NON | 08/09/2026 09:22 | 6373 |
| LU31183164 | RED BIRD S.A. | 4, RUE HENRI SCHNADT, L-2530  LUXEMBOURG | Verso Industries SA | NON | 08/09/2026 09:22 | 9555 |
| LU31271255 | ACTIVITE GERANCE S.A R.L. | 11, BOULEVARD GRANDE-DUCHESSE CHARLOTTE, L-1331  LUXEMBOURG | Global Foods SA | NON | 08/09/2026 09:22 | 8866 |
| LU31386046 | SN IMMOBILIE ERLANGEN GMBH | 142, ROUTE DE LUXEMBOURG, L-7241  BERELDANGE | Delta Trading A/S | NON | 08/09/2026 09:22 | 6216 |
| LU32371017 | PROPERKONFORT MULTISERVICE, S.A.R.L.-S | 27, RUE ERMESINDE, L-6437  ECHTERNACH | Fabrica Trading SAS | NON | 08/09/2026 09:22 | 3189 |
| LU32431802 | RUCOLINO S.A R.L. | 15, RUE DU COMMERCE, L-3450  DUDELANGE | Delta Services Lda | NON | 08/09/2026 09:22 | 6457 |
| LU32598264 | VGP PARK ERFURT 2 S.A R.L. | 1B, HEIENHAFF, L-1736  SENNINGERBERG | Prima Materials Sp. z o.o. | NON | 08/09/2026 09:22 | 7548 |
| LU32758868 | GC WERBEARTIKEL SARL-S | 11, RUE MICHEL RODANGE, L-3750  RUMELANGE | Meridian Trading SpA | NON | 08/09/2026 09:23 | 8975 |
| LU32789721 | MUSTAFA                                 KHADIJA | 6-8, RUE MICHEL NOEL, L-3859  SCHIFFLANGE | Azur Industries SpA | NON | 08/09/2026 09:23 | 1315 |
| LU32958316 | BIF IV ENERGY SIDECAR (ER) SCSP | 31, AVENUE MONTEREY, L-2163  LUXEMBOURG | Delta Transports BV | NON | 08/09/2026 09:23 | 586 |
| LU32963972 | ALIBERT                                 MARIE-CHARLOTTE | 10, RUE DES ECOLES, L-4731  PETANGE | Cobalt Industries Lda | NON | 08/09/2026 09:23 | 5989 |
| LU33340410 | ARTPOADOR SARL | 61, CHEMIN DE BAS-RANSBECK, B-1380  LASNE | Corvus Industries AB | NON | 08/09/2026 09:23 | 4849 |
| LU33513045 | ZELLIGE.SHOP S.A R.L. | 22, AVENUE DE LA LIBERTE, L-1930  LUXEMBOURG | Papyrus Technologies AB | NON | 08/09/2026 09:23 | 8187 |
| LU33544201 | LOEWIN SARL | 5, RUE DU KIEM, L-1857  LUXEMBOURG | Delta Foods Lda | NON | 08/09/2026 09:23 | 8354 |
| LU33712885 | EFV ST CRISPINS S.A R.L. | 23A, RUE DE HOLLERICH, L-1741  LUXEMBOURG | Global Materials Sp. z o.o. | NON | 08/09/2026 09:23 | 7161 |
| LU34195416 | MANET                                   PATRICK JEAN PIERRE ARMAND | 10, SCHLASSUECHT, L-7435  HOLLENFELS | Fabrica Materials Lda | NON | 08/09/2026 09:23 | 2279 |
| LU34601168 | KONSTANT PARTNERS GP S.A R.L | 9, RUE SCHILLER, L-2519  LUXEMBOURG | Textil Technologies Lda | NON | 08/09/2026 09:23 | 1173 |
| LU34632425 | MY ENERGY | 30, AN DER GAASS, L-9638  POMMERLOCH | Delta Technologies AB | NON | 08/09/2026 09:23 | 1468, 1517 |
| LU34955047 | MACQUARIE INFRASTRUCTURE PARTNERS VI SCSP | 20, BOULEVARD ROYAL, L-2449  LUXEMBOURG | Batavia Consulting SA | NON | 08/09/2026 09:23 | 4727 |
| LU35339161 | EXPECTO S.A R.L. | 9B, RUE BASSE, L-4963  CLEMENCY | Lumen Logistics GmbH | NON | 08/09/2026 09:23 | 8781 |
| LU35378207 | NAIL AT HOME S.A R.L.-S | 1, RUE XAVIER DE FELLER, L-1514  LUXEMBOURG | Solaris Industries SARL | NON | 08/09/2026 09:23 | 5501 |
| LU35907347 | EMMARS CAPITAL S.A R.L. | 1, BOULEVARD DE LA RECHERCHE, L-4373  BELVAUX | Azur Technologies NV | NON | 08/09/2026 09:23 | 2607 |
| LU36125201 | AM & NO INVEST SARL | 8, ROUTE DE LUXEMBOURG, L-7759  ROOST (BISSEN) | Azur Industries NV | NON | 08/09/2026 09:23 | 2630 |
| LU36555229 | BATONI CORP | 16, RUE D'EPERNAY, L-1490  LUXEMBOURG | Lusitania Technologies SARL | NON | 08/09/2026 09:23 | 274 |
| LU36862879 | ICG RENEWABLES (KOREA) SCSP | 3, RUE GABRIEL LIPPMANN, L-5365  MUNSBACH | Azur Transports BV | NON | 08/09/2026 09:24 | 2584 |
| LU36968770 | LETZENERGY S.A R.L. | 46, GRAND-RUE, L-6630  WASSERBILLIG | Alpine Distribution SARL | NON | 08/09/2026 09:24 | 7382 |
| LU36993248 | WEISS & FABER IMMOBILIERE | 4C, HAAPTSTROOSS, L-9764  MARNACH | Orion Industries BV | NON | 08/09/2026 09:24 | 9339 |
| LU37122001 | APOLLO ASSET-BACKED FINANCE LENDING COMPANY SUBSIDIARY I LUX, S.A R.L. | 2, AVENUE CHARLES DE GAULLE, L-1653  LUXEMBOURG | Atlantic Services SA | NON | 08/09/2026 09:24 | 5494 |
| LU37150115 | MESSAOUDI                               SALMA | 3, RUE DU CENTRE, L-8282  KEHLEN | Baltic Distribution SAS | NON | 08/09/2026 09:24 | 4166, 4806 |
| LU37201685 | HANSEMERKUR DIGITAL INFRASTRUCTURE ELTIF S.C.A., SICAV | 1C, RUE GABRIEL LIPPMANN, L-5365  MUNSBACH | Papyrus Services A/S | NON | 08/09/2026 09:24 | 7757 |
| LU37213829 | ELITE PARTNERS CLEANING SRL | 226, AVENUE DE MARLAGNE, B-5000  NAMUR | Lumen Consulting SA | NON | 08/09/2026 09:24 | 8939 |
| LU37322649 | INTELLIGENCE CAPITAL SAS | 36, GRAND-RUE, L-1660  LUXEMBOURG | Textil Distribution Sp. z o.o. | NON | 08/09/2026 09:24 | 1738 |
| LU37464746 | CUBE GP KMEN S.A R.L. | 28, PLACE DE LA GARE, L-1616  LUXEMBOURG | Textil Technologies NV | NON | 08/09/2026 09:24 | 1806 |
| LU37471929 | SOUZA DA CUNHA OLIVEIRA                 PATRICIA | 57, RUE DES JARDINS, L-7782  BISSEN | Verso Logistics SA | NON | 08/09/2026 09:24 | 8319 |
| LU37487305 | EVP II SPRINT SCSP SICAV-RAIF | 2, BOULEVARD DE LA FOIRE, L-1528  LUXEMBOURG | Hanse Consulting SAS | NON | 08/09/2026 09:24 | 854 |
| LU37650535 | OGILVIE-FORBES                          ALEXANDER JOHN ADAM | 9, RUE JULES MERSCH, L-2184  LUXEMBOURG | Cobalt Foods Sp. z o.o. | NON | 08/09/2026 09:24 | 6594 |
| PL7281493244 | IWONA ŁUKASIK | HELENY MODRZEJEWSKIEJ 30, 92-620 ŁÓDŹ | Nord Services SpA | NON | 08/09/2026 11:12 | 1899 |
| PL7692232367 | GREEN HEMP POLAND SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ | OSIEDLE DOLNOŚLĄSKIE 135 M9, 97-400 BEŁCHATÓW | Textil Foods Oy | NON | 08/09/2026 11:13 | 5800 |
| PL7812041197 | R&A-INSTALLATIONS SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ | ŚW. LEONARDA 8 M10, 60-654 POZNAŃ | Vertex Services GmbH | NON | 08/09/2026 11:13 | 4669 |
| PL8992975239 | KAMIL STASIAK | KADŁUB 28, 98-300 | Azur Technologies SARL | NON | 08/09/2026 11:17 | 9082 |
| PT207862389 | PAULO MIGUEL GOMES SARMENTO | R ALEXANDRE HERCULANO 20 2º ESQ, PÓVOA VARZIM, 4490-461 PÓVOA DE VARZIM | Solaris Logistics SARL | NON | 08/09/2026 11:14 | 2854 |
| PT215440528 | PEDRO MIGUEL DA SILVA COSTA | R DE DEVESA 255 HAB 223 OLIVEIRA DO DOURO, VILA NOVA GAIA, 4430-376 VILA NOVA DE GAIA | Hanse Transports SARL | NON | 08/09/2026 11:14 | 5605 |
| PT513154671 | GUIMATUBOS TUBOS E SANITARIOS LDA | RUA DA INDIA N 374 R C LOJA 2 URGEZES, GUIMARÃES, 4810-482 GUIMARAES | Cobalt Trading SAS | NON | 08/09/2026 11:22 | 6620 |
| PT513795111 | MVLMCS - CONSULTORIA E SERVIÇOS LDA | RUA ARTILHARIA 1 71-77 EMPREENDIMENTO NOVA AMOREIRAS PALACI, O 1, LISBOA, 1250-038 LISBOA | Batavia Materials A/S | NON | 08/09/2026 11:22 | 877 |
| PT514947063 | CARDOSO & MARTINS LDA | RUA IMACULADO CORAÇÃO DE MARIA N 182, FOROS DE SALVATERRA, 2120-188 FOROS DE SALVATERRA | Baltic Industries GmbH | NON | 08/09/2026 11:22 | 1507, 3526 |
| PT516517953 | NUANCE POSITIVA, LDA | AVENIDA DR MARIO SOARES N 626 2 ESQ, GONDOMAR, 4420-619 GONDOMAR | Hanse Trading SAS | NON | 08/09/2026 11:22 | 1447 |
| PT518825990 | LEMONBAY LDA | ESTRADA NAIONAL N 16 ALTO DE ABRAVESES RUA FONTE DO CÃO S/N , ABRAVESES, VISEU, 3515-113 VISEU | Verso Consulting SARL | NON | 08/09/2026 11:22 | 6855 |

Numéros éligibles restant à trancher (non interrogés ou indéterminés transitoires) : **501**. Relancer `uv run meridian-tva campaign` reprend exactement là : les verdicts définitifs ne sont jamais rappelés.

## 7. Durée de validité d'un verdict

VIES ne répond que pour l'instant présent. Chaque verdict est stocké avec sa date ; l'API le sert comme « frais » pendant 24 h puis le revérifie. La facturation doit consulter l'API avant chaque émission hors taxe, et conserver le numéro de consultation VIES (`request_identifier`) sur la facture : il n'est délivré que si le numéro de TVA de Meridian est transmis en tant que demandeur (non configuré : à renseigner dans .env).

## 8. Méthode et limites de la vérification en ligne

- VIES ne possède aucune base : il relaie chaque question au registre de l'État membre concerné, en temps réel, avec la limite de débit de ce registre. Il n'existe ni extraction en masse ni registre européen consolidé.
- La campagne n'envoie jamais plus d'un appel à la fois à un même registre ; des registres différents sont interrogés en parallèle. La temporisation de chaque registre s'allonge quand il refuse (`MS_MAX_CONCURRENT_REQ`) et revient à la normale ensuite. Un registre indisponible ou saturé produit des indéterminés, jamais des invalides.
- Un indéterminé est réessayé lors de la campagne suivante, au plus deux fois (six appels) ; au-delà, il reste indéterminé et la ligne apparaît comme telle ici : la décision de facturer avec TVA, ou d'attendre, appartient à la facturation.
- « Valide » signifie que le numéro existe et est actif dans le registre national à la date indiquée. Il ne signifie pas qu'il appartient au client facturé : la concordance d'identité (section 6) est indispensable, plusieurs registres attribuant leurs numéros séquentiellement.
- Les numéros britanniques (GB/UK) ne sont plus interrogeables dans VIES depuis le Brexit ; ils sont classés hors périmètre.
