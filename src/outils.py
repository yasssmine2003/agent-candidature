"""Outils de l'agent : des fonctions Python pures (aucun appel au LLM ici).

Ce fichier contient trois choses :
1. les fonctions elles-mêmes ;
2. OUTILS : le registre qui associe un nom à une fonction (utilisé par notre code) ;
3. TOOLS : la description des outils au format JSON (lue par le LLM).
"""
from datetime import date


# ============================================================
# 1. Les fonctions
# ============================================================

def vers_annee_mois(texte):
    """Transforme "2025-01" en (2025, 1), avec des erreurs claires si le format est faux."""
    morceaux = texte.split("-")

    if len(morceaux) != 2:
        raise ValueError("La date doit respecter le format AAAA-MM.")

    annee = int(morceaux[0])
    mois = int(morceaux[1])

    if mois < 1 or mois > 12:
        raise ValueError("Le mois doit être compris entre 1 et 12.")

    return annee, mois


def duree_mois(debut, fin):
    """Écart en mois entre deux tuples (annee, mois). fin=None signifie "aujourd'hui"."""
    if fin is None:
        fin = (date.today().year, date.today().month)

    annee_debut, mois_debut = debut
    annee_fin, mois_fin = fin

    # Choix de conception : on calcule l'écart (janvier -> juin = 5 mois).
    return (annee_fin - annee_debut) * 12 + (mois_fin - mois_debut)


def calculer_duree_mois(date_debut, date_fin=None):
    """Fonction d'adaptation : reçoit des textes "AAAA-MM" (le format envoyé par le LLM)."""
    debut = vers_annee_mois(date_debut)
    fin = None if date_fin is None else vers_annee_mois(date_fin)
    return duree_mois(debut, fin)


# ============================================================
# 2. Registre : nom de l'outil -> fonction Python
# ============================================================

OUTILS = {
    "calculer_duree_mois": calculer_duree_mois,
}


# ============================================================
# 3. Description des outils pour le LLM
# ============================================================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculer_duree_mois",
            "description": (
                "Calcule le nombre de mois entre deux dates au format AAAA-MM. "
                "Omettre date_fin si le poste est encore en cours."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "date_debut": {"type": "string", "description": "Date de début au format AAAA-MM"},
                    "date_fin": {"type": "string", "description": "Date de fin au format AAAA-MM"},
                },
                "required": ["date_debut"],
            },
        },
    }
]
