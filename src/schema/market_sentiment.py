from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

# --- PORTFOLIO SHOWCASE VERSION ---
# Este archivo define el 'Data Contract' central que permite que el sistema de 
# Inteligencia Fundamental se comunique con motores de ejecución externos.

class SentimentPayload(BaseModel):
    """
    Schema estricto para el envío de señales de sentimiento macro.
    Diseñado para integraciones desacopladas (Decoupled Architecture).
    """
    symbol: str = Field(..., description="Símbolo del activo (ej: BTC-USDT)")
    sentiment_score: float = Field(
        ..., 
        ge=-1.0, 
        le=1.0, 
        description="Puntaje normalizado: -1 (Extremadamente Bearish) a 1 (Extremadamente Bullish)"
    )
    confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Nivel de confianza del análisis de IA (0 a 1)"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, 
        description="Momento exacto en que se generó la señal"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "BTC-USDT",
                "sentiment_score": 0.75,
                "confidence": 0.92,
                "timestamp": "2026-02-04T12:00:00"
            }
        }
