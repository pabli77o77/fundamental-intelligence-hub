import requests
import time
import logging
from typing import Optional
from requests.exceptions import RequestException, Timeout, ConnectionError

logger = logging.getLogger(__name__)

def request_with_retry(
    url: str, 
    method: str = "GET", 
    timeout: int = 10, 
    max_retries: int = 3,
    **kwargs
) -> requests.Response:
    """
    Realiza una petición HTTP con reintentos y backoff exponencial.
    
    No reintenta errores 4xx (excepto 429) ya que generalmente indican errores
    del cliente que no se solucionarán repitiendo la petición.
    
    Args:
        url: URL a la que realizar la petición.
        method: Método HTTP (default: GET).
        timeout: Tiempo de espera en segundos.
        max_retries: Número máximo de reintentos.
        **kwargs: Argumentos adicionales para requests.request.
        
    Returns:
        Response objeto de la librería requests.
        
    Raises:
        RequestException: Si se agotan los reintentos o hay un error fatal.
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            response = requests.request(method, url, timeout=timeout, **kwargs)
            
            # Si es 429 (Too Many Requests) o 5xx (Server Error), reintentamos
            if response.status_code == 429 or 500 <= response.status_code < 600:
                if attempt < max_retries:
                    wait_time = 2 ** attempt # Backoff exponencial: 1s, 2s, 4s...
                    logger.warning(
                        f"Petición fallida ({response.status_code}) en {url}. "
                        f"Reintentando {attempt + 1}/{max_retries} en {wait_time}s..."
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    return response
            
            # No reintentamos otros 4xx (400, 401, 403, 404, etc.)
            return response
            
        except (Timeout, ConnectionError) as e:
            last_exception = e
            if attempt < max_retries:
                wait_time = 2 ** attempt
                logger.warning(
                    f"Error de red ({type(e).__name__}) en {url}. "
                    f"Reintentando {attempt + 1}/{max_retries} en {wait_time}s..."
                )
                time.sleep(wait_time)
            else:
                logger.error(f"Se agotaron los reintentos para {url}. Error: {e}")
                raise
        except RequestException as e:
            logger.error(f"Error fatal en petición a {url}: {e}")
            raise

    if last_exception:
        raise last_exception
    
    # Esto no debería alcanzarse
    raise RequestException("Error desconocido en request_with_retry")
