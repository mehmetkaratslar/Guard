# File: utils/auth.py
# Amac: Firebase kimlik dogrulama islemlerini (eposta/sifre ve Google ile giris dahil) yurutur.
# Kullanildigi yerler: ui/login.py icin kullanici girisi, kayit olma ve Google auth akisi

import logging
import requests
import pyrebase
from typing import Dict, Tuple, Optional
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import socket
import webbrowser
import os
from dotenv import load_dotenv
import re

# Ortam degiskenlerini yukle
load_dotenv()

class CallbackHandler(BaseHTTPRequestHandler):
    """Google OAuth callback icin HTTP handler."""
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        
        # URL'den kod parametresini çıkar
        path_parts = self.path.split('?', 1)
        if len(path_parts) > 1:
            query = path_parts[1]
            self.server.auth_code = urllib.parse.parse_qs(query).get("code", [None])[0]
        else:
            self.server.auth_code = None
            
        # ASCII karakterlerle sınırlı HTML
        html_content = """
        <html>
        <head>
            <title>Guard Application - Authentication Successful</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; background-color: #f5f5f5; }
                .container { background: white; max-width: 500px; margin: 0 auto; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h2 { color: #4285f4; margin-bottom: 20px; }
                p { color: #666; margin-bottom: 20px; }
                .success-icon { font-size: 64px; color: #0f9d58; margin-bottom: 20px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success-icon">&#10003;</div>
                <h2>Login Successful!</h2>
                <p>Authentication completed. You can close this window and return to the Guard application.</p>
                <p>Closing automatically...</p>
            </div>
            <script>
                setTimeout(function() {
                    window.close();
                }, 3000);
            </script>
        </body>
        </html>
        """
        
        self.wfile.write(html_content.encode('ascii', 'ignore'))

