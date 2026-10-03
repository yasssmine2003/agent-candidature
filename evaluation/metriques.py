"""Fonctions de notation de l'évaluation : du Python pur, testable sans LLM."""


def verifier_outils(appeles, acceptables):
    """Le choix d'outils est correct si l'ensemble des outils appelés correspond
    à l'une des combinaisons acceptables. Plusieurs trajectoires peuvent être valides."""
    return any(set(appeles) == set(option) for option in acceptables)


def verifier_contenu(reponse, cas):
    """Vérifications simples sur le texte de la réponse : mots attendus et mots interdits.
    Renvoie (réussite, liste des problèmes)."""
    texte = (reponse or "").lower()
    problemes = []

    for mot in cas.get("doit_contenir", []):
        if mot.lower() not in texte:
            problemes.append(f"absent : {mot}")

    for mot in cas.get("ne_doit_pas_contenir", []):
        if mot.lower() in texte:
            problemes.append(f"interdit présent : {mot}")

    return len(problemes) == 0, problemes


def calculer_resume(resultats):
    """Agrège les résultats de tous les cas en quelques indicateurs."""
    n = len(resultats)
    if n == 0:
        return {}

    def taux(cle):
        return round(100 * sum(r[cle] for r in resultats) / n, 1)

    return {
        "nombre_executions": n,
        "choix_outils_correct_pct": taux("outils_ok"),
        "contenu_correct_pct": taux("contenu_ok"),
        "reussite_complete_pct": taux("reussite"),
        "erreurs": sum(1 for r in resultats if r["erreur"]),
        "latence_moyenne_s": round(sum(r["latence_s"] for r in resultats) / n, 2),
        "tokens_moyens": round(sum(r["tokens"] for r in resultats) / n),
        "appels_outils_moyens": round(sum(r["nb_appels"] for r in resultats) / n, 2),
    }