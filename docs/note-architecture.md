# Note d'architecture

## 1. Comment les appels à VIES ont été réduits, et de combien

Une approche naïve interroge VIES une fois par ligne : 10 000 appels. Mesuré le 07/09/2026, VIES répond en 0,1 s pour un
numéro inexistant et en 6 à 8 s pour un numéro valide ; la limite de requêtes concurrentes est globale par État membre, donc
un seul appel à la fois vers un même registre. À 1,5 s de temporisation plus la latence, 10 000 appels représentent 8 à
10 heures en séquentiel, et plusieurs milliers d'entre eux seraient inutiles. Le volume se réduit d'abord (tableau
ci-dessous) ; la durée se réduit ensuite en interrogeant plusieurs États en parallèle, chacun toujours un appel à la fois
(`--par-pays`, quatre par défaut recommandé, dix États dans le jeu) : la campagne complète passe de 6 à 9 heures à
environ une heure et demie, sans jamais dépasser le rythme accepté par chaque registre.

| Étape (ordre imposé) | Lignes ou numéros | Ce qui est retiré |
|---|---|---|
| Lignes reçues | 10 000 | |
| Numéro absent (6 formes de vide : `''`, `' '`, `-`, `N/A`, `null`, `NU.LL`) | − 261 | rien à vérifier, à collecter auprès du client |
| Hors périmètre VIES | − 519 | GB/UK (208, Brexit : régime export) ; codes pays inexistants ZZ/QQ/XX (311) |
| Structure invalide | − 2 605 | clé fausse 1 341, longueur 726, caractères parasites 453, format 85 |
| Structure valide | 6 615 lignes | |
| Dédoublonnage (même pays + même numéro normalisé) | − 313 | 6 302 numéros distincts |
| **Appels VIES nécessaires** | **6 302** | **réduction de 37,0 %** (3 698 appels évités) |

La normalisation joue dans l'autre sens : 2 140 lignes portent du bruit de saisie (casse, espaces, points, tirets) et
532 n'ont pas de préfixe pays. Sans normalisation elles seraient rejetées à tort ; avec elle, elles rejoignent les 6 615
candidats. Le nombre de doublons dépend de la définition : 390 lignes identiques au caractère près (dont 255 vides entre
eux), 438 lignes en trop après normalisation (définition retenue : même pays résolu, même numéro normalisé, vides exclus).

Deux décisions changent ces chiffres de plusieurs points et sont assumées :

- **Le module structurel est réécrit** (celui du kit n'est pas fourni). Il vérifie format et clé de contrôle nationale,
  et rien de plus profond (pas de Luhn sur le SIREN français, pas de code d'office italien) : c'est le niveau « clé de
  contrôle » que le brief décrit. Un validateur plus strict (python-stdnum) ferait tomber FR et IT de 80 % à moins de 10 %
  de valides structurels, sur un jeu synthétique qui respecte la clé mais pas ces règles internes.
- **Aucune réparation** : un numéro BE à 9 chiffres n'est pas complété par un 0, un O n'est pas changé en 0. Ces lignes
  sont invalides avec leur motif, et le client est invité à corriger.

## 2. Quelle durée de validité pour un verdict

VIES ne répond que pour l'instant présent ; il n'existe aucune durée de validité officielle. La condition légale (art. 138
de la directive TVA, BOI-TVA-CHAMP-30-20-10 § 100 et suivants) est que le numéro soit valide **à la date de l'opération**.

Politique retenue, paramétrable (`VERDICT_TTL_HOURS`, 24 h par défaut) :

- l'API sert une valeur connue de moins de 24 h comme **fraîche** ; au-delà, elle rappelle VIES avant de répondre ;
- la facturation appelle l'API **avant chaque émission hors taxe**, et n'exonère que si `facturation_hors_taxe_possible`
  est vrai (verdict valide **et** fraîcheur fraîche) ;
- chaque réponse VIES est stockée datée, avec sa réponse brute et le numéro de consultation (`request_identifier`) quand
  le numéro de TVA de Meridian est transmis en demandeur ; ce numéro est la preuve à conserver avec la facture ;
- une revérification périodique du référentiel (campagne mensuelle) maintient l'état des lieux, mais ne remplace pas le
  contrôle au moment de la facture.

Une information vieille de six ou huit mois est donc servie, mais toujours marquée `perimee`, jamais comme un feu vert.

## 3. Ce qui est fait des indéterminés

« Indéterminé » recouvre des situations différentes, et le modèle les distingue par le code conservé :

| Situation | Code stocké | Traitement |
|---|---|---|
| Structure valide, VIES pas encore interrogé | `NON_VERIFIE` (vue) | prochaine campagne |
| État membre ou service indisponible, débit limité, timeout, erreur réseau | `MS_UNAVAILABLE`, `SERVICE_UNAVAILABLE`, `*_MAX_CONCURRENT_REQ*`, `TIMEOUT`, `HTTP_5xx`, `RESEAU_*` | `definitif = false` : réessayé automatiquement (3 tentatives avec attente croissante dans la campagne, puis à la campagne suivante) |
| Entrée refusée par VIES | `INVALID_INPUT` | `definitif = true` : pas de nouvel appel, requalification manuelle |
| Blocage | `IP_BLOCKED`, `VAT_BLOCKED`, `INVALID_REQUESTER_INFO` | arrêt de la campagne, intervention humaine |

Règle absolue, appliquée dans le code et testée : une indisponibilité n'est **jamais** enregistrée comme une invalidité,
et un indéterminé n'autorise **jamais** une facture hors taxe. Quand VIES est injoignable et qu'aucune valeur n'est connue,
l'API répond HTTP 200 avec `verdict = indetermine`, `origine = vies_live`, et le code d'erreur en motif : une réponse
explicite plutôt qu'une erreur 5xx que l'appelant pourrait mal interpréter. Quand une valeur périmée existe, elle est
renvoyée avec `fraicheur = perimee` et `facturation_hors_taxe_possible = false`.

Au niveau du référentiel, deux populations ne relèvent pas de VIES et sont présentées séparément à la direction
financière : **hors périmètre** (519 lignes : GB/UK à traiter en régime export, codes pays inexistants à requalifier) et
**absent** (261 lignes : numéro à collecter). Enfin, les 974 lignes FR sont des clients domestiques : même valides, elles ne
donnent aucun droit à l'exonération intracommunautaire ; l'API répond quand même (le contrôle d'existence reste utile),
mais la règle d'exonération appartient à la facturation.

## 4. Schéma et reprise

Trois tables : `lignes_referentiel` (ce que nous avons reçu, clé `id` du fichier, rechargement idempotent),
`numeros` (une entité par numéro normalisé, `nb_lignes` = doublons, `eligible_vies`), `verifications_vies` (historique daté,
code, réponse brute JSONB, `definitif`). La vue `etat_vies_courant` donne la dernière vérification par numéro ; `etat_numeros`
et `etat_lignes` calculent l'état final (structure d'abord, VIES ensuite, indéterminé par défaut). L'état de reprise de la
campagne est la base elle-même : un commit par numéro, et la sélection des numéros à traiter exclut ceux qui ont un verdict
définitif. Une interruption (Ctrl+C) est gérée au niveau du programme principal ; la relance reprend exactement là.
