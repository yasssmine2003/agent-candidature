"""Tests de l'API avec un faux LLM : on vérifie les routes, pas l'intelligence du modèle."""
import json
from types import SimpleNamespace as NS

import pytest
from fastapi.testclient import TestClient

import agent
import api
import extraction

CV_JSON = {"nom": "Y", "competences": ["Python"], "experiences": [
    {"poste": "Dev", "entreprise": "A", "date_debut": "2025-01", "date_fin": "2025-06",
     "competences_demontrees": []}]}
OFFRE_JSON = {"titre": "Stage", "entreprise": "B", "competences_requises": ["Python", "Docker"],
              "experience_min_mois": 6}


def faux_create(**kwargs):
    """Imite client.chat.completions.create : JSON pour l'extraction, texte pour l'agent."""
    if "response_format" in kwargs:
        donnees = CV_JSON if kwargs["response_format"]["json_schema"]["name"] == "cv" else OFFRE_JSON
        return NS(choices=[NS(message=NS(content=json.dumps(donnees), tool_calls=None))], usage=None)
    message = NS(role="assistant", content="Il te manque Docker.", tool_calls=None)
    return NS(choices=[NS(message=message)], usage=NS(total_tokens=42))


@pytest.fixture
def client(monkeypatch):
    faux_client = NS(chat=NS(completions=NS(create=faux_create)))
    monkeypatch.setattr(extraction, "client", faux_client)
    monkeypatch.setattr(agent, "client", faux_client)
    api.SESSIONS.clear()
    return TestClient(api.app)


TEXTES = {"cv": "Y, développeuse Python chez A de 2025-01 à 2025-06.", "offre": "Stage chez B : Python, Docker."}


def test_sante(client):
    assert client.get("/sante").json() == {"statut": "ok"}


def test_analyse_puis_question(client):
    analyse = client.post("/analyses", json=TEXTES).json()
    assert analyse["cv"]["nom"] == "Y"

    reponse = client.post(f"/analyses/{analyse['session_id']}/questions", json={"question": "Que me manque-t-il ?"})
    assert reponse.status_code == 200
    assert reponse.json()["tokens"] == 42


def test_session_inconnue(client):
    reponse = client.post("/analyses/inexistante/questions", json={"question": "Bonjour"})
    assert reponse.status_code == 404


def test_texte_trop_court_refuse(client):
    reponse = client.post("/analyses", json={"cv": "court", "offre": "court"})
    assert reponse.status_code == 422  # rejeté par Pydantic avant tout appel au LLM