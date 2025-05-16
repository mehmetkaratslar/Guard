# guard_pc_app/core/camera.py
import cv2
import numpy as np
import threading
import logging
import time
from config.settings import CAMERA_INDEX, FRAME_WIDTH, FRAME_HEIGHT, FRAME_RATE

class Camera:
    """Kamera işlemlerini yöneten sınıf."""
    
    def __init__(self, camera_index=CAMERA_INDEX):
        self.camera_index = camera_index
        self.cap = None
        self.is_running = False
        self.thread = None
        self.frame = None
        self.last_frame_time = 0
        self.frame_lock = threading.Lock()
    
    def start(self):
        """Kamerayı başlatır ve kare yakalama thread'ini başlatır."""
        if self.is_running:
            logging.warning("Kamera zaten çalışıyor.")
            return False
        
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                logging.error(f"Kamera {self.camera_index} açılamadı.")
                return False
            
            # Kamera ayarlarını yap
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
            self.cap.set(cv2.CAP_PROP_FPS, FRAME_RATE)
            
            # İlk kareyi oku
            ret, frame = self.cap.read()
            if not ret:
                logging.error("İlk kare okunamadı.")
                self.cap.release()
                return False
            
            with self.frame_lock:
                self.frame = frame
            
            # Thread'i başlat
            self.is_running = True
            self.thread = threading.Thread(target=self._capture_loop)
            self.thread.daemon = True
            self.thread.start()
            
            logging.info(f"Kamera başlatıldı: {self.camera_index}")
            return True
            
        except Exception as e:
            logging.error(f"Kamera başlatılırken hata oluştu: {str(e)}")
            if self.cap and self.cap.isOpened():
                self.cap.release()
            return False
    
    def stop(self):
        """Kamerayı ve kare yakalama thread'ini durdurur."""
        if not self.is_running:
            logging.warning("Kamera zaten durmuş durumda.")
            return
        
        self.is_running = False
        
        if self.thread:
            self.thread.join(timeout=1.0)
            self.thread = None
        
        if self.cap and self.cap.isOpened():
            self.cap.release()
            self.cap = None
        
        logging.info("Kamera durduruldu.")
    
    def get_frame(self):
        """En son yakalanan kareyi döndürür."""
        with self.frame_lock:
            if self.frame is None:
                return np.zeros((FRAME_HEIGHT, FRAME_WIDTH, 3), dtype=np.uint8)
            return self.frame.copy()
    
    def capture_screenshot(self):
        """Anlık ekran görüntüsü alır."""
        return self.get_frame()
    
    def _capture_loop(self):
        """Sürekli olarak kamera karelerini yakalayan thread fonksiyonu."""
        while self.is_running:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    logging.warning("Kare okunamadı, yeniden deneniyor...")
                    time.sleep(0.1)
                    continue
                
                with self.frame_lock:
                    self.frame = frame
                    self.last_frame_time = time.time()
                
                # Frame hızını kontrol etmek için
                sleep_time = 1.0 / FRAME_RATE - (time.time() - self.last_frame_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
            except Exception as e:
                logging.error(f"Kare yakalama sırasında hata: {str(e)}")
                time.sleep(0.1)