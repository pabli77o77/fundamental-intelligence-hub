import os
import logging
import yt_dlp
from typing import Optional

logger = logging.getLogger(__name__)

class YouTubeDownloader:
    """
    Wrapper de yt-dlp para descarga optimizada de audio de videos de analistas.
    """
    
    def __init__(self, output_path: str = "downloads"):
        self.output_path = output_path
        os.makedirs(output_path, exist_ok=True)
        
    def download_audio(self, video_url: str) -> Optional[str]:
        """
        Descarga el audio de un video en formato MP3.
        
        Args:
            video_url: URL del video de YouTube.
            
        Returns:
            Ruta absoluta al archivo descargado o None si falla.
        """
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '128',
            }],
            'outtmpl': f'{self.output_path}/%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                file_path = os.path.join(self.output_path, f"{info['id']}.mp3")
                
                if os.path.exists(file_path):
                    logger.info(f"Audio descargado con éxito: {file_path}")
                    return file_path
                return None
                
        except Exception as e:
            logger.error(f"Error al descargar audio de {video_url}: {e}")
            return None

    @staticmethod
    def get_video_id(url: str) -> str:
        """Extrae el ID del video de una URL de YouTube."""
        if "v=" in url:
            return url.split("v=")[1].split("&")[0]
        elif "be/" in url:
            return url.split("be/")[1].split("?")[0]
        return url
