"""Tests de la mémoire courte, avec de faux messages (aucun appel au LLM)."""
from memoire import tronquer_historique


def faux_echange(n):
    """Une question, une demande d'outil, son résultat, puis la réponse finale."""
    return [
        {"role": "user", "content": f"question {n}"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": f"appel{n}"}]},
        {"role": "tool", "tool_call_id": f"appel{n}", "content": "résultat"},
        {"role": "assistant", "content": f"réponse {n}"},
    ]


def historique(nb_questions):
    messages = [{"role": "system", "content": "consignes"}]
    for n in range(1, nb_questions + 1):
        messages += faux_echange(n)
    return messages


def test_historique_court_inchange():
    messages = historique(2)
    assert tronquer_historique(messages, max_questions=5) == messages


def test_garde_le_system_prompt():
    resultat = tronquer_historique(historique(8), max_questions=3)
    assert resultat[0]["role"] == "system"


def test_garde_les_dernieres_questions():
    resultat = tronquer_historique(historique(8), max_questions=3)
    questions = [m["content"] for m in resultat if m["role"] == "user"]
    assert questions == ["question 6", "question 7", "question 8"]


def test_ne_separe_jamais_un_outil_de_sa_demande():
    resultat = tronquer_historique(historique(8), max_questions=3)
    # Juste après le system prompt, on doit trouver une question, jamais un résultat d'outil orphelin.
    assert resultat[1]["role"] == "user"