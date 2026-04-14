import logging
import os
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MemoryManager:
    """
    Interfaz de persistencia para el Vector Store (ChromaDB).
    Almacena transcripciones y resúmenes diarios para recuperación semántica (RAG).
    """
    
    def __init__(self, db_path: str = "memory_db"):
        self.db_path = db_path
        os.makedirs(db_path, exist_ok=True)
        
        # Inicializar cliente persistente
        self.client = chromadb.PersistentClient(path=db_path)
        
        # Colección para transcripciones (audio -> texto)
        self.transcripts = self.client.get_or_create_collection(
            name="transcripts",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Colección para resúmenes de análisis diarios
        self.daily_summaries = self.client.get_or_create_collection(
            name="daily_summaries",
            metadata={"hnsw:space": "cosine"}
        )
        
    def save_transcript(self, text: str, metadata: Dict) -> None:
        """
        Guarda una nueva transcripción. Evita duplicados mediante el video_id.
        """
        video_id = metadata.get("video_id")
        if not video_id:
            logger.error("No se puede guardar transcripción sin video_id.")
            return
            
        # Verificar si ya existe el ID
        existing = self.transcripts.get(ids=[video_id])
        if existing and existing['ids']:
            logger.info(f"La transcripción {video_id} ya existe. Saltando...")
            return
            
        try:
            self.transcripts.add(
                documents=[text],
                metadatas=[metadata],
                ids=[video_id]
            )
            logger.info(f"Transcripción {video_id} guardada en ChromaDB.")
        except Exception as e:
            logger.error(f"Error al guardar en ChromaDB: {e}")

    def save_daily_summary(self, summary_text: str, date_str: str) -> None:
        """
        Guarda o actualiza el resumen consolidado de un día específico.
        """
        try:
            self.daily_summaries.upsert(
                documents=[summary_text],
                metadatas=[{"date": date_str}],
                ids=[date_str]
            )
            logger.info(f"Resumen diario del {date_str} actualizado.")
        except Exception as e:
            logger.error(f"Error al guardar resumen diario: {e}")

    def get_recent_context(self, n_days: int = 3) -> str:
        """
        Recupera los resúmenes de los últimos N días para dar contexto al LLM.
        """
        context_parts = []
        today = datetime.now()
        
        for i in range(n_days):
            target_date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            result = self.daily_summaries.get(ids=[target_date])
            
            if result and result['documents']:
                date_label = f"--- RESUMEN DEL {target_date} ---"
                context_parts.append(f"{date_label}\n{result['documents'][0]}")
                
        if not context_parts:
            return "No hay contexto histórico disponible para los últimos días."
            
        return "\n\n".join(context_parts)
