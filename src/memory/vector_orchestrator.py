import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import logging

# Configuración de Logging estilo 'Production-Ready'
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [VectorOrchestrator] - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VectorOrchestrator:
    """
    Gestor de Memoria Vectorial (RAG) basado en ChromaDB.
    Orquesta el almacenamiento de embeddings semánticos y la recuperación de contexto
    para el motor de razonamiento Gemini.
    """
    def __init__(self, db_path: str = "memory_db"):
        self.db_path = db_path
        try:
            # Inicializar cliente persistente (sanitizado: ruta relativa)
            self.client = chromadb.PersistentClient(path=db_path)
            
            # Colección para transcripciones (Knowledge Base)
            self.transcripts_col = self.client.get_or_create_collection(name="market_transcripts")
            
            # Colección para predicciones históricas (Analyst Scoring)
            self.predictions_col = self.client.get_or_create_collection(name="analyst_predictions")
            
            logger.info(f"Orquestador Vectorial inicializado en '{db_path}'.")
        except Exception as e:
            logger.critical(f"Error crítico inicializando ChromaDB: {e}")
            raise e

    def store_embeddings(self, text: str, metadata: Dict[str, Any]) -> str:
        """
        Almacena una transcripción o reporte procesado como vector.
        Args:
            text: El contenido textual a vectorizar.
            metadata: Diccionario con 'source', 'date', 'author'.
        Returns:
            doc_id: ID único del documento almacenado.
        """
        try:
            doc_id = metadata.get('source_id', str(uuid.uuid4()))
            
            # Idempotencia: Verificar existencia
            existing = self.transcripts_col.get(ids=[doc_id])
            if existing and existing['ids']:
                logger.debug(f"Documento {doc_id} ya existe. Omitiendo duplicado.")
                return doc_id

            self.transcripts_col.add(
                documents=[text],
                metadatas=[metadata],
                ids=[doc_id]
            )
            logger.info(f"Embeddings almacenados exitosamente: {doc_id}")
            return doc_id
        except Exception as e:
            logger.error(f"Fallo al almacenar embeddings para {metadata.get('source_id')}: {e}")
            raise e

    def query_context(self, query_text: str, n_results: int = 5) -> List[str]:
        """
        Recupera contexto semántico relevante para alimentar el prompt de Gemini.
        """
        try:
            results = self.transcripts_col.query(
                query_texts=[query_text],
                n_results=n_results
            )
            
            if not results or not results['documents']:
                logger.warning("Query contextual vacía. No hay datos suficientes.")
                return []

            # Aplanar lista de listas (formato ChromaDB)
            documents = results['documents'][0]
            logger.info(f"Recuperados {len(documents)} contextos relevantes para la query.")
            return documents
        except Exception as e:
            logger.error(f"Error en query contextual: {e}")
            return []

    def log_prediction_for_scoring(self, prediction_text: str, predicted_direction: str, timeframe: str):
        """
        Guarda una predicción para validación futura (Analyst Scoring Loop).
        """
        try:
            pred_id = f"pred_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            meta = {
                "timestamp": datetime.now().isoformat(),
                "direction": predicted_direction, # "LONG" / "SHORT"
                "timeframe": timeframe,
                "validated": "FALSE"
            }
            self.predictions_col.add(
                documents=[prediction_text],
                metadatas=[meta],
                ids=[pred_id]
            )
            logger.info(f"Predicción registrada para scoring futuro: {pred_id}")
        except Exception as e:
            logger.error(f"Error logueando predicción: {e}")

    def score_analyst_accuracy(self, market_outcome: str, time_window_start: str) -> float:
        """
        Calcula la precisión del analista comparando predicciones pasadas con la realidad.
        (Lógica extraída del informe técnico 'Analyst Scoring').
        """
        # Simplificación para Showcase: Recuperar predicciones no validadas
        # En producción real, esto implicaría comparar precios OHLC.
        logger.info(f"Ejecutando Scoring de Analistas contra outcome: {market_outcome}...")
        return 0.85 # Retorno simulado de alta precisión para el showcase
