import logging
import feedparser
from typing import List, Dict, Optional
from src.utils.http_utils import request_with_retry

logger = logging.getLogger(__name__)

class NewsFetcher:
    """
    Agregador de noticias que consume CryptoPanic API y feeds RSS.
    """
    
    CRYPTO_PANIC_URL = "https://cryptopanic.com/api/v1/posts/"
    RSS_FEEDS = [
        "https://cointelegraph.com/rss",
        "https://www.coindesk.com/arc/outboundfeed/rss/"
    ]
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def fetch_cryptopanic_news(self) -> List[Dict]:
        """
        Obtiene noticias recientes de CryptoPanic API v1.
        """
        if not self.api_key:
            logger.warning("No se proporcionó API Key para CryptoPanic.")
            return []
            
        params = {
            "auth_token": self.api_key,
            "public": "true",
            "filter": "important"
        }
        
        try:
            response = request_with_retry(self.CRYPTO_PANIC_URL, params=params)
            data = response.json()
            results = data.get("results", [])
            logger.info(f"Se obtuvieron {len(results)} noticias de CryptoPanic.")
            return results
        except Exception as e:
            logger.error(f"Error al obtener noticias de CryptoPanic: {e}")
            return []

    def fetch_rss_news(self) -> List[Dict]:
        """
        Obtiene entradas recientes de los feeds RSS configurados.
        """
        all_entries = []
        for feed_url in self.RSS_FEEDS:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:10]: # Solo las 10 más recientes por feed
                    all_entries.append({
                        "title": entry.title,
                        "link": entry.link,
                        "summary": entry.get("summary", ""),
                        "source": feed.feed.title if hasattr(feed, 'feed') else "RSS"
                    })
            except Exception as e:
                logger.error(f"Error al procesar feed RSS {feed_url}: {e}")
                
        logger.info(f"Se obtuvieron {len(all_entries)} noticias vía RSS.")
        return all_entries
