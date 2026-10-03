"""Tests des fonctions de notation : une évaluation fausse serait pire que pas d'évaluation."""
from metriques import calculer_resume, verifier_contenu, verifier_outils


def test_outils_ordre_sans_importance():
    assert verifier_outils(["b", "a"], [["a", "b"]])


def test_outils_plusieurs_trajectoires_acceptables():
    assert verifier_outils(["lister"], [["lister"], ["lister", "calculer"]])


def test_outil_manquant_detecte():
    assert not verifier_outils(["a"], [["a", "b"]])


def test_aucun_outil_attendu():
    assert verifier_outils([], [[]])
    assert not verifier_outils(["a"], [[]])


def test_contenu_mot_absent():
    ok, problemes = verifier_contenu("Il manque Docker", {"doit_contenir": ["Docker", "LLM"]})
    assert not ok and problemes == ["absent : LLM"]


def test_contenu_mot_interdit():
    ok, _ = verifier_contenu("Le salaire est de 800 DT", {"ne_doit_pas_contenir": ["DT"]})
    assert not ok


def test_resume():
    resultats = [
        {"outils_ok": True, "contenu_ok": True, "reussite": True, "erreur": None,
         "latence_s": 1.0, "tokens": 100, "nb_appels": 1},
        {"outils_ok": False, "contenu_ok": True, "reussite": False, "erreur": None,
         "latence_s": 3.0, "tokens": 300, "nb_appels": 3},
    ]
    resume = calculer_resume(resultats)
    assert resume["choix_outils_correct_pct"] == 50.0
    assert resume["latence_moyenne_s"] == 2.0
    assert resume["tokens_moyens"] == 200