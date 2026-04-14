import logging
from typing import List, Dict, Optional
from datetime import datetime
import requests
# Usamos defusedxml para protección contra ataques XXE (XML External Entity)
from defusedxml import ElementTree as ET
from src.utils.http_utils import request_with_retry

logger = logging.getLogger(__name__)

class MacroFetcher:
    """
    Ingesta y parseo seguro del calendario macroeconómico de ForexFactory.
    """
    
    URL = "https://www.forexfactory.com/ffcal_week_this.xml"
    
    def fetch_high_impact_events(self) -> List[Dict]:
        """
        Descarga el calendario XML semanal de ForexFactory y extrae eventos
        de impacto alto (Impact: High) y medio para divisas clave.
        """
        try:
            response = request_with_retry(self.URL)
            root = ET.fromstring(response.content)
            
            events = []
            today = datetime.now().strftime("%m-%d-%Y")
            
            for event in root.findall('event'):
                title = event.find('title').text
                country = event.find('country').text
                date = event.find('date').text
                time = event.find('time').text
                impact = event.find('impact').text
                
                # Filtrar solo eventos de alto impacto para USD (o EUR si se prefiere)
                if country == "USD" and impact in ["High", "Medium"]:
                    events.append({
                        "title": title,
                        "country": country,
                        "date": date,
                        "time": time,
                        "impact": impact,
                        "is_today": date == today
                    })
            
            logger.info(f"Se recuperaron {len(events)} eventos macro de alto impacto.")
            return events
            
        except Exception as e:
            logger.error(f"Error al obtener calendario macroeconómico: {e}")
            return []

    def format_macro_for_prompt(self, events: List[Dict]) -> str:
        """
        Formatea los eventos macroeconómicos para ser incluidos en el
        prompt del FundamentalAnalyzer (Gemini).
        """
        if not events:
            return "No se detectaron eventos macroeconómicos relevantes esta semana."
            
        lines = ["--- CALENDARIO MACROECONÓMICO (USD) ---"]
        for ev in events:
            prefix = "🚨 [HOY]" if ev["is_today"] else f"📅 [{ev['date']}]"
            lines.append(
                f"{prefix} - {ev['title']} ({ev['impact']}) - {ev['time']}"
            )
            
        return "\n".join(lines)
