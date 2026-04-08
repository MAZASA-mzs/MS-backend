from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.settings import BotCommandResponse, FaqSectionResponse
from app.services.settings_service import get_commands, get_faqs
router = APIRouter()


@router.get("/settings/commands", response_model=List[BotCommandResponse])
def read_commands(platform: str = Query(None, description="Фильтр платформы: TG или MAX"), db: Session = Depends(get_db)):
    return get_commands(db, platform)

@router.get("/faq/sections", response_model=List[FaqSectionResponse])
def read_faqs(db: Session = Depends(get_db)):
    return get_faqs(db, only_enabled=True)

@router.get("/privacy-policy")
def read_privacy_policy():
    """
    Возвращает текст политики и ссылку на скачивание PDF.
    """
    return {
        "text": "Официальный текст Политики Конфиденциальности и обработки ПД. Настоящим документом устанавливается...",
        "pdf_link": "https://example.com/documents/privacy_policy.pdf"
    }

@router.get("/max-bot-link")
def read_max_bot_link():
    """
    Возвращает ссылку на MAX бота.
    """
    return {"link": "max.me/@max-bot"}
