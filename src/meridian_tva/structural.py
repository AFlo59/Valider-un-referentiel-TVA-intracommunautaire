"""Contrôle structurel : format et clé de contrôle des dix pays du jeu.

Le module annoncé par le brief n'étant pas fourni, il est réécrit ici à partir des spécifications nationales
(Commission européenne, « VAT identification numbers » ; formules de clé publiées par chaque administration).
« Structurellement valide » signifie : préfixe d'un pays couvert, longueur et motif corrects, clé de contrôle exacte.
Cela ne dit RIEN de l'existence du numéro ni de son attribution à l'entreprise facturée : seul VIES le dit.

Verdicts :
  VALIDE_STRUCTURE   format et clé corrects -> candidat à la vérification VIES
  INVALIDE_STRUCTURE défaut de format ou de clé -> rejet définitif, aucun appel VIES
  HORS_PERIMETRE     pays hors UE (GB/UK), code pays inexistant (ZZ, QQ, XX) ou pays non couvert -> à requalifier, aucun appel VIES
  ABSENT             numéro vide
"""

from __future__ import annotations

from dataclasses import dataclass

from .normalize import Normalized, normalize

COVERED = {"FR", "BE", "DK", "FI", "IT", "LU", "NL", "PL", "PT", "SE"}
EU_NOT_COVERED = {"AT", "BG", "CY", "CZ", "DE", "EE", "EL", "ES", "HR", "HU", "IE", "LT", "LV", "MT", "RO", "SI", "SK", "XI"}
NON_EU = {"GB", "UK", "CH", "NO", "IS", "LI", "US", "CA", "TR", "MC", "AD", "SM"}

VALIDE, INVALIDE, HORS_PERIMETRE, ABSENT = "VALIDE_STRUCTURE", "INVALIDE_STRUCTURE", "HORS_PERIMETRE", "ABSENT"


@dataclass(frozen=True)
class Verdict:
    verdict: str
    motif: str
    detail: str
    normalized: Normalized

    @property
    def eligible_vies(self) -> bool:
        return self.verdict == VALIDE


# ---------------------------------------------------------------- clés de contrôle


def _luhn_ok(digits: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(digits)):
        n = int(ch)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def _weighted(digits: str, weights: list[int]) -> int:
    return sum(int(d) * w for d, w in zip(digits, weights))


