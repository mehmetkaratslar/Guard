# File: utils/password_reset_handler.py
# Description: Enhanced password reset functionality for Guard application
import logging
import tkinter as tk
from tkinter import messagebox
import threading
import time

class PasswordResetHandler:
    """Password reset operations handler for the Guard application."""
    
    def __init__(self, auth_manager):
        """
        Initialize the password reset handler.
        
        Args:
            auth_manager (FirebaseAuth): Firebase authentication manager
        """
        self.auth = auth_manager
    
    def send_reset_email(self, email, parent_window=None):
        """
        Send a password reset email and show appropriate messages.
        
        Args:
            email (str): User's email address
            parent_window: Parent window for displaying messages
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        if not email:
            self._show_error("Hata", "Lütfen geçerli bir e-posta adresi girin.", parent_window)
            return False
            
        # Show sending message
        self._show_info("İşlem Sürüyor", f"Şifre sıfırlama bağlantısı gönderiliyor: {email}", parent_window)
        
        # Run in separate thread to avoid UI freezing
        result_container = {"success": False, "error": None}
        
        def send_email_thread():
            try:
                self.auth.send_password_reset_email(email)
                result_container["success"] = True
            except Exception as e:
                result_container["error"] = str(e)
        
        thread = threading.Thread(target=send_email_thread)
        thread.daemon = True
        thread.start()
        
        # Wait for the thread to finish with timeout
        start_time = time.time()
        while thread.is_alive() and time.time() - start_time < 10:  # 10 second timeout
            time.sleep(0.1)
            
        if thread.is_alive():
            self._show_error("Zaman Aşımı", "Şifre sıfırlama e-postası gönderilemedi. Lütfen internet bağlantınızı kontrol edin.", parent_window)
            return False
            
        if result_container["success"]:
            self._show_success("Başarılı", 
                              f"Şifre sıfırlama bağlantısı {email} adresine gönderildi.\n\n"
                              f"Lütfen e-posta kutunuzu kontrol edin ve gelen bağlantıya tıklayın.", 
                              parent_window)
            return True
        else:
            self._show_error("Hata", 
                            f"Şifre sıfırlama e-postası gönderilemedi: {result_container['error']}", 
                            parent_window)
            return False
    
    def _show_error(self, title, message, parent=None):
        """Display error message."""
        return messagebox.showerror(title, message, parent=parent)
        
    def _show_info(self, title, message, parent=None):
        """Display info message."""
        return messagebox.showinfo(title, message, parent=parent)
        
    def _show_success(self, title, message, parent=None):
        """Display success message."""
        return messagebox.showinfo(title, message, parent=parent)