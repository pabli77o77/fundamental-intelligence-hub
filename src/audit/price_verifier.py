import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from utils.http_utils import request_with_retry
from utils.file_manager import FileManager

logger = logging.getLogger(__name__)

class PriceVerifier:
    """
    Auditor financiero encargado de verificar predicciones vs mercado real.
    
    Consulta la API de Binance para obtener precios actuales y compararlos
    con las predicciones almacenadas. Mantiene un historial limitado para
    prevenir el crecimiento indefinido del log de predicciones.
    """
    
    _MAX_RESOLVED = 500
    _BINANCE_API_URL = "https://api.binance.com/api/v3/ticker/price"
    
    def __init__(self, tracker):
        self.tracker = tracker
        
    def verify_pending_predictions(self) -> None:
        """
        Proceso principal de auditoría:
        1. Carga predicciones PENDING.
        2. Verifica si el timeframe ha vencido.
        3. Consulta precio real en Binance.
        4. Marca SUCCESS o FAILED.
        5. Poda el historial resuelto a las últimas 500 entradas.
        """
        all_predictions = self.tracker.load_predictions()
        if not all_predictions:
            logger.info("No hay predicciones para verificar.")
            return
            
        updated = []
        pending_count = 0
        resolved_this_cycle = 0
        
        for pred in all_predictions:
            if pred.get("status") != "PENDING":
                updated.append(pred)
                continue
                
            # Verificar si ha pasado el tiempo suficiente (ej. 24h, 1w)
            if not self._is_timeframe_expired(pred):
                updated.append(pred)
                pending_count += 1
                continue
                
            # Consultar precio actual
            current_price = self._get_current_price(pred["asset"])
            if current_price is None:
                updated.append(pred) # Mantener como pending si falla la API
                continue
                
            # Evaluar acierto
            success = self._is_prediction_correct(pred, current_price)
            pred["status"] = "SUCCESS" if success else "FAILED"
            pred["verified_at"] = datetime.now().isoformat()
            pred["final_price"] = current_price
            
            updated.append(pred)
            resolved_this_cycle += 1
            
        # Poda de historial resuelto (Pilar 6 - Resilience)
        pending = [p for p in updated if p["status"] == "PENDING"]
        resolved = [p for p in updated if p["status"] != "PENDING"]
        
        final_list = pending + resolved[-self._MAX_RESOLVED:]
        self.tracker._save_all_predictions(final_list)
        
        logger.info(f"Auditoría completada: {resolved_this_cycle} resueltas, {pending_count} aún pendientes.")

    def _get_current_price(self, asset: str) -> Optional[float]:
        """Consulta precio actual en Binance via REST."""
        symbol = f"{asset.upper()}USDT"
        params = {"symbol": symbol}
        try:
            resp = request_with_retry(self._BINANCE_API_URL, params=params)
            data = resp.json()
            return float(data["price"])
        except Exception as e:
            logger.error(f"Error consultando precio de {symbol} en Binance: {e}")
            return None

    def _is_prediction_correct(self, pred: dict, current_price: float) -> bool:
        """Lógica de validación de dirección y precio objetivo."""
        direction = pred["direction"].upper()
        entry_price = pred.get("entry_price", 0.0) # Podría no existir en versiones simplificadas
        
        if direction == "UP":
            return current_price > entry_price
        elif direction == "DOWN":
            return current_price < entry_price
        return False

    def _is_timeframe_expired(self, pred: dict) -> bool:
        """Determina si una predicción ya debe ser auditada basándose en su timeframe."""
        added_date = datetime.fromisoformat(pred["date_added"])
        tf = pred["timeframe"].lower()
        
        now = datetime.now()
        if "24h" in tf:
            return now > added_date + timedelta(hours=24)
        elif "1w" in tf:
            return now > added_date + timedelta(weeks=1)
        elif "1m" in tf:
            return now > added_date + timedelta(days=30)
            
        return now > added_date + timedelta(hours=24) # Default 24h
