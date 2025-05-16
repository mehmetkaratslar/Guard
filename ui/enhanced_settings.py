# File: ui/enhanced_settings.py
# Description: Enhanced settings frame with functional password reset and settings update
import tkinter as tk
from tkinter import ttk, messagebox
import logging
import threading
import os
import sys

# Import our custom modules
from utils.password_reset_handler import PasswordResetHandler
from utils.user_settings_manager import UserSettingsManager

class EnhancedSettingsFrame:
    """
    Enhances the existing SettingsFrame with fully functional features.
    This class doesn't replace the SettingsFrame, but adds functionality to it.
    """
    
    def __init__(self, settings_frame, user, auth, db_manager):
        """
        Initialize the enhanced settings frame.
        
        Args:
            settings_frame: The original SettingsFrame instance
            user (dict): User information
            auth (FirebaseAuth): Authentication manager
            db_manager (FirestoreManager): Database manager
        """
        self.frame = settings_frame
        self.user = user
        self.auth = auth
        self.db_manager = db_manager
        
        # Create handlers
        self.password_handler = PasswordResetHandler(auth)
        self.settings_manager = UserSettingsManager(auth, db_manager)
        
        # Initialize notification manager if available
        try:
            from core.notification import NotificationManager
            user_data = db_manager.get_user_data(user["localId"])
            self.notification_manager = NotificationManager(user_data)
        except Exception as e:
            logging.error(f"Bildirim yöneticisi başlatılamadı: {str(e)}")
            self.notification_manager = None
        
        # Override methods in the original frame
        self._override_methods()
        
        # Initial settings load
        self._load_user_settings()
    
    def _override_methods(self):
        """Override methods in the original frame with enhanced ones."""
        # Store original methods for reference
        self.original_methods = {
            "send_password_reset": getattr(self.frame, "_send_password_reset", None),
            "save_settings": getattr(self.frame, "_save_settings", None),
            "test_email": getattr(self.frame, "_test_email", None),
            "test_sms": getattr(self.frame, "_test_sms", None),
            "test_telegram": getattr(self.frame, "_test_telegram", None)
        }
        
        # Override methods
        setattr(self.frame, "_send_password_reset", self._enhanced_send_password_reset)
        setattr(self.frame, "_save_settings", self._enhanced_save_settings)
        setattr(self.frame, "_test_email", self._enhanced_test_email)
        setattr(self.frame, "_test_sms", self._enhanced_test_sms)
        setattr(self.frame, "_test_telegram", self._enhanced_test_telegram)
    
    def _load_user_settings(self):
        """Load user settings from database and update UI."""
        try:
            # Get user data
            user_data = self.db_manager.get_user_data(self.user["localId"])
            if not user_data:
                return
            
            # Get settings
            settings = user_data.get("settings", {})
            
            # Update UI with settings
            self._update_ui_with_settings(settings)
            
        except Exception as e:
            logging.error(f"Ayarlar yüklenirken hata: {str(e)}")
    
    def _update_ui_with_settings(self, settings):
        """
        Update UI elements with loaded settings.
        
        Args:
            settings (dict): User settings
        """
        try:
            # Update email notification
            if hasattr(self.frame, "email_notification_var"):
                self.frame.email_notification_var.set(settings.get("email_notification", True))
            
            # Update SMS notification
            if hasattr(self.frame, "sms_notification_var"):
                sms_enabled = settings.get("sms_notification", False)
                self.frame.sms_notification_var.set(sms_enabled)
                
                # Update phone number
                if hasattr(self.frame, "phone_var"):
                    self.frame.phone_var.set(settings.get("phone_number", ""))
                
                # Update phone entry state
                if hasattr(self.frame, "phone_entry"):
                    self.frame.phone_entry.config(state="normal" if sms_enabled else "disabled")
                
                # Update SMS test button state
                if hasattr(self.frame, "sms_test_btn"):
                    self.frame.sms_test_btn.config(state="normal" if sms_enabled else "disabled")
            
            # Update Telegram notification
            if hasattr(self.frame, "telegram_notification_var"):
                telegram_enabled = settings.get("telegram_notification", False)
                self.frame.telegram_notification_var.set(telegram_enabled)
                
                # Update Telegram chat ID
                if hasattr(self.frame, "telegram_var"):
                    self.frame.telegram_var.set(settings.get("telegram_chat_id", ""))
                
                # Update Telegram entry state
                if hasattr(self.frame, "telegram_entry"):
                    self.frame.telegram_entry.config(state="normal" if telegram_enabled else "disabled")
                
                # Update Telegram test button state
                if hasattr(self.frame, "telegram_test_btn"):
                    self.frame.telegram_test_btn.config(state="normal" if telegram_enabled else "disabled")
            
            # Update theme
            if hasattr(self.frame, "theme_var"):
                self.frame.theme_var.set(settings.get("theme", "light"))
            
            # Update color
            if hasattr(self.frame, "color_var"):
                self.frame.color_var.set(settings.get("color", "blue"))
            
            # Update custom color
            if hasattr(self.frame, "custom_color_var"):
                self.frame.custom_color_var.set(settings.get("custom_color", "#2196f3"))
                
                # Update custom color preview
                if hasattr(self.frame, "custom_preview"):
                    self.frame.custom_preview.config(bg=settings.get("custom_color", "#2196f3"))
            
        except Exception as e:
            logging.error(f"UI ayarları güncellenirken hata: {str(e)}")
    
    def _enhanced_send_password_reset(self, event=None):
        """
        Enhanced password reset function with proper feedback.
        
        Args:
            event: Event object (optional)
        """
        email = self.user.get("email", "")
        if not email:
            messagebox.showerror("Hata", "E-posta adresi bulunamadı.")
            return
            
        self.password_handler.send_reset_email(email, self.frame)
    
    def _enhanced_save_settings(self):
        """Enhanced settings save function with validation and error handling."""
        try:
            # Collect settings from UI
            settings = self._collect_settings_from_ui()
            
            # Collect profile updates
            profile_updates = self._collect_profile_updates()
            
            # Check if name is empty
            if not profile_updates.get("displayName", "").strip():
                messagebox.showerror("Hata", "Ad Soyad alanı boş olamaz.")
                return
            
            # Check if at least one notification method is enabled
            if not (settings.get("email_notification", False) or 
                    settings.get("sms_notification", False) or 
                    settings.get("telegram_notification", False)):
                messagebox.showwarning("Uyarı", "En az bir bildirim yöntemi etkinleştirilmelidir.")
                return
            
            # Show saving message
            self._show_saving_dialog()
            
            # Save settings
            def settings_callback(result):
                # Handle settings result
                if result["success"]:
                    # Now update profile
                    self.settings_manager.update_user_profile(
                        self.user["localId"], 
                        profile_updates,
                        profile_callback
                    )
                else:
                    self._hide_saving_dialog()
                    messagebox.showerror("Hata", f"Ayarlar kaydedilemedi: {result.get('error', 'Bilinmeyen hata')}")
            
            def profile_callback(result):
                # Hide saving dialog
                self._hide_saving_dialog()
                
                if result["success"]:
                    # Update local user object
                    if "displayName" in profile_updates:
                        self.user["displayName"] = profile_updates["displayName"]
                    
                    messagebox.showinfo("Başarılı", "Ayarlarınız başarıyla kaydedildi.")
                    
                    # Return to dashboard
                    if hasattr(self.frame, "back_fn") and callable(self.frame.back_fn):
                        self.frame.back_fn()
                else:
                    messagebox.showerror("Hata", f"Profil güncellenirken hata oluştu: {result.get('error', 'Bilinmeyen hata')}")
            
            # Start saving process
            self.settings_manager.save_user_settings(
                self.user["localId"], 
                settings,
                settings_callback
            )
            
        except Exception as e:
            logging.error(f"Ayarlar kaydedilirken hata: {str(e)}")
            messagebox.showerror("Hata", f"Ayarlar kaydedilirken bir hata oluştu: {str(e)}")
    
    def _collect_settings_from_ui(self):
        """
        Collect settings from UI elements.
        
        Returns:
            dict: Settings from UI
        """
        settings = {}
        
        # Email notification
        if hasattr(self.frame, "email_notification_var"):
            settings["email_notification"] = self.frame.email_notification_var.get()
        
        # SMS notification
        if hasattr(self.frame, "sms_notification_var"):
            settings["sms_notification"] = self.frame.sms_notification_var.get()
        
        # Phone number
        if hasattr(self.frame, "phone_var"):
            settings["phone_number"] = self.frame.phone_var.get().strip()
        
        # Telegram notification
        if hasattr(self.frame, "telegram_notification_var"):
            settings["telegram_notification"] = self.frame.telegram_notification_var.get()
        
        # Telegram chat ID
        if hasattr(self.frame, "telegram_var"):
            settings["telegram_chat_id"] = self.frame.telegram_var.get().strip()
        
        # Theme
        if hasattr(self.frame, "theme_var"):
            settings["theme"] = self.frame.theme_var.get()
        
        # Color
        if hasattr(self.frame, "color_var"):
            settings["color"] = self.frame.color_var.get()
        
        # Custom color
        if hasattr(self.frame, "custom_color_var"):
            settings["custom_color"] = self.frame.custom_color_var.get()
        
        return settings
    
    def _collect_profile_updates(self):
        """
        Collect profile updates from UI elements.
        
        Returns:
            dict: Profile updates
        """
        updates = {}
        
        # Display name
        if hasattr(self.frame, "name_var"):
            name = self.frame.name_var.get().strip()
            if name:
                updates["displayName"] = name
        
        return updates
    
    def _show_saving_dialog(self):
        """Show a saving dialog."""
        try:
            self.saving_dialog = tk.Toplevel(self.frame)
            self.saving_dialog.title("Kaydediliyor")
            self.saving_dialog.geometry("300x150")
            self.saving_dialog.resizable(False, False)
            self.saving_dialog.transient(self.frame)
            self.saving_dialog.grab_set()
            
            # Center dialog
            self.saving_dialog.update_idletasks()
            width = self.saving_dialog.winfo_width()
            height = self.saving_dialog.winfo_height()
            x = (self.saving_dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (self.saving_dialog.winfo_screenheight() // 2) - (height // 2)
            self.saving_dialog.geometry('{}x{}+{}+{}'.format(width, height, x, y))
            
            # Dialog content
            frame = ttk.Frame(self.saving_dialog, padding=20)
            frame.pack(fill=tk.BOTH, expand=True)
            
            label = ttk.Label(
                frame, 
                text="Ayarlarınız kaydediliyor...", 
                font=("Segoe UI", 12)
            )
            label.pack(pady=(0, 20))
            
            progress = ttk.Progressbar(
                frame, 
                mode="indeterminate", 
                length=200
            )
            progress.pack()
            progress.start(10)
            
        except Exception as e:
            logging.error(f"Kaydetme diyaloğu oluşturulurken hata: {str(e)}")
    
    def _hide_saving_dialog(self):
        """Hide the saving dialog."""
        try:
            if hasattr(self, "saving_dialog") and self.saving_dialog.winfo_exists():
                self.saving_dialog.destroy()
        except Exception as e:
            logging.error(f"Kaydetme diyaloğu kapatılırken hata: {str(e)}")
    
    def _enhanced_test_email(self):
        """Enhanced email test function."""
        if not hasattr(self.frame, "email_notification_var") or not self.frame.email_notification_var.get():
            messagebox.showwarning("Uyarı", "E-posta bildirimleri aktif değil.")
            return
            
        email = self.user.get("email", "")
        if not email:
            messagebox.showerror("Hata", "E-posta adresi bulunamadı.")
            return
            
        user_data = {
            "email": email,
            "email_notification": True
        }
        
        # Show testing message
        messagebox.showinfo(
            "Test Gönderiliyor", 
            f"Test e-postası {email} adresine gönderiliyor..."
        )
        
        # Start test
        if not self.notification_manager:
            try:
                from core.notification import NotificationManager
                self.notification_manager = NotificationManager(user_data)
            except Exception as e:
                messagebox.showerror("Hata", f"Bildirim yöneticisi oluşturulamadı: {str(e)}")
                return
        
        # Start test in thread
        def test_thread():
            try:
                event_data = {
                    "timestamp": time.time(),
                    "confidence": 0.85,
                    "test": True
                }
                
                result = self.notification_manager.send_email(email, event_data, None)
                
                # Show result message
                if result:
                    messagebox.showinfo("Test Başarılı", f"Test e-postası {email} adresine gönderildi.")
                else:
                    messagebox.showerror("Test Başarısız", "E-posta gönderilemedi. Lütfen ayarlarınızı kontrol edin.")
            except Exception as e:
                messagebox.showerror("Test Hatası", f"E-posta testi sırasında hata oluştu: {str(e)}")
        
        thread = threading.Thread(target=test_thread)
        thread.daemon = True
        thread.start()
    
    def _enhanced_test_sms(self):
        """Enhanced SMS test function."""
        if not hasattr(self.frame, "sms_notification_var") or not self.frame.sms_notification_var.get():
            messagebox.showwarning("Uyarı", "SMS bildirimleri aktif değil.")
            return
            
        phone = self.frame.phone_var.get() if hasattr(self.frame, "phone_var") else ""
        if not phone.strip():
            messagebox.showerror("Hata", "Telefon numarası bulunamadı.")
            return
            
        user_data = {
            "phone_number": phone,
            "sms_notification": True
        }
        
        # Show testing message
        messagebox.showinfo(
            "Test Gönderiliyor", 
            f"Test SMS'i {phone} numarasına gönderiliyor..."
        )
        
        # Start test
        if not self.notification_manager:
            try:
                from core.notification import NotificationManager
                self.notification_manager = NotificationManager(user_data)
            except Exception as e:
                messagebox.showerror("Hata", f"Bildirim yöneticisi oluşturulamadı: {str(e)}")
                return
        
        # Start test in thread
        def test_thread():
            try:
                event_data = {
                    "timestamp": time.time(),
                    "confidence": 0.85,
                    "test": True
                }
                
                result = self.notification_manager.send_sms(phone, event_data)
                
                # Show result message
                if result:
                    messagebox.showinfo("Test Başarılı", f"Test SMS'i {phone} numarasına gönderildi.")
                else:
                    messagebox.showerror("Test Başarısız", "SMS gönderilemedi. Lütfen ayarlarınızı kontrol edin.")
            except Exception as e:
                messagebox.showerror("Test Hatası", f"SMS testi sırasında hata oluştu: {str(e)}")
        
        thread = threading.Thread(target=test_thread)
        thread.daemon = True
        thread.start()
    
    def _enhanced_test_telegram(self):
        """Enhanced Telegram test function."""
        if not hasattr(self.frame, "telegram_notification_var") or not self.frame.telegram_notification_var.get():
            messagebox.showwarning("Uyarı", "Telegram bildirimleri aktif değil.")
            return
            
        chat_id = self.frame.telegram_var.get() if hasattr(self.frame, "telegram_var") else ""
        if not chat_id.strip():
            messagebox.showerror("Hata", "Telegram Chat ID bulunamadı.")
            return
            
        user_data = {
            "telegram_chat_id": chat_id,
            "telegram_notification": True
        }
        
        # Show testing message
        messagebox.showinfo(
            "Test Gönderiliyor", 
            f"Test Telegram mesajı {chat_id} ID'sine gönderiliyor..."
        )
        
        # Start test
        if not self.notification_manager:
            try:
                from core.notification import NotificationManager
                self.notification_manager = NotificationManager(user_data)
            except Exception as e:
                messagebox.showerror("Hata", f"Bildirim yöneticisi oluşturulamadı: {str(e)}")
                return
        
        # Start test in thread
        def test_thread():
            try:
                event_data = {
                    "timestamp": time.time(),
                    "confidence": 0.85,
                    "test": True
                }
                
                result = self.notification_manager.send_telegram(chat_id, event_data, None)
                
                # Show result message
                if result:
                    messagebox.showinfo("Test Başarılı", f"Test Telegram mesajı {chat_id} ID'sine gönderildi.")
                else:
                    messagebox.showerror("Test Başarısız", "Telegram mesajı gönderilemedi. Lütfen ayarlarınızı kontrol edin.")
            except Exception as e:
                messagebox.showerror("Test Hatası", f"Telegram testi sırasında hata oluştu: {str(e)}")
        
        thread = threading.Thread(target=test_thread)
        thread.daemon = True
        thread.start()