"""Outils de l'agent : des fonctions Python pures (aucun appel au LLM ici).

Ce fichier contient trois choses :
1. les fonctions elles-mêmes ;
2. OUTILS : le registre qui associe un nom à une fonction (utilisé par notre code) ;
3. TOOLS : la description des outils au format JSON (lue par le LLM).
"""
from datetime import date
from embeddings import encoder


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


def normaliser(competence):
    """"  Python " et "python" doivent être considérés comme identiques."""
    return competence.strip().lower()


# ============================================================
# À COLLER dans src/outils.py, À LA PLACE de l'ancienne fonction comparer_competences.
# Garde ta fonction normaliser(), elle est réutilisée ici.
# Ajoute en haut du fichier :   from embeddings import encoder
# ============================================================

# Les embeddings comprennent mal les acronymes courts (étape 0 : « ML » / « Machine Learning » = 0.338).
# On les développe AVANT la comparaison : c'est l'expansion de requête, rendue automatique.
ACRONYMES = {
    "ml": "machine learning",
    "dl": "deep learning",
    "nlp": "natural language processing",
    "taln": "traitement automatique du langage naturel",
    "ia": "intelligence artificielle",
    "ai": "artificial intelligence",
    "llm": "large language model",
    "bdd": "base de données",
    "poo": "programmation orientée objet",
    "oop": "object-oriented programming",
}

# Score minimal pour considérer deux compétences comme identiques.
# NE PAS DEVINER : calibre-le avec src/calibrer_seuil.py, puis reporte la valeur ici.
SEUIL_SIMILARITE = 0.75


def developper(competence):
    """'ML' -> 'ML (machine learning)'. Garde le terme d'origine et ajoute sa forme longue."""
    cle = normaliser(competence)
    return f"{competence} ({ACRONYMES[cle]})" if cle in ACRONYMES else competence


def comparer_competences(competences_cv, competences_offre, seuil=SEUIL_SIMILARITE):
    """Renvoie les compétences de l'offre présentes dans le CV, et celles qui manquent.

    Comparaison PAR LE SENS (projet 2) : acronymes développés, puis embeddings + seuil.
    Le contrat est inchangé (presentes / manquantes = listes de textes) ; la clé
    `correspondances` explique chaque rapprochement, pour la transparence.
    """
    if not competences_offre:
        return {"presentes": [], "manquantes": [], "correspondances": []}
    if not competences_cv:
        return {"presentes": [], "manquantes": list(competences_offre), "correspondances": []}

    exactes = {normaliser(c): c for c in competences_cv}

    # Tous les scores d'un coup : matrice (nb compétences offre) x (nb compétences CV).
    # Les vecteurs sont normalisés, donc le produit scalaire EST le cosinus (étape 2).
    v_offre = encoder([developper(c) for c in competences_offre])
    v_cv = encoder([developper(c) for c in competences_cv])
    scores = v_offre @ v_cv.T

    presentes, manquantes, correspondances = [], [], []
    for i, competence in enumerate(competences_offre):
        # 1. Correspondance exacte : réglé, pas besoin du sens
        if normaliser(competence) in exactes:
            presentes.append(competence)
            correspondances.append({"offre": competence, "cv": exactes[normaliser(competence)], "score": 1.0})
            continue
        # 2. Sinon, la compétence du CV la plus proche par le sens
        j = int(scores[i].argmax())
        if scores[i, j] >= seuil:
            presentes.append(competence)
            correspondances.append(
                {"offre": competence, "cv": competences_cv[j], "score": round(float(scores[i, j]), 3)}
            )
        else:
            manquantes.append(competence)

    return {"presentes": presentes, "manquantes": manquantes, "correspondances": correspondances}

#nouvel  outil 
def competences_supplementaires(competences_cv, competences_offre):
    """Renvoie les compétences du CV que l'offre ne demande pas."""
    offre={normaliser(c) for c in competences_offre}
    supplementaires=[c for c in competences_cv if normaliser(c) not in offre]
    return supplementaires



