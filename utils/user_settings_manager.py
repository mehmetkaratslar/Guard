# File: utils/user_settings_manager.py
# Description: Manages user settings and profile updates
import logging
import threading
import time
from tkinter import messagebox
import re

class UserSettingsManager:
    """Manages user settings and profile updates for the Guard application."""
    
    def __init__(self, auth_manager, db_manager):
        """
        Initialize the user settings manager.
        
        Args:
            auth_manager (FirebaseAuth): Firebase authentication manager
            db_manager (FirestoreManager): Database manager
        """
        self.auth = auth_manager
        self.db = db_manager
        self.is_saving = False
    
    def load_user_settings(self, user_id):
        """
        Load user settings from database.
        
        Args:
            user_id (str): User ID
            
        Returns:
            dict: User settings or empty dict if not found
        """
        try:
            user_data = self.db.get_user_data(user_id)
            if user_data and "settings" in user_data:
                return user_data["settings"]
            return {}
        except Exception as e:
            logging.error(f"Kullanıcı ayarları yüklenirken hata: {str(e)}")
            return {}
    
    def save_user_settings(self, user_id, settings, callback=None):
        """
        Save user settings to database.
        
        Args:
            user_id (str): User ID
            settings (dict): Settings to save
            callback (function, optional): Callback function after save
            
        Returns:
            bool: True if save operation started successfully
        """
        if self.is_saving:
            return False
            
        self.is_saving = True
        
        # Validate settings
        valid_settings = self._validate_settings(settings)
        
        # Run in separate thread to avoid UI freezing
        def save_thread():
            result = {"success": False, "error": None}
            try:
                self.db.save_user_settings(user_id, valid_settings)
                result["success"] = True
            except Exception as e:
                result["error"] = str(e)
                logging.error(f"Ayarlar kaydedilirken hata: {str(e)}")
            
            self.is_saving = False
            
            # Call the callback with result
            if callback:
                callback(result)
        
        thread = threading.Thread(target=save_thread)
        thread.daemon = True
        thread.start()
        
        return True
    
    def update_user_profile(self, user_id, profile_data, callback=None):
        """
        Update user profile information.
        
        Args:
            user_id (str): User ID
            profile_data (dict): Profile data to update
            callback (function, optional): Callback function after update
            
        Returns:
            bool: True if update operation started successfully
        """
        if self.is_saving:
            return False
            
        self.is_saving = True
        
        # Validate profile data
        valid_profile = self._validate_profile(profile_data)
        
        # Run in separate thread to avoid UI freezing
        def update_thread():
            result = {"success": False, "error": None}
            try:
                # Update Firebase Auth profile
                if "displayName" in valid_profile:
                    self.auth.update_profile(display_name=valid_profile["displayName"])
                
                if "photoURL" in valid_profile:
                    self.auth.update_profile(photo_url=valid_profile["photoURL"])
                    
                # Update database
                self.db.update_user_data(user_id, valid_profile)
                result["success"] = True
                
            except Exception as e:
                result["error"] = str(e)
                logging.error(f"Kullanıcı profili güncellenirken hata: {str(e)}")
            
            self.is_saving = False
            
            # Call the callback with result
            if callback:
                callback(result)
        
        thread = threading.Thread(target=update_thread)
        thread.daemon = True
        thread.start()
        
        return True
    
    def _validate_settings(self, settings):
        """
        Validate settings and return a clean settings dictionary.
        
        Args:
            settings (dict): Settings to validate
            
        Returns:
            dict: Validated settings
        """
        valid = {}
        
        # Email notification
        valid["email_notification"] = bool(settings.get("email_notification", True))
        
        # SMS notification
        valid["sms_notification"] = bool(settings.get("sms_notification", False))
        
        # Phone number (if SMS is enabled)
        if valid["sms_notification"]:
            phone = settings.get("phone_number", "").strip()
            # Simple validation for phone number
            if phone and re.match(r'^\+?[0-9]{10,15}$', phone):
                valid["phone_number"] = phone
            else:
                valid["phone_number"] = ""
                valid["sms_notification"] = False  # Disable SMS if phone number is invalid
        else:
            valid["phone_number"] = settings.get("phone_number", "")
        
        # Telegram notification
        valid["telegram_notification"] = bool(settings.get("telegram_notification", False))
        
        # Telegram chat ID (if Telegram is enabled)
        if valid["telegram_notification"]:
            chat_id = settings.get("telegram_chat_id", "").strip()
            if chat_id:
                valid["telegram_chat_id"] = chat_id
            else:
                valid["telegram_chat_id"] = ""
                valid["telegram_notification"] = False  # Disable Telegram if chat ID is invalid
        else:
            valid["telegram_chat_id"] = settings.get("telegram_chat_id", "")
        
        # Theme
        theme = settings.get("theme", "light")
        if theme in ["light", "dark"]:
            valid["theme"] = theme
        else:
            valid["theme"] = "light"
        
        # Color
        color = settings.get("color", "blue")
        if color in ["blue", "green", "purple", "orange", "custom"]:
            valid["color"] = color
        else:
            valid["color"] = "blue"
        
        # Custom color (if color is custom)
        if valid["color"] == "custom":
            custom_color = settings.get("custom_color", "#2196f3")
            # Simple validation for hex color
            if re.match(r'^#(?:[0-9a-fA-F]{3}){1,2}$', custom_color):
                valid["custom_color"] = custom_color
            else:
                valid["custom_color"] = "#2196f3"
        else:
            valid["custom_color"] = settings.get("custom_color", "#2196f3")
        
        return valid
    
    def _validate_profile(self, profile):
        """
        Validate profile data and return a clean profile dictionary.
        
        Args:
            profile (dict): Profile data to validate
            
        Returns:
            dict: Validated profile data
        """
        valid = {}
        
        # Display name
        name = profile.get("displayName", "").strip()
        if name:
            valid["displayName"] = name
            
        # Photo URL
        photo_url = profile.get("photoURL", "").strip()
        if photo_url:
            valid["photoURL"] = photo_url
            
        return valid
    
    def test_notification(self, notification_type, user_data, notification_manager=None):
        """
        Test notification channels.
        
        Args:
            notification_type (str): Type of notification to test ('email', 'sms', 'telegram')
            user_data (dict): User data with notification settings
            notification_manager (NotificationManager, optional): Notification manager instance
            
        Returns:
            dict: Result of the test operation
        """
        result = {"success": False, "message": ""}
        
        try:
            # If notification manager not provided, try to create one
            if not notification_manager:
                try:
                    from core.notification import NotificationManager
                    notification_manager = NotificationManager(user_data)
                except ImportError:
                    result["message"] = "Bildirim yöneticisi yüklenemedi."
                    return result
            
            # Create test event data
            event_data = {
                "timestamp": time.time(),
                "confidence": 0.85,
                "test": True
            }
            
            # Test notification based on type
            if notification_type == "email":
                email = user_data.get("email", "")
                if not email:
                    result["message"] = "E-posta adresi bulunamadı."
                    return result
                    
                success = notification_manager.send_email(email, event_data, None)
                if success:
                    result["success"] = True
                    result["message"] = f"Test e-postası {email} adresine gönderildi."
                else:
                    result["message"] = "E-posta gönderilemedi. Lütfen ayarlarınızı kontrol edin."
                    
            elif notification_type == "sms":
                phone = user_data.get("phone_number", "")
                if not phone:
                    result["message"] = "Telefon numarası bulunamadı."
                    return result
                    
                success = notification_manager.send_sms(phone, event_data)
                if success:
                    result["success"] = True
                    result["message"] = f"Test SMS'i {phone} numarasına gönderildi."
                else:
                    result["message"] = "SMS gönderilemedi. Lütfen ayarlarınızı kontrol edin."
                    
            elif notification_type == "telegram":
                chat_id = user_data.get("telegram_chat_id", "")
                if not chat_id:
                    result["message"] = "Telegram Chat ID bulunamadı."
                    return result
                    
                success = notification_manager.send_telegram(chat_id, event_data, None)
                if success:
                    result["success"] = True
                    result["message"] = f"Test Telegram mesajı {chat_id} ID'sine gönderildi."
                else:
                    result["message"] = "Telegram mesajı gönderilemedi. Lütfen ayarlarınızı kontrol edin."
            
            else:
                result["message"] = f"Bilinmeyen bildirim türü: {notification_type}"
                
        except Exception as e:
            logging.error(f"Bildirim testi sırasında hata: {str(e)}")
            result["message"] = f"Bildirim testi sırasında hata oluştu: {str(e)}"
            
        return result