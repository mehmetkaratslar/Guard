# core/notification.py
# Bildirim gönderme işlemlerini yöneten sınıf (güncellenmiş)

import logging
import smtplib
import requests
import threading
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import os
from config.settings import EMAIL_SUBJECT, EMAIL_FROM, SMS_MESSAGE, TELEGRAM_MESSAGE
import telepot
import time
from dotenv import load_dotenv

# Ortam değişkenlerini yükle
load_dotenv()

class NotificationManager:
    """Farklı kanallarda bildirim gönderen sınıf."""
    
    def __init__(self, user_data=None):
        """
        Args:
            user_data (dict): Kullanıcı verisi ve bildirim tercihleri
        """
        # Kullanıcı verisi yoksa boş bir sözlük kullan
        self.user_data = user_data if user_data else {}
        self.telegram_bot = None
        
        # Telegram botu varsa başlat
        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if telegram_token:
            try:
                self.telegram_bot = telepot.Bot(telegram_token)
                logging.info("Telegram botu başlatıldı.")
            except Exception as e:
                logging.error(f"Telegram botu başlatılamadı: {str(e)}")
    
    def send_notifications(self, event_data, screenshot=None):
        """Kullanıcı tercihlerine göre bildirimleri gönderir.
        
        Args:
            event_data (dict): Olay bilgileri
            screenshot (numpy.ndarray, optional): Olay anındaki ekran görüntüsü
        """
        # Bildirimleri ayrı threadlerde gönder
        if self.user_data.get("email_notification", True) and self.user_data.get("email", None):
            threading.Thread(
                target=self.send_email,
                args=(self.user_data.get("email"), event_data, screenshot),
                daemon=True
            ).start()
        elif self.user_data.get("email_notification", True):
            # Kullanıcı e-posta adresi yoksa .env dosyasındaki SMTP_USER kullan
            email = os.getenv("SMTP_USER")
            if email:
                threading.Thread(
                    target=self.send_email,
                    args=(email, event_data, screenshot),
                    daemon=True
                ).start()
        
        if self.user_data.get("sms_notification", False) and self.user_data.get("phone_number"):
            threading.Thread(
                target=self.send_sms,
                args=(self.user_data["phone_number"], event_data),
                daemon=True
            ).start()
        
        if self.user_data.get("telegram_notification", False) and self.user_data.get("telegram_chat_id"):
            threading.Thread(
                target=self.send_telegram,
                args=(self.user_data["telegram_chat_id"], event_data, screenshot),
                daemon=True
            ).start()
        
        # Test amaçlı: Başka bir tercih aktif değilse ve bir test ise Telegram'a gönder
        if not any([
            self.user_data.get("email_notification", False),
            self.user_data.get("sms_notification", False),
            self.user_data.get("telegram_notification", False)
        ]) and event_data.get("test", False):
            # Telegram bot doğrudan Telegram API'si ile test
            self._send_telegram_direct(event_data, screenshot)
    
    def send_email(self, to_email, event_data, screenshot=None):
        """E-posta bildirimi gönderir.
        
        Args:
            to_email (str): Alıcı e-posta adresi
            event_data (dict): Olay bilgileri
            screenshot (numpy.ndarray, optional): Olay anındaki ekran görüntüsü
        """
        try:
            # SMTP sunucu ayarları
            smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
            smtp_port = int(os.getenv("SMTP_PORT", "587"))
            smtp_user = os.getenv("SMTP_USER")
            smtp_pass = os.getenv("SMTP_PASS")
            
            if not (smtp_user and smtp_pass):
                logging.error("SMTP kimlik bilgileri ayarlanmamış.")
                return
            
            # E-posta mesajı oluştur
            msg = MIMEMultipart()
            msg['From'] = EMAIL_FROM
            msg['To'] = to_email
            msg['Subject'] = EMAIL_SUBJECT
            
            # Timestamp veya şimdi
            timestamp = event_data.get("timestamp", time.time())
            if isinstance(timestamp, str):
                try:
                    timestamp = float(timestamp)
                except:
                    timestamp = time.time()
            
            # Tarih biçimlendirme
            date_time = time.strftime("%d.%m.%Y %H:%M:%S", time.localtime(timestamp))
            
            # Test bildirimi mi?
            is_test = event_data.get("test", False)
            test_label = "[TEST] " if is_test else ""
            
            # Mesaj içeriği
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                    <h2 style="color: #d9534f;">{test_label}Guard Düşme Algılama Sistemi - UYARI!</h2>
                    <p>Merhaba,</p>
                    <p>Sistemimiz <strong>{date_time}</strong> tarihinde bir düşme algıladı.</p>
                    <p>Düşme olasılığı: <strong>%{event_data.get("confidence", 0.0) * 100:.2f}</strong></p>
                    <p>Lütfen durumu kontrol edin ve gerekirse acil yardım çağırın.</p>
                    <hr style="border: 1px solid #eee;">
                    <p style="font-size: 12px; color: #777;"><i>Not: Bu e-postaya yanıt vermeyin, otomatik olarak gönderilmiştir.</i></p>
                </div>
            </body>
            </html>
            """
            msg.attach(MIMEText(html_content, 'html'))
            
            # Ekran görüntüsü varsa ekle
            if screenshot is not None:
                import cv2
                _, img_encoded = cv2.imencode('.jpg', screenshot)
                img_bytes = img_encoded.tobytes()
                
                img_attachment = MIMEImage(img_bytes)
                img_attachment.add_header('Content-Disposition', 'attachment', filename='fall_detected.jpg')
                msg.attach(img_attachment)
            
            # E-postayı gönder
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            
            logging.info(f"E-posta bildirimi gönderildi: {to_email}")
            return True
            
        except Exception as e:
            logging.error(f"E-posta gönderilirken hata oluştu: {str(e)}")
            return False
    
    def send_sms(self, phone_number, event_data):
        """SMS bildirimi gönderir.
        
        Args:
            phone_number (str): Alıcı telefon numarası
            event_data (dict): Olay bilgileri
        """
        try:
            # SMS API ayarları (örnek olarak Twilio)
            twilio_sid = os.getenv("TWILIO_SID")
            twilio_token = os.getenv("TWILIO_TOKEN")
            twilio_from = os.getenv("TWILIO_PHONE")
            
            if not (twilio_sid and twilio_token and twilio_from):
                logging.error("Twilio kimlik bilgileri ayarlanmamış.")
                return False
            
            # Test bildirimi mi?
            is_test = event_data.get("test", False)
            test_label = "[TEST] " if is_test else ""
            
            # Mesaj içeriği
            message = f"{test_label}{SMS_MESSAGE}"
            
            # SMS gönder
            url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages.json"
            data = {
                "From": twilio_from,
                "To": phone_number,
                "Body": message
            }
            
            response = requests.post(
                url,
                data=data,
                auth=(twilio_sid, twilio_token)
            )
            
            if response.status_code == 201:
                logging.info(f"SMS bildirimi gönderildi: {phone_number}")
                return True
            else:
                logging.error(f"SMS gönderilemedi. Durum kodu: {response.status_code}, Yanıt: {response.text}")
                return False
            
        except Exception as e:
            logging.error(f"SMS gönderilirken hata oluştu: {str(e)}")
            return False
    
    def send_telegram(self, chat_id, event_data, screenshot=None):
        """Telegram bildirimi gönderir.
        
        Args:
            chat_id (str): Alıcı Telegram sohbet ID'si
            event_data (dict): Olay bilgileri
            screenshot (numpy.ndarray, optional): Olay anındaki ekran görüntüsü
        """
        try:
            if not self.telegram_bot:
                logging.error("Telegram botu başlatılmamış.")
                return False
            
            # Test bildirimi mi?
            is_test = event_data.get("test", False)
            test_label = "[TEST] " if is_test else ""
            
            # Mesaj içeriği
            message = f"{test_label}{TELEGRAM_MESSAGE}\n\nDüşme olasılığı: %{event_data.get('confidence', 0.0) * 100:.2f}"
            
            # Mesajı gönder
            self.telegram_bot.sendMessage(chat_id, message, parse_mode="Markdown")
            
            # Ekran görüntüsü varsa gönder
            if screenshot is not None:
                import cv2
                import io
                
                _, img_encoded = cv2.imencode('.jpg', screenshot)
                img_bytes = io.BytesIO(img_encoded.tobytes())
                img_bytes.name = 'fall_detected.jpg'
                
                self.telegram_bot.sendPhoto(chat_id, img_bytes)
            
            logging.info(f"Telegram bildirimi gönderildi: {chat_id}")
            return True
            
        except Exception as e:
            logging.error(f"Telegram bildirimi gönderilirken hata oluştu: {str(e)}")
            return False
    
    def _send_telegram_direct(self, event_data, screenshot=None):
        """Telegram API'sini kullanarak doğrudan mesaj gönderir.
        
        Args:
            event_data (dict): Olay bilgileri
            screenshot (numpy.ndarray, optional): Olay anındaki ekran görüntüsü
        """
        try:
            token = os.getenv("TELEGRAM_BOT_TOKEN")
            if not token:
                logging.error("Telegram bot token bulunamadı.")
                return False
            
            # Test bildirimi mi?
            is_test = event_data.get("test", False)
            test_label = "[TEST] " if is_test else ""
            
            # Mesaj içeriği
            message = f"{test_label}{TELEGRAM_MESSAGE}\n\nDüşme olasılığı: %{event_data.get('confidence', 0.0) * 100:.2f}"
            
            # İlk mesajı manuel olarak gönder, chat_id alınacak
            url = f"https://api.telegram.org/bot{token}/getUpdates"
            response = requests.get(url)
            
            if response.status_code != 200:
                logging.error("Telegram getUpdates API'si çağrılamadı.")
                return False
            
            data = response.json()
            chat_ids = []
            
            # Son konuşmaları bul
            if data.get("ok", False) and "result" in data:
                for update in data["result"]:
                    if "message" in update and "chat" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        if chat_id not in chat_ids:
                            chat_ids.append(chat_id)
            
            if not chat_ids:
                logging.warning("Telegram chat_id bulunamadı. Botla bir görüşme başlatın.")
                return False
            
            # Her bir chat_id için mesaj gönder
            for chat_id in chat_ids:
                # Mesajı gönder
                url = f"https://api.telegram.org/bot{token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "Markdown"
                }
                message_response = requests.post(url, data=payload)
                
                # Ekran görüntüsü varsa gönder
                if screenshot is not None and message_response.status_code == 200:
                    import cv2
                    
                    _, img_encoded = cv2.imencode('.jpg', screenshot)
                    img_bytes = img_encoded.tobytes()
                    
                    url = f"https://api.telegram.org/bot{token}/sendPhoto"
                    files = {"photo": ("fall_detected.jpg", img_bytes, "image/jpeg")}
                    payload = {"chat_id": chat_id}
                    
                    photo_response = requests.post(url, data=payload, files=files)
                    
                    if photo_response.status_code != 200:
                        logging.error(f"Telegram fotoğraf gönderilemedi: {photo_response.text}")
            
            logging.info(f"Telegram bildirimi doğrudan gönderildi: {len(chat_ids)} alıcıya")
            return True
            
        except Exception as e:
            logging.error(f"Telegram doğrudan gönderim hatası: {str(e)}")
            return False