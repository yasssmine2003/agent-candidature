"""Schémas Pydantic : la forme exacte des données échangées avec le LLM."""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Experience(BaseModel):
    model_config = ConfigDict(extra="forbid")  # refuse les champs non prévus

    poste: str
    entreprise: Optional[str] = Field(description="Nom de l'entreprise, null si absent")
    date_debut: str = Field(description="Format AAAA-MM")
    date_fin: Optional[str] = Field(description="Format AAAA-MM, null si le poste est en cours")


class CV(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nom: Optional[str]
    competences: list[str] = Field(
        description="Compétences techniques uniquement, sans les qualités personnelles"
    )
    experiences: list[Experience]


class OffreStage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titre: str
    entreprise: Optional[str] = Field(description="Nom de l'entreprise, null si absent")
    competences_requises: list[str] = Field(
        description="Compétences techniques explicitement demandées, sans les qualités personnelles"
    )
    experience_min_mois: Optional[int] = Field(
        description="Expérience minimale demandée, convertie en mois (1 an = 12). Null si non précisée."
    )