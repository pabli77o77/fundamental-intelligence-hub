import logging
from logging.handlers import RotatingFileHandler
import os
import sys

def setup_logger(name: str, log_file: str = "bot.log", level=logging.INFO) -> logging.Logger:
    """
    Configura un logger centralizado con rotación de archivos.
    
    Características:
    - RotatingFileHandler de 5MB con 3 backups.
    - StreamHandler para salida inmediata en consola.
    - Prevención de duplicación de handlers en imports múltiples.
    """
    logger = logging.getLogger(name)
    
    # Si el logger ya tiene handlers configurados, no los duplicamos
    if logger.hasHandlers():
        return logger
        
    logger.setLevel(level)
    
    # Directorio de logs
    log_dir = os.path.dirname(os.path.abspath(log_file))
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    # Formato de logs
    formatter = logging.Formatter('%(asctime)s [%(name)s] %(levelname)s - %(message)s')

    # Handler para archivo con rotación (5MB)
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=5*1024*1024, 
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
