from pydantic import BaseModel, Field, field_validator
from typing import List
from datetime import datetime
import json

class MarketSentimentPayload(BaseModel):
    """
    CONTRATO DE DATOS (DATA CONTRACT) - REPO: fundamental-intelligence-hub
    Define el esquema estricto de salida del análisis de inteligencia fundamental.
    """
    timestamp: datetime = Field(default_factory=datetime.now)
    overall_sentiment: float = Field(
        ..., 
        ge=-1.0, 
        le=1.0, 
        description="Puntaje de sentimiento normalizado entre -1 (Bearish) y 1 (Bullish)"
    )
    confidence_score: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Nivel de confianza del análisis basado en la calidad de las fuentes"
    )
    top_impact_news: List[str] = Field(
        ..., 
        min_length=1, 
        description="Lista de los eventos/noticias más influyentes detectados"
    )

    @field_validator('overall_sentiment')
    @classmethod
    def validate_sentiment(cls, v: float) -> float:
        # Ejemplo de validación personalizada: Asegurar que no sea exactamente 0 para evitar parálisis
        if v == 0:
            return 0.001
        return v

    def to_json(self) -> str:
        return self.model_dump_json()

    class Config:
        json_schema_extra = {
            "example": {
                "overall_sentiment": 0.85,
                "confidence_score": 0.92,
                "top_impact_news": ["FED maintains rates", "BTC ETF Inflows surge"]
            }
        }
