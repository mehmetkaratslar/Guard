# guard_pc_app/data/storage.py (Güncellenmiş)
import logging
import firebase_admin
from firebase_admin import storage
import cv2
import numpy as np
import os
import uuid
import tempfile
import time

class StorageManager:
    """Firebase Storage işlemlerini yöneten sınıf."""
    
    def __init__(self, bucket=None):
        """
        Args:
            bucket (google.cloud.storage.bucket.Bucket, optional): Firebase Storage bucket nesnesi
        """
        try:
            self.bucket = bucket or storage.bucket()
            self.is_available = True
            logging.info("Firebase Storage bağlantısı başarılı.")
        except Exception as e:
            logging.warning(f"Firebase Storage başlatılamadı: {str(e)}")
            logging.info("Yerel dosya depolama kullanılacak.")
            self.is_available = False
            
            # Yerel depolama dizini oluştur
            self.local_storage_dir = os.path.join(os.path.dirname(__file__), "local_storage")
            os.makedirs(self.local_storage_dir, exist_ok=True)
    
    def upload_screenshot(self, user_id, image, event_id=None):
        """Ekran görüntüsünü Firebase Storage'a veya yerel depolamaya yükler.
        
        Args:
            user_id (str): Kullanıcı ID'si
            image (numpy.ndarray): Yüklenecek görüntü (OpenCV formatında)
            event_id (str, optional): Olay ID'si
            
        Returns:
            str: Yüklenen dosyanın URL'si/yolu, hata durumunda None
        """
        try:
            if event_id is None:
                event_id = str(uuid.uuid4())
                
            # Görüntüyü geçici dosyaya kaydet
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                temp_path = temp_file.name
                cv2.imwrite(temp_path, image)
            
            if not self.is_available:
                # Yerel depolamaya kaydet
                user_dir = os.path.join(self.local_storage_dir, user_id)
                os.makedirs(user_dir, exist_ok=True)
                
                local_path = os.path.join(user_dir, f"{event_id}.jpg")
                os.replace(temp_path, local_path)
                
                logging.info(f"Ekran görüntüsü yerel depolamaya kaydedildi: {local_path}")
                return f"file://{os.path.abspath(local_path)}"
            
            # Görüntüyü Storage'a yükle
            destination_path = f"fall_events/{user_id}/{event_id}.jpg"
            blob = self.bucket.blob(destination_path)
            
            blob.upload_from_filename(temp_path)
            
            # Geçici dosyayı sil
            os.unlink(temp_path)
            
            # Dosya URL'sini oluştur
            # Dosya 1 gün boyunca geçerli olacak şekilde URL oluştur
            url = blob.generate_signed_url(
                version="v4",
                expiration=60 * 60 * 24,  # 1 gün
                method="GET"
            )
            
            logging.info(f"Ekran görüntüsü yüklendi: {destination_path}")
            return url
            
        except Exception as e:
            logging.error(f"Ekran görüntüsü yüklenirken hata oluştu: {str(e)}")
            return None
    
    def delete_screenshot(self, user_id, event_id):
        """Ekran görüntüsünü Firebase Storage'dan veya yerel depolamadan siler.
        
        Args:
            user_id (str): Kullanıcı ID'si
            event_id (str): Olay ID'si
            
        Returns:
            bool: İşlem başarılı ise True, değilse False
        """
        try:
            if not self.is_available:
                # Yerel depolamadan sil
                local_path = os.path.join(self.local_storage_dir, user_id, f"{event_id}.jpg")
                if os.path.exists(local_path):
                    os.remove(local_path)
                    logging.info(f"Ekran görüntüsü yerel depolamadan silindi: {local_path}")
                    return True
                else:
                    logging.warning(f"Silinecek ekran görüntüsü bulunamadı: {local_path}")
                    return False
            
            blob_path = f"fall_events/{user_id}/{event_id}.jpg"
            blob = self.bucket.blob(blob_path)
            
            if blob.exists():
                blob.delete()
                logging.info(f"Ekran görüntüsü silindi: {blob_path}")
                return True
            else:
                logging.warning(f"Silinecek ekran görüntüsü bulunamadı: {blob_path}")
                return False
                
        except Exception as e:
            logging.error(f"Ekran görüntüsü silinirken hata oluştu: {str(e)}")
            return False
    
    def get_screenshot_url(self, user_id, event_id):
        """Ekran görüntüsünün URL'sini döndürür.
        
        Args:
            user_id (str): Kullanıcı ID'si
            event_id (str): Olay ID'si
            
        Returns:
            str: Görüntünün URL'si, hata durumunda None
        """
        try:
            if not self.is_available:
                # Yerel dosya yolunu döndür
                local_path = os.path.join(self.local_storage_dir, user_id, f"{event_id}.jpg")
                if os.path.exists(local_path):
                    return f"file://{os.path.abspath(local_path)}"
                else:
                    logging.warning(f"Görüntü bulunamadı: {local_path}")
                    return None
            
            blob_path = f"fall_events/{user_id}/{event_id}.jpg"
            blob = self.bucket.blob(blob_path)
            
            if blob.exists():
                url = blob.generate_signed_url(
                    version="v4",
                    expiration=60 * 60 * 24,  # 1 gün
                    method="GET"
                )
                return url
            else:
                logging.warning(f"Görüntü bulunamadı: {blob_path}")
                return None
                
        except Exception as e:
            logging.error(f"Görüntü URL'si alınırken hata oluştu: {str(e)}")
            return None
    
    def download_screenshot(self, user_id, event_id):
        """Ekran görüntüsünü indirir ve bir numpy dizisi olarak döndürür.
        
        Args:
            user_id (str): Kullanıcı ID'si
            event_id (str): Olay ID'si
            
        Returns:
            numpy.ndarray: Görüntü, hata durumunda None
        """
        try:
            if not self.is_available:
                # Yerel dosyayı oku
                local_path = os.path.join(self.local_storage_dir, user_id, f"{event_id}.jpg")
                if os.path.exists(local_path):
                    img = cv2.imread(local_path)
                    return img
                else:
                    logging.warning(f"İndirilecek görüntü bulunamadı: {local_path}")
                    return None
            
            # Geçici dosya oluştur
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                temp_path = temp_file.name
            
            blob_path = f"fall_events/{user_id}/{event_id}.jpg"
            blob = self.bucket.blob(blob_path)
            
            if blob.exists():
                blob.download_to_filename(temp_path)
                img = cv2.imread(temp_path)
                os.unlink(temp_path)  # Geçici dosyayı sil
                return img
            else:
                logging.warning(f"İndirilecek görüntü bulunamadı: {blob_path}")
                return None
                
        except Exception as e:
            logging.error(f"Görüntü indirilirken hata oluştu: {str(e)}")
            return None
    
    def list_all_screenshots(self, user_id):
        """Kullanıcının tüm ekran görüntülerini listeler.
        
        Args:
            user_id (str): Kullanıcı ID'si
            
        Returns:
            list: event_id'lerin listesi
        """
        try:
            if not self.is_available:
                # Yerel dosyaları listele
                user_dir = os.path.join(self.local_storage_dir, user_id)
                if not os.path.exists(user_dir):
                    return []
                
                files = os.listdir(user_dir)
                event_ids = [f.replace('.jpg', '') for f in files if f.endswith('.jpg')]
                return event_ids
            
            # Storage'dan liste al
            prefix = f"fall_events/{user_id}/"
            blobs = self.bucket.list_blobs(prefix=prefix)
            
            event_ids = []
            for blob in blobs:
                filename = os.path.basename(blob.name)
                if filename.endswith('.jpg'):
                    event_id = filename.replace('.jpg', '')
                    event_ids.append(event_id)
            
            return event_ids
                
        except Exception as e:
            logging.error(f"Ekran görüntüleri listelenirken hata oluştu: {str(e)}")
            return []