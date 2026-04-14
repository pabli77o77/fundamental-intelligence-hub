import json
import os
import logging
from typing import Any, Optional, Union

logger = logging.getLogger(__name__)

class FileManager:
    """
    Gestor de archivos con soporte para escrituras atómicas.
    """
    
    @staticmethod
    def save_json(data: Union[dict, list], path: str) -> None:
        """
        Guarda datos en un archivo JSON de forma atómica.
        
        Patrón: Escribir en archivo temporal (.tmp) y renombrar mediante os.replace().
        Esto garantiza que un fallo durante la escritura (ej. corte de energía) no
        corrompa el archivo original, ya que el renombrado es una operación atómica
        en sistemas operativos modernos.
        """
        temp_path = f"{path}.tmp"
        try:
            # Aseguramos que el directorio existe
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            
            # Operación atómica de reemplazo
            os.replace(temp_path, path)
            
        except Exception as e:
            logger.error(f"Error al guardar JSON en {path}: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise

    @staticmethod
    def load_json(path: str) -> Optional[Union[dict, list]]:
        """
        Carga datos de un archivo JSON con manejo de errores.
        
        Retorna None si el archivo no existe o está corrupto, evitando
        propagar excepciones innecesarias en el pipeline.
        """
        if not os.path.exists(path):
            return None
            
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Error al parsear JSON corrupto en {path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado al leer JSON en {path}: {e}")
            return None
