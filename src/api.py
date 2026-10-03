"""API web de l'agent (étape 8).

Lancement en local, depuis la racine du projet :
    uvicorn api:app --app-dir src --reload
Documentation interactive : http://127.0.0.1:8000/docs
"""
import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from agent import construire_system_prompt, executer_agent
from extraction import extraire_cv, extraire_offre
from memoire import tronquer_historique
from modeles import CV, OffreStage
from outils import TOOLS, creer_outils
from securite import detecter_injection, verifier_ancrage

MAX_QUESTIONS_GARDEES = 5
MAX_CARACTERES = 20_000  # limite la taille des textes : coût maîtrisé, abus plus difficiles

app = FastAPI(
    title="Agent d'analyse de candidature",
    description="Analyse un CV face à une offre de stage, puis répond à des questions libres.",
    version="1.0",
)

# Simplification pédagogique : les sessions vivent en mémoire.
# Elles disparaissent au redémarrage et ne sont pas partagées entre plusieurs serveurs.
# En production : une base comme PostgreSQL ou Redis.
SESSIONS = {}


# ------------------------------------------------------------
# Schémas des requêtes et des réponses (validés par Pydantic)
# ------------------------------------------------------------

class DemandeAnalyse(BaseModel):
    cv: str = Field(min_length=20, max_length=MAX_CARACTERES, description="Texte brut du CV")
    offre: str = Field(min_length=20, max_length=MAX_CARACTERES, description="Texte brut de l'offre")


class ResultatAnalyse(BaseModel):
    session_id: str
    cv: CV
    offre: OffreStage
    alertes: list[str]


class Question(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


class Reponse(BaseModel):
    reponse: str
    outils_appeles: list[str]
    tokens: int


# ------------------------------------------------------------
# Routes
# ------------------------------------------------------------

@app.get("/sante")
def sante():
    """Vérification que le service tourne (utilisée par Docker ou un hébergeur)."""
    return {"statut": "ok"}


@app.post("/analyses", response_model=ResultatAnalyse)
def creer_analyse(demande: DemandeAnalyse):
    """Étape de démarrage : contrôles de sécurité, extraction, création d'une session."""
    alertes = []
    for nom, texte in [("CV", demande.cv), ("offre", demande.offre)]:
        suspects = detecter_injection(texte)
        if suspects:
            alertes.append(f"Formulations suspectes dans le texte du {nom} : {suspects}")

    try:
        cv = extraire_cv(demande.cv)
        offre = extraire_offre(demande.offre)
    except Exception:
        # On ne renvoie pas le détail de l'erreur interne au client (il pourrait révéler des
        # informations sur le système). En production, on l'enregistrerait dans les logs.
        raise HTTPException(status_code=502, detail="L'analyse par le modèle a échoué. Réessaie plus tard.")

    non_ancrees = verifier_ancrage(cv, demande.cv)
    if non_ancrees:
        alertes.append(f"Compétences extraites introuvables dans le CV original : {non_ancrees}")

    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = {
        "outils": creer_outils(cv, offre),
        "messages": [{"role": "system", "content": construire_system_prompt(cv, offre)}],
    }

    return ResultatAnalyse(session_id=session_id, cv=cv, offre=offre, alertes=alertes)


@app.post("/analyses/{session_id}/questions", response_model=Reponse)
def poser_question(session_id: str, question: Question):
    """Étape de conversation : une question, avec la mémoire courte de la session."""
    session = SESSIONS.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session inconnue. Crée d'abord une analyse.")

    messages = session["messages"] + [{"role": "user", "content": question.question}]
    messages = tronquer_historique(messages, MAX_QUESTIONS_GARDEES)
    journal = {"outils": [], "tokens": 0}

    try:
        reponse = executer_agent(messages, session["outils"], TOOLS, journal=journal)
    except Exception:
        raise HTTPException(status_code=502, detail="Le modèle n'a pas pu répondre. Réessaie plus tard.")

    # L'historique n'est enregistré qu'en cas de succès : une erreur ne laisse pas de question orpheline.
    session["messages"] = messages

    return Reponse(reponse=reponse, outils_appeles=journal["outils"], tokens=journal["tokens"])