"""Défenses de l'étape 6. Aucune n'est parfaite seule : on les empile (défense en profondeur).

Ces vérifications ne bloquent rien : elles ALERTENT. La décision revient à un humain.
"""
import re

from outils import normaliser

# Formulations typiques d'une tentative de manipulation. Liste volontairement simple :
# un attaquant motivé peut la contourner, c'est une alerte, pas une garantie.
MOTIFS_SUSPECTS = [
    r"ignor\w* (toutes |tous )?(les |tes |vos )?(consignes|instructions|règles)",
    r"(consignes|instructions) précédentes",
    r"note pour (le|l')\s?(système|systeme|ia|assistant|agent)",
    r"système d'analyse",
    r"réponds? (qu|que)",
    r"tu es (maintenant|désormais)",
    r"ignore (all|previous|the above)",
    r"system prompt",
]


def detecter_injection(texte):
    """Renvoie les passages du texte qui ressemblent à des instructions adressées à une IA."""
    texte_min = texte.lower()
    trouves = []
    for motif in MOTIFS_SUSPECTS:
        for correspondance in re.finditer(motif, texte_min):
            trouves.append(correspondance.group(0))
    return sorted(set(trouves))


def verifier_ancrage(cv, texte_source):
    """Contrôle d'ancrage : chaque compétence extraite doit apparaître dans le texte original.

    Détecte les compétences INVENTÉES par le LLM. Limite : une compétence réécrite sous un
    nom canonique ("ML" écrit "Machine Learning") peut déclencher une fausse alerte.
    """
    source = normaliser(texte_source)
    toutes = list(cv.competences) + [c for e in cv.experiences for c in e.competences_demontrees]
    return [c for c in toutes if normaliser(c) not in source]