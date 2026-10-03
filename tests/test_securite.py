"""Tests des défenses : on rejoue l'attaque du CV piégé, sans appeler le LLM."""
from pathlib import Path

from modeles import CV, Experience
from securite import detecter_injection, verifier_ancrage

DATA = Path(__file__).parent.parent / "data"


def test_cv_piege_detecte():
    assert detecter_injection((DATA / "cv_piege.txt").read_text(encoding="utf-8")) != []


def test_cv_normal_sans_alerte():
    assert detecter_injection((DATA / "cv_exemple.txt").read_text(encoding="utf-8")) == []


def test_offre_sans_alerte():
    assert detecter_injection((DATA / "offre_exemple.txt").read_text(encoding="utf-8")) == []


def test_competence_inventee_detectee():
    cv = CV(
        nom="Y",
        competences=["Python", "Kubernetes"],  # Kubernetes n'est pas dans le texte
        experiences=[
            Experience(poste="Dev", entreprise="A", date_debut="2025-01", date_fin="2025-06",
                       competences_demontrees=["FastAPI"]),
        ],
    )
    texte = "Compétences : Python. Développement d'API avec FastAPI."
    assert verifier_ancrage(cv, texte) == ["Kubernetes"]