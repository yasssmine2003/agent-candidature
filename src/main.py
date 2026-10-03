"""Point d'entrée de l'étape 4 : extraction, puis une question à l'agent."""
from pathlib import Path

from agent import construire_system_prompt, executer_agent
from extraction import extraire_cv, extraire_offre
from outils import TOOLS, creer_outils

DOSSIER_DATA = Path(__file__).parent.parent / "data"

# 1. Démarrage : workflow fixe, une seule fois
cv = extraire_cv((DOSSIER_DATA / "cv_exemple.txt").read_text(encoding="utf-8"))
offre = extraire_offre((DOSSIER_DATA / "offre_exemple.txt").read_text(encoding="utf-8"))

# 2. Les outils, liés à cette candidature
outils = creer_outils(cv, offre)

# 3. La question, traitée par l'agent
question = "Ai-je assez d'expérience pour ce stage, et quelles compétences me manquent ?"
messages = [
    {"role": "system", "content": construire_system_prompt(cv, offre)},
    {"role": "user", "content": question},
]

print("Question :", question)
print(executer_agent(messages, outils, TOOLS, trace=True))