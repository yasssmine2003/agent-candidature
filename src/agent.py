"""La boucle agentique : le LLM décide, notre code exécute."""

import json

from llm import MODELE, client
from outils import OUTILS, TOOLS

MAX_TOURS = 5
SYSTEM_PROMPT = (
    "Tu es un assistant qui aide une candidate à analyser sa candidature à un stage. "
    "Pour tout calcul de durée, utilise les outils disponibles au lieu de calculer toi-même. "
    "Réponds en français, de façon concise."
)


def executer_outil(appel):
    """Exécute UN appel d'outil demandé par le modèle. Renvoie toujours une chaîne,
    même en cas d'erreur : l'erreur devient une information que le modèle peut utiliser."""
    try:
        arguments = json.loads(appel.function.arguments)

        if appel.function.name not in OUTILS:
            raise ValueError(f"Outil inconnu : {appel.function.name}")

        resultat = OUTILS[appel.function.name](**arguments)
        return str(resultat)

    except Exception as erreur:
        return f"Erreur lors de l'exécution de l'outil : {erreur}"


def executer_agent(messages):
    """Fait tourner la boucle jusqu'à une réponse en texte, ou jusqu'à MAX_TOURS.
    `messages` est modifiée sur place : l'historique complet reste disponible après l'appel."""
    for _ in range(MAX_TOURS):
        response = client.chat.completions.create(
            model=MODELE,
            messages=messages,
            tools=TOOLS,
            temperature=0,
        )
        msg = response.choices[0].message
        messages.append(msg)

        # Pas de demande d'outil : le modèle a fini.
        if not msg.tool_calls:
            return msg.content

        # Sinon : exécuter chaque outil demandé et renvoyer son résultat au modèle.
        for appel in msg.tool_calls:
            messages.append({
                "role": "tool",
                "tool_call_id": appel.id,
                "content": executer_outil(appel),
            })

    return "Limite de tours atteinte : l'agent n'a pas fourni de réponse finale."
