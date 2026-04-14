import logging
import os
import requests
import json
import re
from typing import Dict, List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from src.utils.http_utils import request_with_retry

logger = logging.getLogger(__name__)

class FundamentalAnalyzer:
    """
    Cerebro cognitivo del Hub. Orquesta la interacción con Gemini 2.5 Flash
    vía REST API para generar reportes estructurados y predicciones auditables.
    """
    
    API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    
    def __init__(self, config: Dict):
        """
        Args:
            config: Diccionario con claves 'gemini_api_key' y 'model_params'.
        """
        self.api_key = config.get("gemini_api_key")
        if not self.api_key:
            logger.error("No se encontró GEMINI_API_KEY en la configuración.")
            
        self.model_params = config.get("model_params", {
            "temperature": 0.2,
            "topP": 0.8,
            "maxOutputTokens": 2048
        })

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=15, max=120),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    def _generate_content_rest(self, prompt: str) -> str:
        """
        Llama a la API de Gemini mediante POST con headers personalizados.
        La API key se envía en 'x-goog-api-key' por seguridad (no en la URL).
        """
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": self.model_params
        }
        
        try:
            response = requests.post(self.API_URL, headers=headers, json=payload, timeout=120)
            response.raise_for_status()
            
            data = response.json()
            # Extraer el texto de la respuesta de Gemini
            return data['candidates'][0]['content']['parts'][0]['text']
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code in [429, 500, 503]:
                logger.warning(f"Error temporal en Gemini ({e.response.status_code}). Reintentando...")
                raise
            logger.error(f"Error fatal de API en Gemini: {e}")
            raise

    def analyze_market_data(
        self, 
        transcripts: str, 
        news: List[Dict], 
        macro: str, 
        context: str, 
        scores: Dict
    ) -> Dict:
        """
        Consolida todas las fuentes y genera el análisis final.
        """
        prompt = self._build_prompt(transcripts, news, macro, context, scores)
        
        logger.info("Enviando datos a Gemini para análisis fundamental...")
        raw_response = self._generate_content_rest(prompt)
        
        return self._parse_structured_response(raw_response)

    def _build_prompt(self, transcripts, news, macro, context, scores) -> str:
        """Construye el mega-prompt (Sanitizado para showcase)."""
        return f"""
        Actúa como un experto Analista de Mercados Financieros (Macro & Crypto).
        Analiza las siguientes fuentes heterogéneas y genera un dictamen propio.

        [CONTEXTO HISTÓRICO - ÚLTIMOS 3 DÍAS]
        {context}

        [TRANSCRIPCIONES DE ANALISTAS (MENTORES)]
        {transcripts}

        [SCORES DE CREDIBILIDAD DE MENTORES]
        {json.dumps(scores, indent=2)}

        [NOTICIAS RECIENTES]
        {json.dumps(news, indent=2)}

        [CALENDARIO MACROECONÓMICO]
        {macro}

        REQUERIMIENTOS:
        1. Detecta contradicciones entre los analistas actuales y sus opiniones históricas.
        2. Prioriza analistas con mayor credibilidad (Trust Score).
        3. Identifica eventos macro que invaliden el análisis técnico.
        
        OUTPUT ESPERADO:
        Genera un reporte en Markdown que incluya:
        - Resumen Ejecutivo (obligatorio)
        - Sentimiento del Mercado (0-100)
        - Análisis de Contradicciones
        - Al final, incluye un bloque JSON válido con este formato:
        {{
            "market_sentiment": 65,
            "bias": "BULLISH",
            "predictions": [
                {{"mentor": "Nombre", "asset": "BTC", "direction": "UP", "target_price": 72000, "timeframe": "4h"}}
            ]
        }}
        """

    def _parse_structured_response(self, response_text: str) -> Dict:
        """
        Extrae el JSON y el resumen ejecutivo de la respuesta de Gemini.
        """
        result = {
            "full_report": response_text,
            "executive_summary": self._extract_executive_summary(response_text),
            "structured_data": {}
        }
        
        # Intentar extraer bloque JSON con regex
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                result["structured_data"] = json.loads(json_match.group())
            except:
                logger.error("Error al parsear el JSON extraído de la respuesta.")
                
        return result

    def _extract_executive_summary(self, markdown: str) -> str:
        """Extrae la sección Resumen Ejecutivo usando regex."""
        match = re.search(r'#+\s*Resumen Ejecutivo(.*?)(?=#|\Z)', markdown, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return "Resumen ejecutivo no encontrado."
