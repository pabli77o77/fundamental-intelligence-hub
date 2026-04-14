import logging
import os
from datetime import datetime
from typing import List, Dict, Optional
from src.utils.file_manager import FileManager

logger = logging.getLogger(__name__)

class PredictionTracker:
    """
    Persistencia y gestión de predicciones extraídas por el analizador.
    Controla el ciclo de vida de cada predicción: PENDING -> SUCCESS/FAILED.
    """
    
    FILE_PATH = "outputs/predictions.json"
    
    def __init__(self, storage_path: str = "outputs"):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
        self.file_path = os.path.join(storage_path, "predictions.json")

    def load_predictions(self) -> List[Dict]:
        """Carga las predicciones desde el almacenamiento JSON."""
        data = FileManager.load_json(self.file_path)
        if data is None:
            return []
        return data

    def save_new_predictions(self, predictions: List[Dict]) -> None:
        """
        Agrega nuevas predicciones provenientes de Gemini.
        """
        if not predictions:
            return
            
        current = self.load_predictions()
        timestamp = datetime.now().isoformat()
        
        new_entries = []
        for pred in predictions:
            new_entries.append({
                "mentor": pred.get("mentor", "Unknown"),
                "asset": pred.get("asset", "BTC"),
                "direction": pred.get("direction", "NEUTRAL"),
                "target_price": pred.get("target_price"),
                "timeframe": pred.get("timeframe", "1h"),
                "date_added": timestamp,
                "status": "PENDING",
                "verified_at": None,
                "final_price": None
            })
            
        current.extend(new_entries)
        self._save_all_predictions(current)
        logger.info(f"Se registraron {len(new_entries)} nuevas predicciones.")

    def _save_all_predictions(self, predictions: List[Dict]) -> None:
        """Escritura atómica de la lista completa de predicciones."""
        FileManager.save_json(predictions, self.file_path)

    def get_mentor_scores(self) -> Dict[str, Dict]:
        """
        Calcula estadísticas básicas de acierto para cada analista (mentor).
        """
        all_preds = self.load_predictions()
        scores = {}
        
        for pred in all_preds:
            mentor = pred["mentor"]
            if mentor not in scores:
                scores[mentor] = {"success": 0, "failed": 0, "total": 0, "accuracy": 0.0}
            
            if pred["status"] != "PENDING":
                scores[mentor]["total"] += 1
                if pred["status"] == "SUCCESS":
                    scores[mentor]["success"] += 1
                else:
                    scores[mentor]["failed"] += 1
                    
        # Calcular porcentaje
        for m in scores:
            if scores[m]["total"] > 0:
                scores[m]["accuracy"] = round(scores[m]["success"] / scores[m]["total"] * 100, 2)
                
        return scores
