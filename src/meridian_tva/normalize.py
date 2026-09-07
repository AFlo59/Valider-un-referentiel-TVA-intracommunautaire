"""Normalisation d'un numéro de TVA tel que saisi.

Décisions (chacune change les chiffres finaux, elles sont donc explicites) :
- Le vide a plusieurs formes ('', ' ', '-', 'N/A', 'null', 'NU.LL'...). Il est détecté AVANT toute normalisation,
  sinon 'N/A' devient le faux numéro « NA » et 'null' le faux numéro « NULL ».
- On ne supprime que le bruit de saisie : espaces, points, tirets, barres, apostrophes, casse. On ne « répare » rien :
  un O à la place d'un 0 reste une lettre parasite et sera rejeté par le contrôle structurel.
- Un numéro sans préfixe pays reçoit celui de la colonne pays_declare (532 lignes dans le jeu), et on le note.
- Un préfixe présent mais différent de pays_declare n'est pas corrigé : c'est une incohérence à signaler, pas à deviner.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Formes du vide observées dans le référentiel (comparées après strip + majuscules, puis après compactage)
EMPTY_TOKENS = {"", "-", "--", "?", "N/A", "NA", "NULL", "NONE", "NAN", "NU.LL", "NEANT", "NÉANT", "INCONNU", "TBD", "X"}
EMPTY_COMPACT = {"", "NA", "NULL", "NONE", "NAN", "NEANT", "INCONNU", "TBD", "X"}

_NON_ALNUM = re.compile(r"[^A-Z0-9]")


@dataclass(frozen=True)
class Normalized:
    raw: str
    is_empty: bool
    compact: str | None          # numéro complet normalisé (préfixe + corps), None si vide
    country: str | None          # préfixe pays retenu
    body: str | None             # partie nationale
    prefix_source: str           # 'numero' | 'pays_declare' | 'aucun'
    had_noise: bool              # la valeur brute contenait du bruit de saisie (casse, séparateurs, espaces)
    prefix_conflict: bool        # préfixe du numéro différent de pays_declare


def normalize(raw: str | None, pays_declare: str | None) -> Normalized:
    raw = "" if raw is None else str(raw)
    stripped = raw.strip().upper()
    declared = (pays_declare or "").strip().upper() or None

    if stripped in EMPTY_TOKENS:
        return Normalized(raw, True, None, None, None, "aucun", False, False)

    compact = _NON_ALNUM.sub("", stripped)
    if compact in EMPTY_COMPACT:
        return Normalized(raw, True, None, None, None, "aucun", False, False)

    had_noise = compact != raw  # tout écart avec la valeur brute est du bruit (casse, séparateurs, espaces)

    if len(compact) >= 2 and compact[:2].isalpha():
        country = compact[:2]
        body = compact[2:]
        prefix_source = "numero"
        conflict = declared is not None and declared.isalpha() and len(declared) == 2 and declared != country
    elif declared and declared.isalpha() and len(declared) == 2:
        country = declared
        body = compact
        compact = country + body
        prefix_source = "pays_declare"
        conflict = False
    else:
        return Normalized(raw, False, compact, None, compact, "aucun", had_noise, False)

    return Normalized(raw, False, compact, country, body, prefix_source, had_noise, conflict)
