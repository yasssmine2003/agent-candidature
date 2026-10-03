"""Point d'entrée de l'étape 6 : conversation avec l'agent, avec contrôles de sécurité."""
import sys
from pathlib import Path

from agent import construire_system_prompt, executer_agent
from extraction import extraire_cv, extraire_offre
from memoire import tronquer_historique
from outils import TOOLS, creer_outils
from securite import detecter_injection, verifier_ancrage

DOSSIER_DATA = Path(__file__).parent.parent / "data"
MAX_QUESTIONS_GARDEES = 5

# Le fichier CV peut être choisi au lancement : python src/main.py data/cv_piege.txt
chemin_cv = Path(sys.argv[1]) if len(sys.argv) > 1 else DOSSIER_DATA / "cv_exemple.txt"
texte_cv = chemin_cv.read_text(encoding="utf-8")
texte_offre = (DOSSIER_DATA / "offre_exemple.txt").read_text(encoding="utf-8")

# 0. Contrôle AVANT le LLM : le texte contient-il des instructions suspectes ?
for nom, texte in [("CV", texte_cv), ("offre", texte_offre)]:
    suspects = detecter_injection(texte)
    if suspects:
        print(f"ALERTE : le texte du {nom} contient des formulations suspectes : {suspects}")
        print("         Vérifie ce document manuellement avant de te fier à l'analyse.\n")

# 1. Démarrage : workflow fixe, une seule fois
print(f"Analyse du CV ({chemin_cv.name}) et de l'offre...")
cv = extraire_cv(texte_cv)
offre = extraire_offre(texte_offre)

# 2. Contrôle APRÈS le LLM : chaque compétence extraite existe-t-elle dans le texte ?
non_ancrees = verifier_ancrage(cv, texte_cv)
if non_ancrees:
    print(f"ALERTE : compétences extraites introuvables dans le CV original : {non_ancrees}\n")

outils = creer_outils(cv, offre)

# 3. Conversation
messages = [{"role": "system", "content": construire_system_prompt(cv, offre)}]
print(f"Prêt. Offre analysée : {offre.titre}. Tape 'quit' pour quitter.")

while True:
    question = input("\nToi : ").strip()

    if question.lower() in {"quit", "exit"}:
        break
    if not question:
        continue

    messages.append({"role": "user", "content": question})
    messages = tronquer_historique(messages, MAX_QUESTIONS_GARDEES)

    try:
        reponse = executer_agent(messages, outils, TOOLS, trace=True)
    except Exception as erreur:
        # Erreur d'API (quota 429, réseau...) : on prévient sans perdre la conversation.
        # Le SDK Groq réessaie déjà automatiquement quelques fois avant d'en arriver là.
        messages.pop()  # retire la question restée sans réponse
        print(f"\nErreur lors de l'appel au modèle : {erreur}. Réessaie dans un instant.")
        continue

    print(f"\nAgent : {reponse}")