"""Point d'entrée de l'étape 2 : extraire le CV et l'offre, puis afficher les objets validés."""
from pathlib import Path

from extraction import extraire_cv, extraire_offre

DOSSIER_DATA = Path(__file__).parent.parent / "data"

texte_cv = (DOSSIER_DATA / "cv_exemple.txt").read_text(encoding="utf-8")
texte_offre = (DOSSIER_DATA / "offre_exemple.txt").read_text(encoding="utf-8")

cv = extraire_cv(texte_cv)
offre = extraire_offre(texte_offre)

print("=== CV ===")
print(cv.model_dump_json(indent=2))
print("\n=== OFFRE ===")
print(offre.model_dump_json(indent=2))