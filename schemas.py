from enum import StrEnum
from pydantic import BaseModel, ConfigDict, Field

class CriticalityLevel(StrEnum):
    LOW = "baja"
    MEDIUM = "media"
    HIGH = "alta"

"""Contrato de salida para validar la extracción."""
class TechnicalExtraction(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_by_name=True,
        serialize_by_alias=True,
    )
    technologies: list[str] = Field(
        alias="tecnologias",
        description="Tecnologías mencionadas en el texto. Usá [] si no se menciona ninguna.",
    )
    criticality: CriticalityLevel = Field(
        alias="nivel_de_criticidad",
        description="Criticidad del incidente: baja, media o alta.",
    )
    technical_summary: str = Field(
        alias="resumen_tecnico",
        min_length=1,
        description="Resumen técnico en una frase en castellano.",
    )
