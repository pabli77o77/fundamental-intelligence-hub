import asyncio
import logging
import time
from typing import Dict, Any
from pipeline.full_cycle import FullCycle
from ingestion.news_fetcher import NewsFetcher

logger = logging.getLogger(__name__)

class ContinuousEngine:
    """
    Orquestador asíncrono de dos velocidades (Dual Cycle).
    
    1. Full Cycle Loop (30 min): Análisis cognitivo profundo.
    2. Fast Path Loop (5 min): Detección de noticias críticas (Breaking News).
    
    Ambos operan en paralelo sin bloquearse mutuamente.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.full_cycle = FullCycle(config)
        self.news_fetcher = NewsFetcher()
        self.is_running = False

    async def start(self) -> None:
        """Inicia los loops de ejecución continua."""
        self.is_running = True
        logger.info("🚀 Motor Continuo de Inteligencia Iniciado.")
        
        # Ejecutar ambos ciclos en paralelo
        await asyncio.gather(
            self._full_cycle_loop(),
            self._fast_path_loop()
        )

    async def _full_cycle_loop(self) -> None:
        """Ciclo completo cada 30 min (~1800s)."""
        interval = self.config.get("intervals", {}).get("full_cycle_sec", 1800)
        
        while self.is_running:
            try:
                start_time = time.time()
                await self.full_cycle.run()
                
                # Calcular tiempo de espera para el siguiente ciclo
                elapsed = time.time() - start_time
                wait_time = max(0, interval - elapsed)
                
                logger.info(f"Full Cycle finalizado. Próximo en {wait_time/60:.1f} min.")
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                logger.error(f"Error en Full Cycle Loop: {e}")
                await asyncio.sleep(60) # Esperar un minuto antes de reintentar

    async def _fast_path_loop(self) -> None:
        """Ciclo rápido cada 5 min (~300s)."""
        interval = self.config.get("intervals", {}).get("fast_path_sec", 300)
        
        while self.is_running:
            try:
                start_time = time.time()
                logger.info("⚡ Fast Path: Escaneando noticias de alta frecuencia...")
                
                # Solo noticias para detección de urgencia
                news_items = await asyncio.to_thread(self.news_fetcher.fetch_all_news)
                if news_items:
                    # Persistencia simplificada para el dashboard/control plane
                    logger.info(f"Fast Path: {len(news_items)} noticias capturadas.")
                    
                # Calcular tiempo de espera
                elapsed = time.time() - start_time
                wait_time = max(0, interval - elapsed)
                
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                logger.error(f"Error en Fast Path Loop: {e}")
                await asyncio.sleep(30)
