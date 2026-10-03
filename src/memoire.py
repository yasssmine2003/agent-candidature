"""Mémoire courte : garder l'historique de conversation sous contrôle.

Chaque tour renvoie tout l'historique au LLM : sans limite, le coût et la lenteur
augmentent à chaque question, jusqu'à dépasser la fenêtre de contexte.
"""


def role_de(message):
    """Les messages sont soit des dictionnaires (les nôtres), soit des objets (ceux renvoyés par Groq)."""
    return message["role"] if isinstance(message, dict) else message.role


def tronquer_historique(messages, max_questions=5):
    """Garde le system prompt + les `max_questions` dernières questions, avec tout ce qui les suit.

    On coupe toujours JUSTE AVANT une question de l'utilisateur. Ainsi, une demande d'outil
    (message assistant avec tool_calls) n'est jamais séparée de son résultat (message tool) :
    l'API refuserait un résultat d'outil sans la demande correspondante.
    """
    indices_questions = [i for i, m in enumerate(messages) if role_de(m) == "user"]

    if len(indices_questions) <= max_questions:
        return messages

    debut = indices_questions[-max_questions]
    return [messages[0]] + messages[debut:]