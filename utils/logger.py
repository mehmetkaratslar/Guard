# guard_pc_app/utils/logger.py
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
import datetime

def setup_logger(log_level=logging.INFO):
    """Günlük kaydı sistemini ayarlar.
    
    Args:
        log_level (int, optional): Günlük kaydı seviyesi
    """
    # Logs klasörünü oluştur
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Tarih tabanlı log dosyası adı
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(logs_dir, f"guard_{today}.log")
    
    # Kök logger yapılandırması
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Mevcut handlers temizle
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Konsol handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_format = logging.Formatter("[%(levelname)s] %(message)s")
    console_handler.setFormatter(console_format)
    
    # Dosya handler (dönen log dosyaları)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5
    )
    file_handler.setLevel(log_level)
    file_format = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_format)
    
    # Handlers ekle
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    logging.info(f"Logger başlatıldı - Seviye: {logging.getLevelName(log_level)}")