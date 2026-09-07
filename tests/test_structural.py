"""Normalisation et contrôle structurel : chaque décision documentée a son test."""

import pytest

from meridian_tva.normalize import normalize
from meridian_tva.structural import ABSENT, HORS_PERIMETRE, INVALIDE, VALIDE, validate


@pytest.mark.parametrize("raw", ["", " ", "-", "N/A", "null", "NU.LL", "  N/A  ", "NONE"])
def test_empty_forms_are_detected_before_normalization(raw):
    v = validate(raw, "FR")
    assert v.verdict == ABSENT and v.motif == "NUMERO_ABSENT"
    assert normalize(raw, "FR").compact is None


def test_noise_is_removed_but_not_repaired():
    n = normalize("  fr-27 552 032 534 ", "FR")
    assert n.compact == "FR27552032534" and n.had_noise and n.prefix_source == "numero"
    assert validate("FR2755203253O", "FR").motif == "CARACTERES_INVALIDES"  # O à la place de 0 : pas de réparation


def test_missing_prefix_uses_declared_country():
    n = normalize("27552032534", "FR")
    assert n.compact == "FR27552032534" and n.prefix_source == "pays_declare"
    assert validate("27552032534", "FR").verdict == VALIDE


def test_prefix_conflict_is_flagged_not_guessed():
    v = validate("FR27552032534", "BE")
    assert v.verdict == INVALIDE and v.motif == "PAYS_INCOHERENT"


@pytest.mark.parametrize("raw,pays,motif", [
    ("GB0749640348", "GB", "PAYS_HORS_UE"),
    ("UK227979060", "UK", "PAYS_HORS_UE"),
    ("ZZ23140153", "ZZ", "PAYS_INCONNU"),
    ("QQ72558658", "QQ", "PAYS_INCONNU"),
    ("DE811128135", "DE", "PAYS_NON_COUVERT"),
])
def test_out_of_scope_countries(raw, pays, motif):
    v = validate(raw, pays)
    assert v.verdict == HORS_PERIMETRE and v.motif == motif and not v.eligible_vies


# Numéros réels publics (clé de contrôle exacte) et leurs variantes à clé fausse
VALID_NUMBERS = [
    ("FR27552032534", "FR"),   # SA DANONE
    ("FR89380129866", "FR"),   # SA ORANGE
    ("BE0440832930", "BE"),    # Colruyt Group
    ("DK13585628", "DK"),      # Carlsberg
    ("FI01120389", "FI"),      # Nokia
    ("IT00743110157", "IT"),   # Pirelli
    ("LU20260743", "LU"),      # ArcelorMittal
    ("NL004495445B01", "NL"),  # Heineken NV
    ("PL5260250995", "PL"),    # Orlen
    ("PT500697256", "PT"),     # EDP
    ("SE556012579001", "SE"),  # Volvo AB (organisationsnummer 556012-5790)
]


@pytest.mark.parametrize("number,pays", VALID_NUMBERS)
def test_real_numbers_pass_structural_check(number, pays):
    v = validate(number, pays)
    assert (v.verdict, v.motif) == (VALIDE, "OK"), v.detail


@pytest.mark.parametrize("number,pays", VALID_NUMBERS)
def test_wrong_check_digit_is_rejected(number, pays):
    # on altère le dernier chiffre (avant le suffixe fixe pour SE, avant B.. pour NL le dernier des 9 chiffres)
    if pays == "SE":
        altered = number[:-3] + str((int(number[-3]) + 1) % 10) + number[-2:]
    elif pays == "NL":
        altered = number[:10] + str((int(number[10]) + 1) % 10) + number[11:]
    else:
        altered = number[:-1] + str((int(number[-1]) + 1) % 10)
    v = validate(altered, pays)
    assert v.verdict == INVALIDE and v.motif == "CLE_INVALIDE", (altered, v.detail)


def test_fr_alphabetic_key_is_supported():
    # clé alphanumérique valide construite avec l'algorithme officiel pour le SIREN 552032534 : clé numérique 27 -> équivalent lettres non unique,
    # on vérifie donc seulement qu'une clé alphabétique mal formée est rejetée et qu'une clé avec I ou O est refusée
    assert validate("FRAO552032534", "FR").motif == "CARACTERES_INVALIDES"
    assert validate("FRZZ552032534", "FR").motif == "CLE_INVALIDE"


@pytest.mark.parametrize("number,pays,motif", [
    ("BE123456789", "BE", "LONGUEUR_INVALIDE"),      # ancien format à 9 chiffres : non complété automatiquement
    ("BE2123456789", "BE", "FORMAT_INVALIDE"),       # premier chiffre 2
    ("SE556012579002", "SE", "FORMAT_INVALIDE"),     # suffixe différent de 01
    ("NL004495445A01", "NL", "FORMAT_INVALIDE"),     # lettre autre que B
    ("FR2755203253", "FR", "LONGUEUR_INVALIDE"),
    ("DK1358562", "DK", "LONGUEUR_INVALIDE"),
    ("FR", "FR", "LONGUEUR_INVALIDE"),               # préfixe seul
])
def test_format_and_length_motifs(number, pays, motif):
    v = validate(number, pays)
    assert v.verdict == INVALIDE and v.motif == motif, v.detail


def test_nl_new_mod97_rule():
    # btw-id (règle mod 97 depuis 2020) : NL000000093B12 est valide sous mod 97 (NL->2321, B->11) mais pas sous l'ancienne règle mod 11
    assert validate("NL000000093B12", "NL").verdict == VALIDE
    assert validate("NL000000094B12", "NL").motif == "CLE_INVALIDE"
