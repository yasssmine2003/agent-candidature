"""La boucle agentique : le LLM décide, notre code exécute.

Depuis l'étape 4, l'agent ne connaît plus ses outils à l'avance : on les lui passe
en paramètres. Le même code peut donc servir pour n'importe quelle candidature.
"""
import json

from llm import MODELE, client

MAX_TOURS = 5


def construire_system_prompt(cv, offre):
    """Injection de contexte : on donne au modèle les informations courtes et stables.
    Les calculs et les détails passent par les outils."""
    return (
        "Tu aides une candidate à analyser sa candidature à un stage.\n"
        f"Candidate : {cv.nom or 'nom non précisé'}.\n"
        f"Offre : {offre.titre} chez {offre.entreprise or 'entreprise non précisée'}.\n"
        "Pour toute question sur les compétences, l'expérience ou les durées, "
        "utilise les outils au lieu de deviner. "
        "Si une information n'est pas disponible, dis-le clairement. "
        "Réponds en français, de façon concise."
    )


def executer_outil(appel, outils):
    """Exécute UN appel d'outil. Renvoie toujours du texte, même en cas d'erreur."""
    try:
        # Un outil sans arguments peut arriver avec une chaîne vide : on la remplace par "{}".
        arguments = json.loads(appel.function.arguments or "{}")

        if appel.function.name not in outils:
            raise ValueError(f"Outil inconnu : {appel.function.name}")

        resultat = outils[appel.function.name](**arguments)
        # json.dumps produit un texte JSON propre, plus lisible pour le modèle que str().
        return json.dumps(resultat, ensure_ascii=False)

    except Exception as erreur:
        return f"Erreur lors de l'exécution de l'outil : {erreur}"


def executer_agent(messages, outils, tools, trace=False):
    """Fait tourner la boucle jusqu'à une réponse en texte, ou jusqu'à MAX_TOURS.

    messages : l'historique, complété sur place
    outils   : le registre nom -> fonction Python (créé par creer_outils)
    tools    : la description des outils envoyée au LLM
    trace    : si True, affiche chaque appel d'outil (utile pour comprendre et déboguer)
    """
    for _ in range(MAX_TOURS):
        response = client.chat.completions.create(
            model=MODELE,
            messages=messages,
            tools=tools,
            temperature=0,
        )
        msg = response.choices[0].message
        messages.append(msg)

        if not msg.tool_calls:
            return msg.content

        for appel in msg.tool_calls:
            resultat = executer_outil(appel, outils)
            if trace:
                print(f"  [outil] {appel.function.name}({appel.function.arguments}) -> {resultat}")
            messages.append({
                "role": "tool",
                "tool_call_id": appel.id,
                "content": resultat,
            })

    return "Limite de tours atteinte : l'agent n'a pas fourni de réponse finale."