-- Référentiel TVA Meridian Distribution. Idempotent : rejoué à chaque chargement.
--
-- Trois niveaux, volontairement séparés :
--   lignes_referentiel : ce que nous avons REÇU (valeur brute, telle que saisie) + ce que nous en avons DÉDUIT ligne à ligne
--   numeros            : un numéro normalisé = une entité à vérifier (plusieurs lignes peuvent pointer vers le même numéro)
--   verifications_vies : l'historique des réponses du service en ligne, datées, avec la réponse brute

CREATE TABLE IF NOT EXISTS lignes_referentiel (
    id                  INTEGER PRIMARY KEY,           -- identifiant du fichier source : clé du rechargement idempotent
    raison_sociale      TEXT,
    pays_declare        TEXT,
    numero_brut         TEXT,                          -- exactement la valeur du fichier, espaces compris
    date_saisie         DATE,
    source_saisie       TEXT,
    numero_normalise    TEXT,                          -- NULL quand le numéro est absent (6 formes de vide)
    pays_resolu         TEXT,                          -- préfixe du numéro, ou pays_declare si le numéro n'en porte pas
    verdict_structurel  TEXT NOT NULL,                 -- VALIDE_STRUCTURE | INVALIDE_STRUCTURE | HORS_PERIMETRE | ABSENT
    motif_structurel    TEXT NOT NULL,                 -- OK, NUMERO_ABSENT, PAYS_INCONNU, PAYS_HORS_UE, LONGUEUR_INVALIDE, CLE_INVALIDE...
    detail_structurel   TEXT,
    charge_le           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS numeros (
    numero_normalise    TEXT PRIMARY KEY,
    pays                TEXT NOT NULL,
    verdict_structurel  TEXT NOT NULL,
    motif_structurel    TEXT NOT NULL,
    nb_lignes           INTEGER NOT NULL,              -- nombre de lignes du référentiel portant ce numéro (doublons)
    eligible_vies       BOOLEAN NOT NULL               -- structure valide ET pays interrogeable dans VIES
);

CREATE TABLE IF NOT EXISTS verifications_vies (
    id                  BIGSERIAL PRIMARY KEY,
    numero_normalise    TEXT NOT NULL REFERENCES numeros (numero_normalise),
    verifie_le          TIMESTAMPTZ NOT NULL DEFAULT now(),
    etat                TEXT NOT NULL,                 -- valide | invalide | indetermine
    code_vies           TEXT NOT NULL,                 -- VALID, INVALID, MS_UNAVAILABLE, MS_MAX_CONCURRENT_REQ, HTTP_503, RESEAU...
    definitif           BOOLEAN NOT NULL,              -- faux pour un indéterminé transitoire : à réessayer
    nom                 TEXT,
    adresse             TEXT,
    request_date        TEXT,
    request_identifier  TEXT,                          -- numéro de consultation VIES : preuve pour l'administration
    reponse             JSONB,                         -- réponse brute complète
    duree_ms            INTEGER,
    tentative           INTEGER NOT NULL DEFAULT 1,
    origine             TEXT NOT NULL DEFAULT 'campagne'  -- campagne | api
);

CREATE INDEX IF NOT EXISTS verifications_numero_date_idx ON verifications_vies (numero_normalise, verifie_le DESC);
CREATE INDEX IF NOT EXISTS lignes_numero_idx ON lignes_referentiel (numero_normalise);

-- Dernière vérification connue par numéro
CREATE OR REPLACE VIEW etat_vies_courant AS
SELECT DISTINCT ON (numero_normalise) *
FROM verifications_vies
ORDER BY numero_normalise, verifie_le DESC;

-- État final d'un numéro : la structure d'abord, VIES ensuite, indéterminé par défaut
CREATE OR REPLACE VIEW etat_numeros AS
SELECT n.numero_normalise,
       n.pays,
       n.verdict_structurel,
       n.motif_structurel,
       n.nb_lignes,
       n.eligible_vies,
       v.etat        AS etat_vies,
       v.code_vies,
       v.verifie_le,
       v.request_identifier,
       CASE
           WHEN n.verdict_structurel = 'HORS_PERIMETRE'      THEN 'hors_perimetre'
           WHEN n.verdict_structurel = 'INVALIDE_STRUCTURE'  THEN 'invalide'
           WHEN v.etat = 'valide'                            THEN 'valide'
           WHEN v.etat = 'invalide'                          THEN 'invalide'
           ELSE 'indetermine'
       END AS etat_final,
       CASE
           WHEN n.verdict_structurel <> 'VALIDE_STRUCTURE'   THEN n.motif_structurel
           WHEN v.etat IS NULL                               THEN 'NON_VERIFIE'
           ELSE v.code_vies
       END AS motif_final
FROM numeros n
LEFT JOIN etat_vies_courant v USING (numero_normalise);

-- État final ramené à chaque ligne du référentiel (les lignes sans numéro sont 'absent')
CREATE OR REPLACE VIEW etat_lignes AS
SELECT l.id, l.raison_sociale, l.pays_declare, l.numero_brut, l.date_saisie, l.source_saisie,
       l.numero_normalise, l.pays_resolu, l.verdict_structurel, l.motif_structurel,
       COALESCE(e.etat_final, 'absent') AS etat_final,
       COALESCE(e.motif_final, l.motif_structurel) AS motif_final,
       e.etat_vies, e.verifie_le, e.request_identifier
FROM lignes_referentiel l
LEFT JOIN etat_numeros e USING (numero_normalise);
