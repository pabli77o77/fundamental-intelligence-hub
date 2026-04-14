import asyncio
import logging
from typing import Optional, Dict, Any
from ingestion.youtube_downloader import YoutubeDownloader
from ingestion.news_fetcher import NewsFetcher
from ingestion.macro_fetcher import MacroFetcher
from analysis.fundamental_analyzer import FundamentalAnalyzer
from analysis.memory_manager import MemoryManager
from audit.prediction_tracker import PredictionTracker
from audit.price_verifier import PriceVerifier

logger = logging.getLogger(__name__)

class FullCycle:
    """
    Orquestador del pipeline completo de inteligencia (Cold Path).
    
    1. Ingesta Multi-Fuente (YouTube, RSS, Macro).
    2. Transcripción y Almacenamiento Vectorial (RAG).
    3. Recuperación de Contexto Semántico.
    4. Análisis con Gemini 2.5 Flash.
    5. Persistencia de Predicciones y Auditoría de Precios.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.downloader = YoutubeDownloader()
        self.news = NewsFetcher()
        self.macro = MacroFetcher()
        self.memory = MemoryManager()
        self.analyzer = FundamentalAnalyzer(config)
        self.tracker = PredictionTracker()
        self.verifier = PriceVerifier(self.tracker)

    async def run(self) -> bool:
        """Ejecuta un ciclo completo de análisis (~30 min)."""
        logger.info("--- Iniciando FULL CYCLE de Inteligencia ---")
        
        try:
            # 1. Auditoría Previa (Cerrar ciclo anterior)
            self.verifier.verify_pending_predictions()
            
            # 2. Ingesta (YouTube asíncrono con hilos)
            videos = await asyncio.to_thread(self.downloader.get_latest_videos_from_channels)
            transcripts = []
            for v in videos:
                txt = await asyncio.to_thread(self.downloader.download_and_transcribe, v)
                if txt:
                    transcripts.append(txt)
                    self.memory.save_transcript(txt, v) # RAG update
            
            # 3. Ingesta de Datos Rápidos
            news_items = await asyncio.to_thread(self.news.fetch_all_news)
            macro_events = await asyncio.to_thread(self.macro.fetch_high_impact_events)
            
            # 4. RAG: Recuperar contexto semántico (Contradicciones)
            historical_context = self.memory.get_recent_context(n_days=3)
            mentor_scores = self.tracker.get_all_mentor_stats()
            
            # 5. Análisis Cognitivo con Gemini 2.5 Flash
            report_data = await self.analyzer.analyze_market_data(
                transcripts=transcripts,
                news=news_items,
                macro=macro_events,
                context=historical_context,
                scores=mentor_scores
            )
            
            if report_data:
                # 6. Tracking de Nuevas Predicciones
                predictions = report_data.get("extracted_predictions", [])
                self.tracker.save_new_predictions(predictions)
                
                # 7. Persistencia de Resultados (JSONs para dashboard)
                logger.info("Ciclo de análisis finalizado con éxito.")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error fatal en FullCycle: {e}", exc_info=True)
            return False