def _check_fr(body: str) -> tuple[bool, str]:
    # 2 caractères de clé (chiffres, ou lettres hors I et O) + 9 chiffres (SIREN)
    if len(body) != 11:
        return False, "LONGUEUR_INVALIDE"
    key, siren = body[:2], body[2:]
    if not siren.isdigit():
        return False, "CARACTERES_INVALIDES"
    if key.isdigit():
        return int(key) == (12 + 3 * (int(siren) % 97)) % 97, "CLE_INVALIDE"
    alphabet = "0123456789ABCDEFGHJKLMNPQRSTUVWXYZ"
    if any(c not in alphabet for c in key):
        return False, "CARACTERES_INVALIDES"
    if key[0].isdigit():
        check = int(key[0]) * 24 + alphabet.index(key[1]) - 10
    else:
        check = alphabet.index(key[0]) * 34 + alphabet.index(key[1]) - 100
    return (int(siren) + 1 + check // 11) % 11 == check % 11, "CLE_INVALIDE"


def _check_be(body: str) -> tuple[bool, str]:
    # 10 chiffres commençant par 0 ou 1 ; les 9 chiffres de l'ancien format ne sont pas complétés automatiquement
    if not body.isdigit():
        return False, "CARACTERES_INVALIDES"
    if len(body) != 10:
        return False, "LONGUEUR_INVALIDE"
    if body[0] not in "01":
        return False, "FORMAT_INVALIDE"
    return 97 - int(body[:8]) % 97 == int(body[8:]), "CLE_INVALIDE"


def _check_dk(body: str) -> tuple[bool, str]:
    if not body.isdigit():
        return False, "CARACTERES_INVALIDES"
    if len(body) != 8:
        return False, "LONGUEUR_INVALIDE"
    return _weighted(body, [2, 7, 6, 5, 4, 3, 2, 1]) % 11 == 0, "CLE_INVALIDE"


def _check_fi(body: str) -> tuple[bool, str]:
    if not body.isdigit():
        return False, "CARACTERES_INVALIDES"
    if len(body) != 8:
        return False, "LONGUEUR_INVALIDE"
    remainder = _weighted(body[:7], [7, 9, 10, 5, 8, 4, 2]) % 11
    if remainder == 1:
        return False, "CLE_INVALIDE"
    return (11 - remainder) % 11 == int(body[7]), "CLE_INVALIDE"


def _check_it(body: str) -> tuple[bool, str]:
    if not body.isdigit():
        return False, "CARACTERES_INVALIDES"
    if len(body) != 11:
        return False, "LONGUEUR_INVALIDE"
    return _luhn_ok(body), "CLE_INVALIDE"


def _check_lu(body: str) -> tuple[bool, str]:
    if not body.isdigit():
        return False, "CARACTERES_INVALIDES"
    if len(body) != 8:
        return False, "LONGUEUR_INVALIDE"
    return int(body[:6]) % 89 == int(body[6:]), "CLE_INVALIDE"


def _check_nl(body: str) -> tuple[bool, str]:
    # 9 chiffres + 'B' + 2 chiffres. Deux règles coexistent : mod 11 (numéros historiques) et mod 97 (btw-id depuis 2020)
    if len(body) != 12:
        return False, "LONGUEUR_INVALIDE"
    if body[9] != "B" or not (body[:9] + body[10:]).isdigit():
        return False, "FORMAT_INVALIDE" if body[:9].isdigit() or body[10:].isdigit() else "CARACTERES_INVALIDES"
    digits = body[:9]
    old_rule = _weighted(digits[:8], [9, 8, 7, 6, 5, 4, 3, 2]) % 11 == int(digits[8])
    as_number = "".join(str(ord(c) - 55) if c.isalpha() else c for c in "NL" + body)
    new_rule = int(as_number) % 97 == 1
    return old_rule or new_rule, "CLE_INVALIDE"


def _check_pl(body: str) -> tuple[bool, str]:
    if not body.isdigit():
        return False, "CARACTERES_INVALIDES"
    if len(body) != 10:
        return False, "LONGUEUR_INVALIDE"
    remainder = _weighted(body[:9], [6, 5, 7, 2, 3, 4, 5, 6, 7]) % 11
    return remainder != 10 and remainder == int(body[9]), "CLE_INVALIDE"


def _check_pt(body: str) -> tuple[bool, str]:
    if not body.isdigit():
        return False, "CARACTERES_INVALIDES"
    if len(body) != 9:
        return False, "LONGUEUR_INVALIDE"
    remainder = _weighted(body[:8], [9, 8, 7, 6, 5, 4, 3, 2]) % 11
    check = 0 if remainder < 2 else 11 - remainder
    return check == int(body[8]), "CLE_INVALIDE"


def _check_se(body: str) -> tuple[bool, str]:
    if not body.isdigit():
        return False, "CARACTERES_INVALIDES"
    if len(body) != 12:
        return False, "LONGUEUR_INVALIDE"
    if not body.endswith("01"):
        return False, "FORMAT_INVALIDE"
    return _luhn_ok(body[:10]), "CLE_INVALIDE"


CHECKERS = {
    "FR": _check_fr, "BE": _check_be, "DK": _check_dk, "FI": _check_fi, "IT": _check_it,
    "LU": _check_lu, "NL": _check_nl, "PL": _check_pl, "PT": _check_pt, "SE": _check_se,
}

EXPECTED_FORMAT = {
    "FR": "FR + 2 caractères de clé + 9 chiffres", "BE": "BE + 10 chiffres (0 ou 1 en tête)", "DK": "DK + 8 chiffres",
    "FI": "FI + 8 chiffres", "IT": "IT + 11 chiffres", "LU": "LU + 8 chiffres", "NL": "NL + 9 chiffres + B + 2 chiffres",
    "PL": "PL + 10 chiffres", "PT": "PT + 9 chiffres", "SE": "SE + 12 chiffres se terminant par 01",
}


# ---------------------------------------------------------------- verdict


def validate(raw: str | None, pays_declare: str | None) -> Verdict:
    n = normalize(raw, pays_declare)
    if n.is_empty:
        return Verdict(ABSENT, "NUMERO_ABSENT", f"valeur brute {raw!r}", n)
    if n.country is None:
        return Verdict(HORS_PERIMETRE, "PAYS_INCONNU", "aucun préfixe pays dans le numéro ni dans pays_declare", n)
    if n.prefix_conflict:
        return Verdict(INVALIDE, "PAYS_INCOHERENT", f"préfixe {n.country} mais pays déclaré {pays_declare}", n)
    if n.country in NON_EU:
        return Verdict(HORS_PERIMETRE, "PAYS_HORS_UE", f"{n.country} : hors Union européenne, non interrogeable dans VIES (Brexit pour GB/UK)", n)
    if n.country in EU_NOT_COVERED:
        return Verdict(HORS_PERIMETRE, "PAYS_NON_COUVERT", f"{n.country} : État membre non couvert par le module structurel", n)
    if n.country not in COVERED:
        return Verdict(HORS_PERIMETRE, "PAYS_INCONNU", f"code pays {n.country} inexistant", n)

    ok, failure_motif = CHECKERS[n.country](n.body or "")
    prefix_note = " ; préfixe ajouté depuis pays_declare" if n.prefix_source == "pays_declare" else ""
    noise_note = " ; bruit de saisie retiré" if n.had_noise else ""
    if ok:
        return Verdict(VALIDE, "OK", f"format et clé corrects{prefix_note}{noise_note}", n)
    return Verdict(INVALIDE, failure_motif, f"attendu : {EXPECTED_FORMAT[n.country]}{prefix_note}{noise_note}", n)