class FirebaseAuth:
    """Firebase kimlik dogrulama islemlerini yoneten sinif."""

    def __init__(self, firebase_config: Dict):
        try:
            self.config = firebase_config
            self.firebase = pyrebase.initialize_app(firebase_config)
            self.auth = self.firebase.auth()
            self.current_user: Optional[Dict] = None
            logging.info("Firebase Authentication baslatildi.")
        except Exception as e:
            logging.error(f"Firebase baslatma hatasi: {str(e)}", exc_info=True)
            raise

    def sign_in_with_email_password(self, email: str, password: str) -> Dict:
        """Email/sifre ile giris yapar."""
        try:
            user = self.auth.sign_in_with_email_and_password(email, password)
            account_info = self.auth.get_account_info(user['idToken'])
            user_info = user.copy()
            if 'users' in account_info and account_info['users']:
                user_info.update(account_info['users'][0])
            self.current_user = user_info
            logging.info(f"Kullanici giris yapti: {user_info.get('email', '-')}")
            return user_info
        except Exception as e:
            raise Exception(self._format_error_message(e))

    def create_user_with_email_password(self, email: str, password: str) -> Dict:
        """Yeni kullanici olusturur."""
        try:
            user = self.auth.create_user_with_email_and_password(email, password)
            account_info = self.auth.get_account_info(user['idToken'])
            user_info = user.copy()
            if 'users' in account_info and account_info['users']:
                user_info.update(account_info['users'][0])
            self.current_user = user_info
            logging.info(f"Yeni kullanici olusturuldu: {user_info.get('email', '-')}")
            return user_info
        except Exception as e:
            raise Exception(self._format_error_message(e))

    def update_profile(self, display_name: Optional[str] = None, photo_url: Optional[str] = None, phone_number: Optional[str] = None) -> bool:
        """Kullanici adini, foto URL'sini ve telefon numarasını gunceller."""
        if not self.current_user:
            raise Exception("Profil guncelleme icin giris yapilmamis.")
        update_data = {}
        if display_name: update_data['displayName'] = display_name
        if photo_url: update_data['photoUrl'] = photo_url
        if not update_data:
            return True
            
        self.auth.update_profile(self.current_user['idToken'], **update_data)
        self.current_user.update(update_data)
        
        # Telefon numarası güncelleme (API destek vermediği için sadece yerel kullanıcı nesnesini güncelliyoruz)
        if phone_number:
            self.current_user['phoneNumber'] = phone_number
            
        return True

    def sign_out(self) -> bool:
        """Cikis yapar."""
        self.current_user = None
        return True

    def get_current_user(self) -> Optional[Dict]:
        return self.current_user

    def is_logged_in(self) -> bool:
        return self.current_user is not None

    def sign_in_with_google(self) -> Tuple[str, str]:
        """Tarayici ile Google yetkilendirme islemini baslatir."""
        try:
            # Basitleştirilmiş yönlendirme URI kullanımı
            port = 3000  # Sabit port kullanımı
            
            # Google Cloud Console'da tanımlı olması gereken URI:
            # http://localhost:3000
            redirect_uri = f"http://localhost:{port}"
            
            client_id = os.getenv("GOOGLE_CLIENT_ID")
            if not client_id:
                raise Exception("GOOGLE_CLIENT_ID ortam degiskeni bulunamadi.")
            
            auth_url = (
                f"https://accounts.google.com/o/oauth2/v2/auth?"
                f"client_id={client_id}&"
                f"response_type=code&"
                f"scope=email%20profile&"
                f"redirect_uri={urllib.parse.quote(redirect_uri)}&"
                f"access_type=offline"
            )

            # Port musait mi kontrol et
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(('localhost', port)) == 0:
                    raise Exception(f"Port {port} zaten kullanimda")

            server = HTTPServer(("localhost", port), CallbackHandler)
            server.auth_code = None
            threading.Thread(target=server.handle_request, daemon=True).start()
            
            # Tarayıcıyı aç
            webbrowser.open(auth_url)
            logging.info(f"Google kimlik dogrulama URL'si acildi: {auth_url}")

            start_time = time.time()
            while server.auth_code is None and time.time() - start_time < 60:
                time.sleep(0.1)

            if server.auth_code:
                return auth_url, server.auth_code
            else:
                raise Exception("Google giris zaman asimina ugradi.")

        except Exception as e:
            raise Exception(f"Google giris hatasi: {str(e)}")

    def complete_google_sign_in(self, request_token: str, auth_code: str) -> Dict:
        """Google yetkilendirme tamamlanir ve Firebase'e login olunur."""
        try:
            client_id = os.getenv("GOOGLE_CLIENT_ID")
            client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
            
            # Basitleştirilmiş yönlendirme URI - Google Cloud Console'da tanımlı olmalıdır
            redirect_uri = f"http://localhost:3000"

            # Google'dan token al
            token_resp = requests.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": auth_code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code"
                }
            )
            token_resp.raise_for_status()
            tokens = token_resp.json()
            id_token = tokens.get("id_token")

            if not id_token:
                raise Exception("Google ID token alinamadi.")

            firebase_resp = requests.post(
                f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithIdp?key={self.config['apiKey']}",
                json={
                    "postBody": f"id_token={id_token}&providerId=google.com",
                    "requestUri": redirect_uri,
                    "returnIdpCredential": True,
                    "returnSecureToken": True
                }
            )
            firebase_resp.raise_for_status()
            user = firebase_resp.json()

            account_info = self.auth.get_account_info(user['idToken'])
            user_info = user.copy()
            if 'users' in account_info and account_info['users']:
                user_info.update(account_info['users'][0])
            self.current_user = user_info
            return user_info

        except Exception as e:
            raise Exception(f"Google giris tamamlanamadi: {str(e)}")
            
    def send_password_reset_email(self, email: str) -> bool:
        """Şifre sıfırlama e-postası gönderir."""
        try:
            self.auth.send_password_reset_email(email)
            logging.info(f"Sifre sifirlama e-postasi gonderildi: {email}")
            return True
        except Exception as e:
            error_msg = self._format_error_message(e)
            logging.error(f"Sifre sifirlama e-postasi gonderilirken hata: {error_msg}")
            raise Exception(error_msg)

    def _format_error_message(self, error: Exception) -> str:
        """Firebase API hatalarini okunabilir mesaja cevirir."""
        error_str = str(error)
        if "INVALID_EMAIL" in error_str:
            return "Gecersiz e-posta adresi."
        elif "EMAIL_NOT_FOUND" in error_str:
            return "Bu e-posta adresi kayitli degil."
        elif "INVALID_PASSWORD" in error_str:
            return "Yanlis sifre."
        elif "EMAIL_EXISTS" in error_str:
            return "Bu e-posta zaten kullaniliyor."
        elif "WEAK_PASSWORD" in error_str:
            return "Sifre en az 6 karakter olmali."
        elif "TOO_MANY_ATTEMPTS" in error_str:
            return "Cok fazla hatali giris denemesi."
        return f"Bir hata olustu: {error_str}"