# File: config/firebase_config.py
# Amaç: Firebase Web SDK + Admin SDK yapılandırmalarını yapar ve gerekli objeleri dışa aktarır.
# Kullanım: Firebase kimlik doğrulama (pyrebase), firestore erişimi, dosya yükleme (admin SDK) gibi işlemlerde.

import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore, storage

# .env dosyasındaki değişkenleri yükle
load_dotenv()

# Pyrebase için Firebase Web SDK yapılandırması (kullanıcı girişleri, auth işlemleri için)
FIREBASE_CONFIG = {
    "apiKey": os.getenv("FIREBASE_API_KEY"),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
    "databaseURL": os.getenv("FIREBASE_DATABASE_URL"),
    "projectId": os.getenv("FIREBASE_PROJECT_ID"),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
    "appId": os.getenv("FIREBASE_APP_ID")
}

# Admin SDK json dosyasının yolu (Firebase Console'dan indirilen dosya)
SERVICE_ACCOUNT_KEY_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),  # proje kök klasörüne git
    "resources",
    "serviceAccountKey.json"
)

# Firebase Admin SDK başlat (sadece 1 defa)
if not firebase_admin._apps:
    cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
    firebase_admin.initialize_app(cred, {
        "storageBucket": FIREBASE_CONFIG["storageBucket"]
    })

# Firestore (veritabanı) ve Storage (dosya yükleme) referansları
db = firestore.client()        # Firestore erişimi için
bucket = storage.bucket()      # Dosya yükleme için
