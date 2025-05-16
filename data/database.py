# guard_pc_app/data/database.py (Güncellenmiş)

import logging
from google.cloud import firestore
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import time
import uuid
import os
import json

class FirestoreManager:
    """Firestore veritabanı işlemlerini yöneten sınıf."""
    
    def __init__(self, db=None):
        """
        Args:
            db (google.cloud.firestore.Client, optional): Firestore client nesnesi
        """
        try:
            self.db = db or firestore.client()
            self.is_available = True
            logging.info("Firestore bağlantısı başarılı.")
        except Exception as e:
            logging.warning(f"Firestore başlatılamadı: {str(e)}")
            logging.info("Yerel dosya tabanlı veri saklama kullanılacak.")
            self.is_available = False
            # Verileri geçici olarak bellekte ve dosyada saklayacak sözlük
            self._memory_storage = {
                "users": {}
            }
            self._load_local_data()

    def _get_local_data_path(self):
        """Yerel veri dosyasının yolunu döndürür."""
        data_dir = os.path.join(os.path.dirname(__file__), "local_data")
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, "local_db.json")
    
    def _load_local_data(self):
        """Yerel veri dosyasından verileri yükler."""
        try:
            file_path = self._get_local_data_path()
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._memory_storage = data
                    logging.info(f"Yerel veri dosyası yüklendi: {file_path}")
            else:
                logging.info("Yerel veri dosyası bulunamadı, yeni dosya oluşturulacak.")
                self._save_local_data()
        except Exception as e:
            logging.error(f"Yerel veri yüklenirken hata: {str(e)}")
    
    def _save_local_data(self):
        """Verileri yerel dosyaya kaydeder."""
        try:
            file_path = self._get_local_data_path()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self._memory_storage, f, indent=2, ensure_ascii=False)
            logging.info(f"Veriler yerel dosyaya kaydedildi: {file_path}")
        except Exception as e:
            logging.error(f"Veriler yerel dosyaya kaydedilirken hata: {str(e)}")

    def get_user_data(self, user_id):
        """Kullanıcı verilerini getirir."""
        if not self.is_available:
            # Bellekten verileri getir
            user_data = self._memory_storage["users"].get(user_id, None)
            logging.info(f"Yerel depodan kullanıcı verisi alındı: {user_id}")
            return user_data
        
        try:
            # Normal Firestore işlemi
            user_ref = self.db.collection("users").document(user_id)
            user_doc = user_ref.get()
            
            if user_doc.exists:
                return user_doc.to_dict()
            else:
                logging.warning(f"Kullanıcı bulunamadı: {user_id}")
                return None
                
        except Exception as e:
            logging.error(f"Kullanıcı verileri getirilirken hata oluştu: {str(e)}")
            return None

    def save_user_settings(self, user_id, settings):
        """Kullanıcı ayarlarını kaydeder."""
        if not self.is_available:
            # Bellekte sakla
            if user_id not in self._memory_storage["users"]:
                self._memory_storage["users"][user_id] = {}
            
            # Ayarları güncelle
            if "settings" not in self._memory_storage["users"][user_id]:
                self._memory_storage["users"][user_id]["settings"] = {}
            
            self._memory_storage["users"][user_id]["settings"].update(settings)
            self._memory_storage["users"][user_id]["updated_at"] = time.time()
            
            # Dosyaya kaydet
            self._save_local_data()
            logging.info(f"Kullanıcı ayarları yerel depoya kaydedildi: {user_id}")
            return True
        
        try:
            # Normal Firestore işlemi
            user_ref = self.db.collection("users").document(user_id)
            
            # Ayarlarla birlikte güncelleme zamanını da kaydet
            settings["updated_at"] = firestore.SERVER_TIMESTAMP
            
            user_ref.set({"settings": settings}, merge=True)
            logging.info(f"Kullanıcı ayarları güncellendi: {user_id}")
            return True
            
        except Exception as e:
            logging.error(f"Kullanıcı ayarları kaydedilirken hata oluştu: {str(e)}")
            return False
    
    def save_fall_event(self, user_id, event_data):
        """Düşme olayını veritabanına kaydeder.
        
        Args:
            user_id (str): Kullanıcı ID'si
            event_data (dict): Olay verileri (confidence, image_url, vb.)
            
        Returns:
            str: Kaydedilen olay ID'si, hata durumunda None
        """
        # Yeni bir event ID oluştur
        event_id = str(uuid.uuid4())
        
        # Olay verilerine ekstra bilgiler ekle
        event_data["id"] = event_id
        event_data["created_at"] = time.time()
        
        # Numpy tiplerini Python tiplerine dönüştür
        if "confidence" in event_data and hasattr(event_data["confidence"], "item"):
            event_data["confidence"] = float(event_data["confidence"])
            
        if not self.is_available:
            # Bellekte sakla
            if user_id not in self._memory_storage["users"]:
                self._memory_storage["users"][user_id] = {}
            
            # Fall events listesini oluştur
            if "fall_events" not in self._memory_storage["users"][user_id]:
                self._memory_storage["users"][user_id]["fall_events"] = []
            
            # Olayı kaydet
            self._memory_storage["users"][user_id]["fall_events"].append(event_data)
            
            # Dosyaya kaydet
            self._save_local_data()
            logging.info(f"Düşme olayı yerel depoya kaydedildi: {event_id} - Kullanıcı: {user_id}")
            return event_id
            
        try:
            # Olayı kaydet
            event_ref = self.db.collection("users").document(user_id).collection("fall_events").document(event_id)
            
            event_ref.set(event_data)
            logging.info(f"Düşme olayı kaydedildi: {event_id} - Kullanıcı: {user_id}")
            
            return event_id
            
        except Exception as e:
            logging.error(f"Düşme olayı kaydedilirken hata oluştu: {str(e)}")
            return None
    
    def get_fall_events(self, user_id, limit=10):
        """Kullanıcının düşme olaylarını getirir.
        
        Args:
            user_id (str): Kullanıcı ID'si
            limit (int, optional): En fazla kaç olay getirileceği
            
        Returns:
            list: Düşme olayları listesi
        """
        if not self.is_available:
            # Bellekten getir
            if user_id not in self._memory_storage["users"]:
                return []
            
            events = self._memory_storage["users"][user_id].get("fall_events", [])
            
            # Oluşturulma zamanına göre sırala (en yeni en üstte)
            sorted_events = sorted(events, key=lambda e: e.get("created_at", 0), reverse=True)
            
            # Limitle
            return sorted_events[:limit]
            
        try:
            events_ref = self.db.collection("users").document(user_id).collection("fall_events")
            query = events_ref.order_by("created_at", direction=firestore.Query.DESCENDING).limit(limit)
            
            events = []
            for doc in query.stream():
                event_data = doc.to_dict()
                events.append(event_data)
            
            return events
            
        except Exception as e:
            logging.error(f"Düşme olayları getirilirken hata oluştu: {str(e)}")
            return []
    
    def create_new_user(self, user_id, user_data):
        """Yeni kullanıcı oluşturur.
        
        Args:
            user_id (str): Kullanıcı ID'si
            user_data (dict): Kullanıcı verileri
            
        Returns:
            bool: İşlem başarılı ise True, değilse False
        """
        # Temel kullanıcı verileri
        base_data = {
            "id": user_id,
            "created_at": time.time(),
            "last_login": time.time(),
            "settings": {
                "email_notification": True,
                "sms_notification": False,
                "telegram_notification": False,
                "phone_number": "",
                "telegram_chat_id": ""
            }
        }
        
        # Kullanıcı verileri ile birleştir
        user_data = {**base_data, **user_data}
        
        if not self.is_available:
            # Bellekte sakla
            self._memory_storage["users"][user_id] = user_data
            
            # Dosyaya kaydet
            self._save_local_data()
            logging.info(f"Yeni kullanıcı yerel depoya kaydedildi: {user_id}")
            return True
            
        try:
            user_ref = self.db.collection("users").document(user_id)
            user_ref.set(user_data)
            logging.info(f"Yeni kullanıcı oluşturuldu: {user_id}")
            
            return True
            
        except Exception as e:
            logging.error(f"Kullanıcı oluşturulurken hata oluştu: {str(e)}")
            return False
    
    def update_last_login(self, user_id):
        """Kullanıcının son giriş zamanını günceller.
        
        Args:
            user_id (str): Kullanıcı ID'si
            
        Returns:
            bool: İşlem başarılı ise True, değilse False
        """
        if not self.is_available:
            # Bellekte güncelle
            if user_id not in self._memory_storage["users"]:
                self._memory_storage["users"][user_id] = {"id": user_id}
            
            self._memory_storage["users"][user_id]["last_login"] = time.time()
            
            # Dosyaya kaydet
            self._save_local_data()
            logging.info(f"Son giriş zamanı yerel depoda güncellendi: {user_id}")
            return True
            
        try:
            user_ref = self.db.collection("users").document(user_id)
            user_ref.update({"last_login": firestore.SERVER_TIMESTAMP})
            return True
            
        except Exception as e:
            logging.error(f"Son giriş zamanı güncellenirken hata oluştu: {str(e)}")
            return False
    
    def update_user_data(self, user_id, user_data):
        """Kullanıcı bilgilerini günceller.
        
        Args:
            user_id (str): Kullanıcı ID'si
            user_data (dict): Güncellenecek kullanıcı verileri
            
        Returns:
            bool: İşlem başarılı ise True, değilse False
        """
        if not self.is_available:
            # Bellekte güncelle
            if user_id not in self._memory_storage["users"]:
                self._memory_storage["users"][user_id] = {"id": user_id}
            
            self._memory_storage["users"][user_id].update(user_data)
            self._memory_storage["users"][user_id]["updated_at"] = time.time()
            
            # Dosyaya kaydet
            self._save_local_data()
            logging.info(f"Kullanıcı verileri yerel depoda güncellendi: {user_id}")
            return True
            
        try:
            user_ref = self.db.collection("users").document(user_id)
            
            # Güncelleme zamanını ekle
            user_data["updated_at"] = firestore.SERVER_TIMESTAMP
            
            user_ref.update(user_data)
            logging.info(f"Kullanıcı verileri güncellendi: {user_id}")
            return True
            
        except Exception as e:
            logging.error(f"Kullanıcı verileri güncellenirken hata oluştu: {str(e)}")
            return False
    
    def delete_fall_event(self, user_id, event_id):
        """Düşme olayını siler.
        
        Args:
            user_id (str): Kullanıcı ID'si
            event_id (str): Silinecek olayın ID'si
            
        Returns:
            bool: İşlem başarılı ise True, değilse False
        """
        if not self.is_available:
            # Bellekten sil
            if user_id not in self._memory_storage["users"]:
                return False
            
            if "fall_events" not in self._memory_storage["users"][user_id]:
                return False
            
            # Olayı bul ve sil
            events = self._memory_storage["users"][user_id]["fall_events"]
            self._memory_storage["users"][user_id]["fall_events"] = [e for e in events if e.get("id") != event_id]
            
            # Dosyaya kaydet
            self._save_local_data()
            logging.info(f"Düşme olayı yerel depodan silindi: {event_id} - Kullanıcı: {user_id}")
            return True
            
        try:
            event_ref = self.db.collection("users").document(user_id).collection("fall_events").document(event_id)
            event_ref.delete()
            logging.info(f"Düşme olayı silindi: {event_id} - Kullanıcı: {user_id}")
            return True
            
        except Exception as e:
            logging.error(f"Düşme olayı silinirken hata oluştu: {str(e)}")
            return False