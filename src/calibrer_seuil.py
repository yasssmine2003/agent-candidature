"""
Calibrer le seuil de similarité sur des exemples dont on connaît la bonne réponse.

Un score n'a pas de valeur absolue (leçon de l'étape 0) : on ne devine pas le seuil,
on le mesure. Le bon seuil sépare les paires qui DOIVENT correspondre de celles
qui NE DOIVENT PAS correspondre.

Lancement, depuis la racine de agent-candidature :
    python src/calibrer_seuil.py
"""

from embeddings import encoder
from outils import developper

# (compétence de l'offre, compétence du CV, doivent-elles correspondre ?)
PAIRES = [
    ("ML", "Machine Learning", True),
    ("Machine Learning", "apprentissage automatique", True),
    ("NLP", "traitement du langage naturel", True),
    ("Deep Learning", "apprentissage profond", True),
    ("IA", "intelligence artificielle", True),
    ("Bases de données", "SQL", False),   # proches, mais pas la même compétence
    ("Java", "JavaScript", False),
    ("Python", "Excel", False),
    ("ML", "comptabilité", False),
    ("Docker", "Kubernetes", False),
]


def score(a: str, b: str) -> float:
    va, vb = encoder([a, b])
    return float(va @ vb)


def main() -> None:
    print(f"{'Offre':<18}{'CV':<30}{'attendu':<10}{'brut':>7}{'développé':>11}")
    print("-" * 76)
    positifs, negatifs = [], []
    for a, b, attendu in PAIRES:
        brut = score(a, b)
        dev = score(developper(a), developper(b))
        (positifs if attendu else negatifs).append(dev)
        print(f"{a:<18}{b:<30}{'oui' if attendu else 'non':<10}{brut:>7.3f}{dev:>11.3f}")

    plus_bas_positif, plus_haut_negatif = min(positifs), max(negatifs)
    print(f"\nPlus petit score qui DOIT correspondre    : {plus_bas_positif:.3f}")
    print(f"Plus grand score qui NE DOIT PAS correspondre : {plus_haut_negatif:.3f}")
    if plus_bas_positif > plus_haut_negatif:
        seuil = round((plus_bas_positif + plus_haut_negatif) / 2, 2)
        print(f"Séparation possible : seuil conseillé = {seuil} (au milieu de l'écart)")
    else:
        print("Pas de séparation nette : aucun seuil ne classe tout correctement.")
        print("Regarde quelles paires se chevauchent, et ajoute un acronyme ou accepte un compromis.")


if __name__ == "__main__":
    main()