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
    competences: list[str]
    experiences: list[Experience]
