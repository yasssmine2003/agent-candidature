"""Tests de la comparaison par le sens (charge le modèle d'embeddings : quelques secondes)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from outils import comparer_competences, developper


def test_developper_acronyme():
    assert developper("ML") == "ML (machine learning)"
    assert developper("Python") == "Python"  # pas un acronyme connu : inchangé


def test_correspondance_exacte_inchangee():
    r = comparer_competences(["Python", "SQL"], ["python"])
    assert r["presentes"] == ["python"] and r["manquantes"] == []


def test_ml_reconnu_comme_machine_learning():
    r = comparer_competences(["Machine Learning", "SQL"], ["ML"])
    assert r["presentes"] == ["ML"], "La limite du projet 1 doit être corrigée"
    assert r["correspondances"][0]["cv"] == "Machine Learning"


def test_traduction_reconnue():
    r = comparer_competences(["apprentissage automatique"], ["Machine Learning"])
    assert r["presentes"] == ["Machine Learning"]


def test_java_different_de_javascript():
    r = comparer_competences(["JavaScript"], ["Java"])
    assert r["manquantes"] == ["Java"], "Deux compétences proches à l'écrit ne sont pas la même"


def test_listes_vides():
    assert comparer_competences([], ["Python"])["manquantes"] == ["Python"]
    assert comparer_competences(["Python"], [])["presentes"] == []