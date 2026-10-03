"""Schémas Pydantic : la forme exacte des données échangées avec le LLM."""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

# Même règle pour le CV et pour l'offre : deux listes comparées doivent être extraites pareil.
NOM_CANONIQUE = (
    "Chaque compétence est écrite sous sa forme la plus courte et la plus courante "
    "(exemples : 'RAG', 'LLM', 'Docker', 'Machine Learning'), sans mots comme 'connaissance de'."
)


class Experience(BaseModel):
    model_config = ConfigDict(extra="forbid")  # refuse les champs non prévus

    poste: str
    entreprise: Optional[str] = Field(description="Nom de l'entreprise, null si absent")
    date_debut: str = Field(description="Format AAAA-MM")
    date_fin: Optional[str] = Field(description="Format AAAA-MM, null si le poste est en cours")
    competences_demontrees: list[str] = Field(
        description=(
            "Compétences techniques EXPLICITEMENT mentionnées dans la description de cette expérience. "
            "Ne rien déduire : une compétence absente du texte n'est pas listée. Liste vide si aucune. "
            + NOM_CANONIQUE
        )
    )


class CV(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nom: Optional[str]
    competences: list[str] = Field(
        description=(
            "Compétences techniques listées dans la section compétences du CV, "
            "sans les qualités personnelles. " + NOM_CANONIQUE
        )
    )
    experiences: list[Experience]


class OffreStage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titre: str
    entreprise: Optional[str] = Field(description="Nom de l'entreprise, null si absent")
    competences_requises: list[str] = Field(
        description=(
            "Compétences techniques explicitement demandées, sans les qualités personnelles. "
            + NOM_CANONIQUE
        )
    )
    experience_min_mois: Optional[int] = Field(
        description="Expérience minimale demandée, convertie en mois (1 an = 12). Null si non précisée."
    )