from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class OpenWeatherConfig(BaseModel):
    language: str = Field(
        ...,
        title="Idioma",
        examples=["pt_br"],
        json_schema_extra={"placeholder": "pt_br", "help_text": "Valores permitidos: pt_br ou en_us."}
    )
    city: str = Field(
        ...,
        title="Cidade",
        json_schema_extra={"placeholder": "São Paulo", "help_text": "Nome da cidade para buscar o clima."}
    )

    @field_validator("language", mode="after")
    @classmethod
    def validate_language(cls, v):
        allowed = ["pt_br", "en_us"]
        if v not in allowed:
            raise ValueError(f"Idioma inválido: {v}")
        return v


class NormalizedDataSchema(BaseModel):
    temperature: Optional[float]
    humidity: Optional[int]
    weather: Optional[str]
    city: Optional[str]
    country: Optional[str]
    timestamp: Optional[datetime]
