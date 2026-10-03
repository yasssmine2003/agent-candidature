"""Évaluation automatique de l'agent sur un jeu de cas de test.

Lancement, depuis la racine du projet :  python evaluation/evaluer.py
Attention : chaque cas appelle réellement le LLM (consomme ton quota Groq).
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).parent.parent
sys.path.insert(0, str(RACINE / "src"))  # pour importer les modules du projet

from agent import construire_system_prompt, executer_agent  # noqa: E402
from extraction import extraire_cv, extraire_offre  # noqa: E402
from metriques import calculer_resume, verifier_contenu, verifier_outils  # noqa: E402
from outils import TOOLS, creer_outils  # noqa: E402

NB_REPETITIONS = 1   # passe à 3 pour mesurer la stabilité (le LLM n'est pas déterministe)
PAUSE_SECONDES = 1   # petite pause entre les cas pour ménager le quota gratuit


def evaluer_cas(cas, cv, offre, outils):
    """Exécute UNE question sur une conversation neuve, et note le résultat."""
    messages = [
        {"role": "system", "content": construire_system_prompt(cv, offre)},
        {"role": "user", "content": cas["question"]},
    ]
    journal = {"outils": [], "tokens": 0}

    debut = time.perf_counter()
    try:
        reponse = executer_agent(messages, outils, TOOLS, journal=journal)
        erreur = None
    except Exception as e:
        reponse, erreur = "", str(e)
    latence = time.perf_counter() - debut

    outils_ok = verifier_outils(journal["outils"], cas["outils_acceptables"])
    contenu_ok, problemes = verifier_contenu(reponse, cas)

    return {
        "id": cas["id"],
        "question": cas["question"],
        "outils_appeles": journal["outils"],
        "nb_appels": len(journal["outils"]),
        "outils_ok": outils_ok,
        "contenu_ok": contenu_ok,
        "reussite": outils_ok and contenu_ok and erreur is None,
        "problemes": problemes,
        "erreur": erreur,
        "latence_s": round(latence, 2),
        "tokens": journal["tokens"],
        "reponse": reponse,
    }


def main():
    cas_de_test = json.loads((RACINE / "evaluation" / "cas_de_test.json").read_text(encoding="utf-8"))

    # Extraction une seule fois, comme dans l'application réelle
    cv = extraire_cv((RACINE / "data" / "cv_exemple.txt").read_text(encoding="utf-8"))
    offre = extraire_offre((RACINE / "data" / "offre_exemple.txt").read_text(encoding="utf-8"))
    outils = creer_outils(cv, offre)

    resultats = []
    for cas in cas_de_test:
        for _ in range(NB_REPETITIONS):
            r = evaluer_cas(cas, cv, offre, outils)
            resultats.append(r)
            statut = "OK   " if r["reussite"] else "ECHEC"
            detail = "" if r["reussite"] else f"  outils={r['outils_appeles']} {r['problemes']} {r['erreur'] or ''}"
            print(f"[{statut}] {r['id']:<24} {r['latence_s']:>5}s {r['tokens']:>6} tokens{detail}")
            time.sleep(PAUSE_SECONDES)

    resume = calculer_resume(resultats)
    print("\n=== Résumé ===")
    for cle, valeur in resume.items():
        print(f"{cle:<28} {valeur}")

    horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")
    fichier = RACINE / "evaluation" / f"resultats_{horodatage}.json"
    fichier.write_text(
        json.dumps({"resume": resume, "details": resultats}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nDétails enregistrés dans {fichier.relative_to(RACINE)}")


if __name__ == "__main__":
    main()