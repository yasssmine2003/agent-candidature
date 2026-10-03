"""Tests des outils : du Python pur, sans aucun appel au LLM (gratuits et instantanés)."""
import pytest

from modeles import Experience
from outils import (
    calculer_duree_mois,
    comparer_competences,
    experience_totale_mois,
    verifier_experience,
    vers_annee_mois,
)


# --- Dates -----------------------------------------------------------

def test_vers_annee_mois_format_correct():
    assert vers_annee_mois("2025-01") == (2025, 1)


def test_vers_annee_mois_refuse_un_format_invalide():
    with pytest.raises(ValueError):
        vers_annee_mois("mars 2024")


def test_vers_annee_mois_refuse_un_mois_impossible():
    with pytest.raises(ValueError):
        vers_annee_mois("2025-13")


def test_duree_sur_deux_annees():
    assert calculer_duree_mois("2024-03", "2025-08") == 17


# --- Compétences ------------------------------------------------------

def test_comparaison_ignore_majuscules_et_espaces():
    resultat = comparer_competences([" python ", "SQL"], ["Python", "sql", "Docker"])
    assert resultat["presentes"] == ["Python", "sql"]
    assert resultat["manquantes"] == ["Docker"]


def test_comparaison_avec_cv_vide():
    resultat = comparer_competences([], ["Python"])
    assert resultat["manquantes"] == ["Python"]


# --- Expérience -------------------------------------------------------

def test_experience_totale():
    experiences = [
        Experience(poste="Dev", entreprise="A", date_debut="2025-01", date_fin="2025-06"),
        Experience(poste="Dev", entreprise="B", date_debut="2024-01", date_fin="2024-04"),
    ]
    assert experience_totale_mois(experiences) == 5 + 3


def test_experience_insuffisante():
    assert verifier_experience(5, 6) == {"suffisante": False, "ecart_mois": -1}


def test_offre_sans_minimum():
    assert verifier_experience(0, None)["suffisante"] is True