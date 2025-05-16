# File: api/server.py
# Amaç: FastAPI ile bir REST API sunucusu başlatmak ve UI ile arka uç arasında HTTP haberleşmesi sağlamak.

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .endpoints import router  # API endpointlerini içeren dosya
import uvicorn
import threading

# FastAPI uygulaması oluşturuluyor
app = FastAPI(
    title="Guard API",
    description="Düşme algılama sistemi API servisi",
    version="1.0.0"
)

# CORS (Tarayıcılar arası erişim) ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Geliştirme sürecinde tüm domainlere izin verilir
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tüm API endpointlerini FastAPI uygulamasına dahil et
app.include_router(router)

def start_server():
    """
    API sunucusunu (FastAPI + Uvicorn) başlatır.
    UI'dan bağımsız bir servis olarak 127.0.0.1:8002 adresinde çalışır.
    """
    host = "127.0.0.1"
    port = 8002
    logging.info(f"API sunucusu başlatılıyor: {host}:{port}")
    uvicorn.run(app, host=host, port=port)

def run_api_server_in_thread():
    """
    API sunucusunu arka planda bir daemon thread olarak başlatır.
    Ana Tkinter uygulamasını bloklamadan çalışmasını sağlar.
    """
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    return server_thread
