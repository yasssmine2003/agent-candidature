"""Tests des outils : du Python pur, sans aucun appel au LLM (gratuits et instantanés)."""
import pytest

from modeles import Experience, CV, OffreStage
from outils import (
    calculer_duree_mois,
    comparer_avec_sources,
    comparer_competences,
    experience_totale_mois,
    verifier_experience,
    vers_annee_mois,
    competences_supplementaires,
    creer_outils,
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


def test_competence_demontree_comptee_comme_presente():
    resultat = comparer_avec_sources(["Python"], ["RAG"], ["RAG", "Docker"])
    assert resultat["presentes"] == [{"competence": "RAG", "source": "démontrée dans une expérience"}]
    assert resultat["manquantes"] == ["Docker"]


def test_sources_distinguees():
    resultat = comparer_avec_sources(["Python", "SQL"], ["python"], ["Python", "SQL"])
    assert resultat["presentes"] == [
        {"competence": "Python", "source": "déclarée et démontrée"},
        {"competence": "SQL", "source": "déclarée"},
    ]


# --- Expérience -------------------------------------------------------

def test_experience_totale():
    experiences = [
        Experience(poste="Dev", entreprise="A", date_debut="2025-01", date_fin="2025-06",
                   competences_demontrees=[]),
        Experience(poste="Dev", entreprise="B", date_debut="2024-01", date_fin="2024-04",
                   competences_demontrees=[]),
    ]
    assert experience_totale_mois(experiences) == 5 + 3


def test_experience_insuffisante():
    assert verifier_experience(5, 6) == {"suffisante": False, "ecart_mois": -1}


def test_offre_sans_minimum():
    assert verifier_experience(0, None)["suffisante"] is True

def test_competences_supplementaires():
    resultat = competences_supplementaires(["Python", "Git", " FastAPI "], ["python", "Docker"])
    assert resultat == ["Git", " FastAPI "]
def test_analyser_atouts_sans_doublon():
    cv = CV(
        nom="Y",
        competences=["Python", "FastAPI"],
        experiences=[
            Experience(poste="Dev", entreprise="A", date_debut="2025-01", date_fin="2025-06",
                       competences_demontrees=["fastapi", "Git"]),
        ],
    )
    offre = OffreStage(titre="Stage", entreprise="B", competences_requises=["Python"],
                       experience_min_mois=None)
    resultat = creer_outils(cv, offre)["analyser_atouts"]()
    assert resultat == {"atouts": ["FastAPI", "Git"]}
def test_analyser_atouts_ignore_les_espaces():
    cv = CV(
        nom="Y",
        competences=["Git"],
        experiences=[
            Experience(poste="Dev", entreprise="A", date_debut="2025-01", date_fin="2025-06",
                       competences_demontrees=[" git "]),
        ],
    )
    offre = OffreStage(titre="Stage", entreprise="B", competences_requises=[],
                       experience_min_mois=None)
    assert creer_outils(cv, offre)["analyser_atouts"]() == {"atouts": ["Git"]}