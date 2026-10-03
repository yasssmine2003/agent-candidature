"""Point d'entrée : prépare la conversation et lance l'agent."""
from agent import SYSTEM_PROMPT, executer_agent

messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {
        "role": "user",
        "content": "J'ai travaillé de mars 2024 à août 2025. Combien de mois cela représente-t-il ?",
    },
]

reponse = executer_agent(messages)
print(reponse)