def comparer_avec_sources(declarees, demontrees, requises):
    """Comme comparer_competences, mais en tenant compte des compétences démontrées
    dans les expériences, et en indiquant d'où vient chaque compétence trouvée.

    Une compétence déclarée ET démontrée est marquée "déclarée et démontrée" : c'est la plus solide.
    """
    declarees_norm = {normaliser(c) for c in declarees}
    demontrees_norm = {normaliser(c) for c in demontrees}

    resultat = comparer_competences(list(declarees) + list(demontrees), requises)

    presentes = []
    for c in resultat["presentes"]:
        dans_declarees = normaliser(c) in declarees_norm
        dans_demontrees = normaliser(c) in demontrees_norm
        if dans_declarees and dans_demontrees:
            source = "déclarée et démontrée"
        elif dans_declarees:
            source = "déclarée"
        else:
            source = "démontrée dans une expérience"
        presentes.append({"competence": c, "source": source})

    return {"presentes": presentes, "manquantes": resultat["manquantes"]}


def experience_totale_mois(experiences):
    """Somme des durées de toutes les expériences, en mois.

    Simplification pédagogique : deux expériences qui se chevauchent sont comptées deux fois.
    """
    return sum(calculer_duree_mois(e.date_debut, e.date_fin) for e in experiences)


def verifier_experience(total_mois, minimum_mois):
    """Compare l'expérience de la candidate au minimum demandé par l'offre."""
    if minimum_mois is None:
        return {"suffisante": True, "detail": "L'offre ne précise pas d'expérience minimale."}

    ecart = total_mois - minimum_mois
    return {"suffisante": ecart >= 0, "ecart_mois": ecart}


# ============================================================
# 2. Outils liés à UNE candidature (l'état de l'agent)
# ============================================================

def creer_outils(cv, offre):
    """Crée le registre d'outils pour une candidature donnée.

    Les fonctions définies ici « se souviennent » de `cv` et `offre` (c'est une closure) :
    le LLM peut les appeler sans arguments, il n'a jamais à recopier le CV.
    """

    def analyser_competences():
        demontrees = [c for e in cv.experiences for c in e.competences_demontrees]
        return comparer_avec_sources(cv.competences, demontrees, offre.competences_requises)

    def analyser_experience():
        total = experience_totale_mois(cv.experiences)
        resultat = verifier_experience(total, offre.experience_min_mois)
        resultat["total_mois"] = total
        resultat["minimum_mois"] = offre.experience_min_mois
        return resultat

    def lister_experiences():
        return [
            {
                "poste": e.poste,
                "entreprise": e.entreprise,
                "date_debut": e.date_debut,
                "date_fin": e.date_fin or "en cours",
                "duree_mois": calculer_duree_mois(e.date_debut, e.date_fin),
                "competences_demontrees": e.competences_demontrees,
            }
            for e in cv.experiences
        ]
    def analyser_atouts():
        demontrees = [c for e in cv.experiences for c in e.competences_demontrees]
        toutes = cv.competences + demontrees
        uniques=[]
        vus=set()
        for e in toutes:
            cle=normaliser(e)
            if cle not in vus:
                vus.add(cle)
                uniques.append(e)
        
        return {"atouts": competences_supplementaires(uniques, offre.competences_requises)}

    return {
        "analyser_competences": analyser_competences,
        "analyser_experience": analyser_experience,
        "lister_experiences": lister_experiences,
        "calculer_duree_mois": calculer_duree_mois,
        "analyser_atouts": analyser_atouts,
    }
    


# ============================================================
# 3. Description des outils pour le LLM
# ============================================================

SANS_ARGUMENTS = {"type": "object", "properties": {}}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "analyser_competences",
            "description": (
                "Compare les compétences du CV (déclarées dans la section compétences et "
                "démontrées dans les expériences) à celles demandées par l'offre. "
                "Renvoie les compétences présentes avec leur source, et les compétences manquantes."
            ),
            "parameters": SANS_ARGUMENTS,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyser_experience",
            "description": (
                "Calcule l'expérience totale de la candidate en mois et indique "
                "si elle atteint le minimum demandé par l'offre."
            ),
            "parameters": SANS_ARGUMENTS,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lister_experiences",
            "description": (
                "Liste les expériences du CV avec le poste, l'entreprise, les dates et la durée en mois. "
                "Utile pour les questions sur une expérience précise."
            ),
            "parameters": SANS_ARGUMENTS,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculer_duree_mois",
            "description": (
                "Calcule le nombre de mois entre deux dates au format AAAA-MM. "
                "Omettre date_fin si la période est encore en cours."
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
    },
        {
        "type": "function",
        "function": {
            "name": "analyser_atouts",
            "description": (
                "Renvoie les compétences du CV qui ne sont pas demandées par l'offre, "
                "c'est-à-dire les atouts supplémentaires de la candidate."
                
            ),
            "parameters": SANS_ARGUMENTS,
        },
    },
]