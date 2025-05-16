# guard_pc_app/api/endpoints.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
import logging
from datetime import datetime

router = APIRouter()

# Veri modelleri
class FallEvent(BaseModel):
    id: str
    user_id: str
    timestamp: datetime
    confidence: float
    image_url: Optional[str] = None
    
class UserSettings(BaseModel):
    user_id: str
    email_notification: bool = True
    sms_notification: bool = False
    telegram_notification: bool = False
    phone_number: Optional[str] = None
    telegram_chat_id: Optional[str] = None

# Endpoints
@router.get("/")
async def root():
    return {"message": "Guard API çalışıyor"}

@router.get("/events/{user_id}", response_model=List[FallEvent])
async def get_events(user_id: str):
    """Kullanıcının düşme olaylarını getirir."""
    # Bu fonksiyon Firestore'dan kullanıcının olaylarını getirecek
    # Şimdilik sahte veri döndürüyoruz
    return [
        FallEvent(
            id="event1",
            user_id=user_id,
            timestamp=datetime.now(),
            confidence=0.95,
            image_url="https://example.com/event1.jpg"
        )
    ]

@router.post("/events/", response_model=FallEvent)
async def create_event(event: FallEvent):
    """Yeni bir düşme olayı kaydeder."""
    # Bu fonksiyon Firestore'a yeni olay ekleyecek
    logging.info(f"Yeni düşme olayı kaydedildi: {event.id}")
    return event

@router.get("/settings/{user_id}", response_model=UserSettings)
async def get_settings(user_id: str):
    """Kullanıcı ayarlarını getirir."""
    # Bu fonksiyon Firestore'dan kullanıcı ayarlarını getirecek
    return UserSettings(user_id=user_id)

@router.post("/settings/", response_model=UserSettings)
async def update_settings(settings: UserSettings):
    """Kullanıcı ayarlarını günceller."""
    # Bu fonksiyon Firestore'da kullanıcı ayarlarını güncelleyecek
    logging.info(f"Kullanıcı ayarları güncellendi: {settings.user_id}")
    return settings